from aiohttp import ClientSession
from loguru import logger
from datetime import datetime

from src.config import settings
from src.exception_notifer import exception_notify


async def renew_cdk(cdk: str, expireTime: datetime) -> bool:
    query_body = {
        "cdk": cdk,
        "expireTime": expireTime.strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        async with ClientSession() as session:
            async with session.post(settings.cdk_renew_api, json=query_body) as response:
                response = await response.json()
                logger.debug(f"url: {settings.cdk_renew_api}, query_body: {query_body}, response: {response}")
    except Exception as e:
        logger.error(f"Renew CDK failed, error: {e}")
        await exception_notify("Auth", e)
        return False

    error_code = response.get("code", 1)
    if error_code:
        logger.error(f"Renew CDK failed, error_code: {error_code}")
        return False
    
    logger.info(f"Renew CDK success, cdk: {cdk}")
    return True
