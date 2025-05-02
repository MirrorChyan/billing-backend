from typing import Annotated
from loguru import logger
from fastapi import APIRouter, Form, Request, Response
import asyncio

from src.config import settings
from .factory import process_yimapay_order

router = APIRouter()


@router.post("/order/yimapay/webhook/" + settings.yimapay_webhook_secret)
async def yimapay_webhook(app_id: Annotated[str, Form()], trade_no: Annotated[str, Form()], response: Response):
    logger.debug(f"app_id: {app_id}, trade_no: {trade_no}")

    if app_id != settings.yimapay_app_id:
        logger.error(f"Invalid app_id: {app_id}")
        response.status_code = 403
        return {"code": "FAIL", "message": f"Invalid app_id {app_id}"}

    if not trade_no:
        logger.error(f"Invalid trade_no: {trade_no}")
        response.status_code = 400
        return {"code": "FAIL", "message": f"Invalid trade_no {trade_no}"}

    # Yimapay 第一次回调来的时候，他们服务器可能有点延迟，立马查查到的是还未完成付款
    await asyncio.sleep(1)

    success, message = await process_yimapay_order(trade_no)
    if not success:
        logger.error(
            f"Process order failed, trade_no: {trade_no}, message: {message}"
        )
        response.status_code = 500
        return {"code": "FAIL", "message": f"{message} {trade_no}"}

    logger.success(
        f"Process order success, trade_no: {trade_no}, message: {message}"
    )
    return {"code": "SUCCESS", "message": "Success"}
