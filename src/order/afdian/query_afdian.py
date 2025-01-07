from aiohttp import ClientSession
from loguru import logger
import json
import time
import hashlib

from src.config import settings


async def query(url: str, params: dict) -> dict:
    logger.debug(f"url: {url}, params: {params}")
    query_params = json.dumps(params)
    query_ts = int(time.time())
    query_sign = (
        settings.afdian_api_token
        + "params"
        + query_params
        + "ts"
        + str(query_ts)
        + "user_id"
        + settings.afdian_user_id
    )
    query_sign = hashlib.md5(query_sign.encode()).hexdigest()

    query_body = {
        "user_id": settings.afdian_user_id,
        "params": query_params,
        "ts": query_ts,
        "sign": query_sign,
    }

    async with ClientSession() as session:
        async with session.post(url, json=query_body) as response:
            response = await response.json()
            logger.debug(f"url: {url}, params: {params}, response: {response}")

    return response


async def query_order_by_out_trade_no(out_trade_no: str) -> dict:
    return await query(settings.afdian_query_order_api, {"out_trade_no": out_trade_no})


async def query_order_by_page(page: int = 1, per_page: int = 100) -> dict:
    return await query(
        settings.afdian_query_order_api, {"page": page, "per_page": per_page}
    )
