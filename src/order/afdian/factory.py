from typing import Tuple, Any
from loguru import logger
from datetime import datetime, timedelta
import json
import string

from src.database import Bill, Plan
from src.cdk.acquire_cdk import acquire_cdk
from src.cdk.renew_cdk import renew_cdk
from .query_afdian import query_order_by_out_trade_no


async def process_order(out_trade_no: str) -> Tuple[Any, str]:
    if not out_trade_no:
        logger.error(f"out_trade_no is reuqired: {out_trade_no}")
        return None, "not an order"

    response = await query_order_by_out_trade_no(out_trade_no)
    if not response or response.get("ec") != 200:
        logger.error(
            f"Query order failed, out_trade_no: {out_trade_no}, response: {response}"
        )
        return None, "Query order failed"

    order = response.get("data", {}).get("list", [])
    if not order:
        logger.error(
            f"Order not found, out_trade_no: {out_trade_no}, response: {response}"
        )
        return None, "Order not found"

    order = order[0]

    remark = None # order.get("remark", "")
    renew_bill = None
    if remark and len(remark) == 24 and all(c in string.hexdigits for c in remark):
        renew_bill = (
            Bill.select()
            .where(Bill.cdk == remark)
            .order_by(Bill.expired_at.desc())
            .get_or_none()
        )

    now = datetime.now()
    buy_count = order.get("sku_detail", [{}])[0].get("count", 1)

    try:
        bill, created = Bill.get_or_create(
            platform="afdian",
            order_id=order["out_trade_no"],
            defaults={
                "custom_order_id": order.get("custom_order_id", ""),
                "plan_id": order["plan_id"],
                "user_id": order["user_id"],
                "created_at": datetime.fromtimestamp(order["create_time"]),
                "buy_count": buy_count,
                "actually_paid": order["total_amount"],
                "original_price": order["show_amount"],
                "raw_data": json.dumps(response),
            },
        )
    except Exception as e:
        logger.error(f"Create bill failed, out_trade_no: {out_trade_no}, error: {e}")
        return None, "Create bill failed"

    if not bill:
        logger.error(f"Bill not found, out_trade_no: {out_trade_no}")
        return None, "Bill not found"

    if bill.cdk:
        logger.info(f"CDK already exists, out_trade_no: {out_trade_no}")
        return None, "CDK already exists"

    try:
        plan = Plan.get(Plan.platform == "afdian", Plan.plan_id == order["plan_id"])
        logger.info(
            f"Plan found, out_trade_no: {out_trade_no}, \
plan: {plan}, title: {plan.title}, valid_days: {plan.valid_days}"
        )
    except Exception as e:
        logger.error(f"Plan not found, out_trade_no: {out_trade_no}, error: {e}")
        return None, "Plan not found"

    delta = timedelta(days=plan.valid_days * buy_count)

    if renew_bill:
        cdk = remark
        if renew_bill.expired_at > now:
            expired = renew_bill.expired_at + delta
        else:
            expired = now + delta

        await renew_cdk(cdk, expired)
    else:
        cdk = await acquire_cdk(now + delta, plan.app_group)
        expired = now + delta

    try:
        bill = Bill.get(Bill.platform == "afdian", Bill.order_id == out_trade_no)
        bill.cdk = cdk
        bill.expired_at = expired
        bill.save()
    except Exception as e:
        logger.error(f"Update bill failed, out_trade_no: {out_trade_no}, error: {e}")
        return None, "Update bill failed"

    if not cdk:
        logger.error(f"Query CDK failed, out_trade_no: {out_trade_no}")
        return None, "Query CDK failed"

    logger.success(f"Process order success, out_trade_no: {out_trade_no}")
    return bill, "OK"
