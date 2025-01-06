from aiohttp import ClientSession
from loguru import logger
import os
import json
import time
import hashlib

AFDIAN_USER_ID = os.getenv("AFDIAN_USER_ID")
AFDIAN_API_TOKEN = os.getenv("AFDIAN_API_TOKEN")

if not AFDIAN_USER_ID or not AFDIAN_API_TOKEN:
    raise ValueError("AFDIAN_USER_ID or AFDIAN_API_TOKEN is not set")


async def query(url: str, params: dict) -> dict:
    logger.debug(f"url: {url}, params: {params}")
    query_params = json.dumps(params)
    query_ts = int(time.time())
    query_sign = (
        AFDIAN_API_TOKEN
        + "params"
        + query_params
        + "ts"
        + str(query_ts)
        + "user_id"
        + AFDIAN_USER_ID
    )
    query_sign = hashlib.md5(query_sign.encode()).hexdigest()

    query_body = {
        "user_id": AFDIAN_USER_ID,
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
    return await query(
        "https://afdian.com/api/open/query-order", {"out_trade_no": out_trade_no}
    )


async def query_order_by_page(page: int = 1, per_page: int = 100) -> dict:
    return await query(
        "https://afdian.com/api/open/query-order", {"page": page, "per_page": per_page}
    )
