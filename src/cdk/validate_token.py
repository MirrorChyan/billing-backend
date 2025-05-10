from aiohttp import ClientSession
from loguru import logger

from src.config import settings
from src.exception_notifer import exception_notify


async def validate_token(rid: str, token: str) -> bool:
    query_params = {
        "rid": rid,
        "token": token,
    }

    try:
        async with ClientSession() as session:
            async with session.post(
                settings.cdk_validate_api, params=query_params
            ) as response:
                response = await response.json()
                logger.debug(f"response: {response}")
    except Exception as e:
        logger.error(
            f"failed to request, url: {settings.cdk_validate_api}, query_params: {query_params}, error: {e}"
        )
        await exception_notify("Auth", e)
        return False

    if response.get("code", -1) != 0:
        logger.error(
            f"failed to validate token, response: {response}, url: {settings.cdk_validate_api}, query_params: {query_params}"
        )
        return False

    logger.success(f"validate token success, rid: {rid}")
    return True
