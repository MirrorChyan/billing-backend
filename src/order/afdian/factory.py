from dataclasses import dataclass
from typing import Tuple
from loguru import logger
from datetime import datetime, timedelta
import json

from src.database import Bill, Plan
from src.cdk.acquire_cdk import acquire_cdk
from .query_afdian import query_order_by_out_trade_no


async def process_order(out_trade_no: str) -> Tuple[bool, str]:
    response = await query_order_by_out_trade_no(out_trade_no)
    if not response or response.get("ec") != 200:
        logger.error(
            f"Query order failed, out_trade_no: {out_trade_no}, response: {response}"
        )
        return False, "Query order failed"

    order = response.get("data", {}).get("list", [])
    if not order:
        logger.error(
            f"Order not found, out_trade_no: {out_trade_no}, response: {response}"
        )
        return False, "Order not found"

    order = order[0]

    now = datetime.now()
    try:
        bill = Bill.get_or_create(
            platform="afdian",
            order_id=order["out_trade_no"],
            defaults={
                "plan_id": order["plan_id"],
                "user_id": order["user_id"],
                "created_at": now,
                "actually_paid": order["total_amount"],
                "original_price": order["show_amount"],
                "raw_data": json.dumps(response),
            },
        )
    except Exception as e:
        logger.error(f"Create bill failed, out_trade_no: {out_trade_no}, error: {e}")

    if not bill:
        logger.error(f"Create bill failed, out_trade_no: {out_trade_no}")
        return False, "Create bill failed"

    bill = bill[0]
    if not bill:
        logger.error(f"Bill not found, out_trade_no: {out_trade_no}")
        return False, "Bill not found"

    if bill.cdk:
        logger.info(f"CDK already exists, out_trade_no: {out_trade_no}")
        return False, "CDK already exists"

    try:
        plan = Plan.get(Plan.platform == "afdian", Plan.plan_id == order["plan_id"])
        logger.info(
            f"Plan found, out_trade_no: {out_trade_no}, \
plan: {plan}, title: {plan.title}, valid_days: {plan.valid_days}"
        )
    except Exception as e:
        logger.error(f"Plan not found, out_trade_no: {out_trade_no}, error: {e}")
        return False, "Plan not found"

    expired = now + timedelta(days=plan.valid_days)
    cdk = await acquire_cdk(expired)
    if not cdk:
        logger.error(f"Query CDK failed, out_trade_no: {out_trade_no}")
        return False, "Query CDK failed"

    try:
        bill = Bill.get(Bill.platform == "afdian", Bill.order_id == out_trade_no)
        bill.cdk = cdk
        bill.expired_at = expired
        bill.save()
    except Exception as e:
        logger.error(f"Update bill failed, out_trade_no: {out_trade_no}, error: {e}")
        return False, "Update bill failed"

    return True, "OK"
