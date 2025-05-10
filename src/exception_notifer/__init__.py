from aiohttp import ClientSession
from loguru import logger

from src.config import settings


async def exception_notify(module: str, error: Exception):
    query_body = {
        "module": module,
        "error": str(error),
    }

    logger.debug(f"exception notify: {query_body}")

    try:
        async with ClientSession() as session:
            async with session.post(
                settings.exception_notify_url, json=query_body
            ) as response:
                pass
    except Exception as e:
        logger.error(
            f"exception notify error: {e}, url: {settings.exception_notify_url}, query_body: {query_body}"
        )

    logger.debug(f"exception notify success: {query_body}")
    return
