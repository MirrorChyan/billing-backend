from dataclasses import dataclass
from typing import Tuple
from loguru import logger
from datetime import datetime

from .query_afdian import query_order_by_out_trade_no
from src.database import Bill, Plan


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

    try:
        Bill.create(
            platform="afdian",
            order_id=order["out_trade_no"],
            plan_id=order["plan_id"],
            user_id=order["user_id"],
            created_at=datetime.now(),
            actually_paid=order["total_amount"],
            original_price=order["show_amount"],
        )
    except Exception as e:
        logger.error(f"Create bill failed, out_trade_no: {out_trade_no}, error: {e}")
        # return False, "Create bill failed"

    try:
        plan = Plan.get(Plan.platform == "afdian", Plan.plan_id == order["plan_id"])
        logger.info(
            f"Plan found, out_trade_no: {out_trade_no}, \
plan: {plan}, title: {plan.title}, valid_days: {plan.valid_days}"
        )
    except Exception as e:
        logger.error(f"Plan not found, out_trade_no: {out_trade_no}, error: {e}")
        return False, "Plan not found"

    # TODO: 请求 CDK

    return True, "OK"
