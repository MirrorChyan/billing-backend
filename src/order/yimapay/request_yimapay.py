from aiohttp import ClientSession
from loguru import logger
import hashlib
import asyncio

from src.config import settings

def gen_sign(params: dict) -> str:
    # 第一步：对参数按照key=value的格式，并按照参数名ASCII字典序排序
    sign = "&".join([f"{key}={value}" for key, value in sorted(params.items()) if key != "sign" and value])
    # 第二步：拼接API密钥
    sign = f"{sign}&key={settings.yimapay_secret_key}"
    # 第三步：进行MD5运算，再将得到的字符串所有字符转换为大写
    sign = hashlib.md5(sign.encode("utf-8")).hexdigest().upper()
    return sign

async def query(url: str, params: dict) -> dict:
    logger.debug(f"url: {url}, params: {params}")

    params["app_id"] = settings.yimapay_app_id

    # gen_sign必须是最后一步
    params["sign"] = gen_sign(params)

    for i in range(1, 4):
        try:
            async with ClientSession() as session:
                async with session.post(url, params=params) as response:
                    response = await response.json()
                    logger.debug(f"url: {url}, params: {params}, response: {response}")
                    return response
        except Exception as e:
            logger.error(f"url: {url}, params: {params}, query error: {e}")
            await asyncio.sleep(i * i)
            continue

    logger.error(f"query failed, url: {url}, params: {params}")
    return {}
