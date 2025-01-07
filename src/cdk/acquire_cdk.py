from aiohttp import ClientSession
from loguru import logger
from datetime import datetime
from typing import Optional
import json

from src.config import settings


async def acquire_cdk(expireTime: datetime) -> Optional[str]:
    query_body = {
        "expireTime": expireTime.strftime("%Y-%m-%d %H:%M:%S"),
    }
    async with ClientSession() as session:
        async with session.post(settings.cdk_acquire_api, json=query_body) as response:
            response = await response.json()
            logger.debug(f"url: {settings.cdk_acquire_api}, query_body: {query_body}, response: {response}")

    error_code = response.get("code", 1)
    if error_code:
        logger.error(f"Query CDK failed, error_code: {error_code}")
        return None

    data = response.get("data", "")
    if not data:
        logger.error(f"Query CDK failed, data is empty")
        return None

    logger.info(f"cdk: {data}")
    return data
