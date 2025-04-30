import string
from loguru import logger
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
import random
from loguru import logger

from src.database import Plan
from src.config import settings

from .query_yimapay import query

router = APIRouter()


@router.get("/order/yimapay/create")
async def create_order(pay: str, plan_id: str, request: Request):
    logger.debug(f"pay: {pay}, plan_id: {plan_id}")

    pay_type = 0
    if pay == "AlipayQRCode":
        pay_type = 30
    elif pay == "WeChatQRCode":
        pay_type = 20
    else:
        logger.error(f"Invalid pay type: {pay}")
        return {"ec": 400, "code": 1001, "msg": "Invalid pay"}

    try:
        plan = Plan.get(Plan.platform == "yimapay", Plan.plan_id == plan_id)
    except Exception as e:
        logger.error(f"Plan not found, plan_id: {plan_id}, error: {e}")
        return {"ec": 400, "code": 1002, "msg": "Plan not found"}

    out_trade_no = datetime.now().strftime("%Y%m%d%H%M%S") + "".join(
        random.SystemRandom().choices(string.ascii_lowercase + string.digits, k=16)
    )

    client_ip = request.headers.get("X-Forwarded-For", request.client.host)

    # https://api.yimapay.com/docs/api.html?chapter=1
    params = {
        "out_trade_no": out_trade_no,
        "pay_type": pay_type,
        "description": plan.title,
        "amount": plan.amount,
        "client_ip": client_ip,
        "time_expire": 30,  # 分钟
        "notify_url": settings.yimapay_notify_url,
    }

    response = await query(settings.yimapay_create_order_api, params)
    if not response:
        logger.error(
            f"Query order failed, url: {settings.yimapay_create_order_api}, params: {params}"
        )
        return {"ec": 500, "code": 1003, "msg": f"Query order failed {out_trade_no}"}

    if response.get("resultCode") != 200:
        logger.error(
            f"Create order failed, url: {settings.yimapay_create_order_api}, params: {params}, response: {response}"
        )
        return {"ec": 500, "code": 1004, "msg": f"Create order failed {out_trade_no}"}

    pay_url = response.get("Data", {}).get("body")
    if not pay_url:
        logger.error(
            f"Pay URL not found, url: {settings.yimapay_create_order_api}, params: {params}, response: {response}"
        )
        return {"ec": 500, "code": 1005, "msg": f"Pay URL not found {out_trade_no}"}

    return {
        "ec": 200,
        "code": 0,
        "msg": "success",
        "data": {
            "pay_url": pay_url,
            "custom_order_id": out_trade_no,
            "amount": plan.amount,
            "title": plan.title,
        },
    }
