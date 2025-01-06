from aiohttp import ClientSession
from loguru import logger
from datetime import datetime
from typing import Optional
import json


async def query_cdk(expireTime: datetime) -> Optional[str]:
    url = "http://127.0.0.1:9768/acquire"
    query_body = {
        "expireTime": expireTime.strftime("%Y-%m-%d %H:%M:%S"),
    }
    async with ClientSession() as session:
        async with session.post(url, json=query_body) as response:
            # response = await response.json()
            response = await response.text()
            response = json.loads(response)
            logger.debug(f"url: {url}, query_body: {query_body}, response: {response}")

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
