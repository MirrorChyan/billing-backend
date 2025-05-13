import json
import string
from loguru import logger
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
import random

from src.database import Plan
from src.config import settings

from .request_yimapay import query

router = APIRouter()

ORDER_EXPIRY_TIME = 60  # 60 minutes

@router.get("/order/yimapay/create")
async def create_order(pay: str, plan_id: str, request: Request):
    logger.debug(f"pay: {pay}, plan_id: {plan_id}")

    pay_type = 0
    if pay == "AlipayQRCode":
        pay_type = 30
    elif pay == "AlipayH5":
        pay_type = 30
    elif pay == "WeChatQRCode":
        pay_type = 20
    elif pay == "WeChatH5":
        pay_type = 23
    else:
        logger.error(f"Invalid pay type: {pay}")
        return {"ec": 400, "code": 21001, "msg": "Invalid pay"}

    try:
        plan = Plan.get(Plan.platform == "yimapay", Plan.plan_id == plan_id)
    except Exception as e:
        logger.error(f"Plan not found, plan_id: {plan_id}, error: {e}")
        return {"ec": 404, "code": 21002, "msg": "Plan not found"}

    custom_order_id = datetime.now().strftime("%Y%m%d%H%M%S") + "".join(
        random.SystemRandom().choices(string.ascii_lowercase + string.digits, k=18)
    )

    client_ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()

    attach = {
        "pay": pay,
        "plan_id": plan.plan_id,
    }

    # https://api.yimapay.com/docs/api.html?chapter=1
    params = {
        "out_trade_no": custom_order_id,
        "pay_type": pay_type,
        "description": plan.title,
        "amount": plan.amount,
        "client_ip": client_ip,
        "time_expire": ORDER_EXPIRY_TIME,  # 分钟
        "notify_url": settings.yimapay_notify_url + settings.yimapay_webhook_secret,
        "attach": json.dumps(attach, separators=(',', ':')),
    }

    response = await query(settings.yimapay_create_order_api, params)
    if not response:
        logger.error(
            f"Query order failed, url: {settings.yimapay_create_order_api}, params: {params}"
        )
        return {"ec": 500, "code": 21000, "msg": f"Query order failed {custom_order_id}"}

    if response.get("resultCode") != 200:
        logger.error(
            f"Create order failed, url: {settings.yimapay_create_order_api}, params: {params}, response: {response}"
        )
        return {
            "ec": 500,
            "code": 21000,
            "msg": f"Create order failed {custom_order_id}",
        }

    pay_url = response.get("Data", {}).get("body")
    if not pay_url:
        logger.error(
            f"Pay URL not found, url: {settings.yimapay_create_order_api}, params: {params}, response: {response}"
        )
        return {"ec": 500, "code": 21000, "msg": f"Pay URL not found {custom_order_id}"}

    return {
        "ec": 200,
        "code": 0,
        "msg": "success",
        "data": {
            "pay_url": pay_url,
            "expiry_time": ORDER_EXPIRY_TIME,
            "custom_order_id": custom_order_id,
            "amount": plan.amount,
            "title": plan.title,
        },
    }
