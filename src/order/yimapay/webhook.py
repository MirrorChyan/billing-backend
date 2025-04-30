from loguru import logger
from fastapi import APIRouter

from src.config import settings
from .factory import process_yimapay_order

router = APIRouter()


@router.post("/order/yimapay/webhook/" + settings.yimapay_webhook_secret)
async def yimapay_webhook(app_id: str, trade_no: str):
    logger.debug(f"app_id: {app_id}, trade_no: {trade_no}")

    if app_id != settings.yimapay_app_id:
        logger.error(f"Invalid app_id: {app_id}")
        return {"code": "FAIL", "message": f"Invalid app_id {app_id}"}

    if not trade_no:
        logger.error(f"Invalid trade_no: {trade_no}")
        return {"code": "FAIL", "message": f"Invalid trade_no {trade_no}"}

    success, message = await process_yimapay_order(trade_no)
    if not success:
        logger.error(
            f"Process order failed, trade_no: {trade_no}, message: {message}"
        )
        return {"code": "FAIL", "message": f"{message} {trade_no}"}

    logger.success(
        f"Process order success, trade_no: {trade_no}, message: {message}"
    )
    return {"code": "SUCCESS", "message": "Success"}
