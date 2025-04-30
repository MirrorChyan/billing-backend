from dataclasses import dataclass
from typing import Tuple, Any
from loguru import logger
from datetime import datetime, timedelta
import json

from src.database import Bill, Plan
from src.cdk.acquire_cdk import acquire_cdk


@dataclass
class OrderData:
    platform: str
    platform_trade_no: str
    custom_order_id: str
    plan_id: str
    user_id: str
    created_at: datetime
    buy_count: int
    actually_paid: str
    original_price: str
    raw_data: str


async def process_order(order_data: OrderData) -> Tuple[Any, str]:
    try:
        bill, created = Bill.get_or_create(
            platform=order_data.platform,
            order_id=order_data.platform_trade_no,
            defaults={
                "custom_order_id": order_data.custom_order_id,
                "plan_id": order_data.plan_id,
                "user_id": order_data.user_id,
                "created_at": order_data.created_at,
                "buy_count": order_data.buy_count,
                "actually_paid": order_data.actually_paid,
                "original_price": order_data.original_price,
                "raw_data": order_data.raw_data,
            },
        )
    except Exception as e:
        logger.error(
            f"Create bill failed, out_trade_no: {order_data.platform_trade_no}, error: {e}"
        )
        return None, "Create bill failed"

    if not bill:
        logger.error(f"Bill not found, out_trade_no: {order_data.platform_trade_no}")
        return None, "Bill not found"

    if bill.cdk:
        logger.info(f"CDK already exists, out_trade_no: {order_data.platform_trade_no}")
        return None, "CDK already exists"

    try:
        plan = Plan.get(
            Plan.platform == order_data.platform, Plan.plan_id == order_data.plan_id
        )
        logger.info(
            f"Plan found, out_trade_no: {order_data.platform_trade_no}, \
plan: {plan}, title: {plan.title}, valid_days: {plan.valid_days}"
        )
    except Exception as e:
        logger.error(
            f"Plan not found, out_trade_no: {order_data.platform_trade_no}, error: {e}"
        )
        return None, "Plan not found"

    delta = timedelta(days=plan.valid_days * order_data.buy_count)

    expired = datetime.now() + delta
    cdk = await acquire_cdk(expired, plan.app_group)

    try:
        bill = Bill.get(
            Bill.platform == order_data.platform,
            Bill.order_id == order_data.platform_trade_no,
        )
        bill.cdk = cdk
        bill.expired_at = expired
        bill.save()
    except Exception as e:
        logger.error(
            f"Update bill failed, out_trade_no: {order_data.platform_trade_no}, error: {e}"
        )
        return None, "Update bill failed"

    if not cdk:
        logger.error(f"Query CDK failed, out_trade_no: {order_data.platform_trade_no}")
        return None, "Query CDK failed"

    logger.success(
        f"Process order success, out_trade_no: {order_data.platform_trade_no}"
    )
    return bill, "OK"
