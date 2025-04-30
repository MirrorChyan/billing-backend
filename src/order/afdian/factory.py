from typing import Tuple, Any
from loguru import logger
from datetime import datetime
import json

from src.order.factory import OrderData, process_order
from .request_afdian import query_order_by_out_trade_no


async def process_afdian_order(out_trade_no: str) -> Tuple[Any, str]:
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

    product_type = order.get("product_type", None)
    if product_type != 1:
        logger.error(
            f"Product type not supported, out_trade_no: {out_trade_no}, product_type: {product_type}"
        )
        return None, "Product type not supported"

    order_data = OrderData(
        platform="afdian",
        platform_trade_no=out_trade_no,
        custom_order_id=order.get("custom_order_id", ""),
        plan_id=order["plan_id"],
        user_id=order["user_id"],
        created_at=datetime.fromtimestamp(order["create_time"]),
        buy_count=order.get("sku_detail", [{}])[0].get("count", 1),
        actually_paid=order["total_amount"],
        original_price=order["show_amount"],
        raw_data=json.dumps(response),
    )

    return await process_order(order_data)
