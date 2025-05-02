from typing import Tuple, Any
from loguru import logger
from datetime import datetime
from urllib.parse import unquote
import json

from src.order.factory import OrderData, process_order
from src.config import settings
from .request_yimapay import query


async def process_yimapay_order(platform_trade_no: str) -> Tuple[Any, str]:
    if not platform_trade_no:
        logger.error(f"out_trade_no is required: {platform_trade_no}")
        return None, "not an order"

    params = {
        "trade_no": platform_trade_no,
        "out_trade_no": "",
    }

    response = await query(settings.yimapay_query_order_api, params)
    if not response:
        logger.error(
            f"Query order failed, url: {settings.yimapay_create_order_api}, params: {params}"
        )
        return None, f"Query order failed {platform_trade_no}"

    if response.get("resultCode") != 200:
        logger.error(
            f"Create order failed, url: {settings.yimapay_create_order_api}, params: {params}, response: {response}"
        )
        return None, f"Create order failed {platform_trade_no}"

    order_data = parse_yimapay_data(response["Data"], response)
    if not order_data:
        logger.error(
            f"Parse order data failed, url: {settings.yimapay_create_order_api}, params: {params}, response: {response}"
        )
        return None, f"Parse order data failed {platform_trade_no}"

    return await process_order(order_data)


def parse_yimapay_data(data: dict, response: Any) -> OrderData | None:
    state = data["trade_state"]
    if state != "success":
        logger.error(
            f"trade_state is not success, state: {state}, response: {response}"
        )
        return None

    attach = json.loads(unquote(data["attach"]))

    amount = str(data["amount"])
    if len(amount) > 2:
        amount = amount[:-2] + "." + amount[-2:]
    else:
        amount = "0." + amount.zfill(2)

    try:
        created_at = datetime.strptime(data["pay_time"], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.error(
            f"Invalid pay_time format, pay_time: {data['pay_time']}, response: {response}"
        )
        created_at = datetime.now()

    return OrderData(
        platform="yimapay",
        platform_trade_no=data["trade_no"],
        custom_order_id=data["out_trade_no"],
        plan_id=attach["plan_id"],
        user_id=data["client_ip"],
        created_at=created_at,
        buy_count=1,
        actually_paid=amount,
        original_price=amount,  # 不知道原价，先按照实际支付的价格来
        raw_data=json.dumps(response),
    )
