from aiohttp import ClientSession
from loguru import logger
from datetime import datetime
from typing import Optional

from src.config import settings


async def acquire_cdk(expireTime: datetime, group: str) -> Optional[str]:
    query_body = {
        "group": group,
        "expireTime": expireTime.strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        async with ClientSession() as session:
            async with session.post(
                settings.cdk_acquire_api, json=query_body
            ) as response:
                response = await response.json()
                logger.debug(
                    f"url: {settings.cdk_acquire_api}, query_body: {query_body}, response: {response}"
                )
    except Exception as e:
        logger.error(f"Query CDK failed, error: {e}")
        return None

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
