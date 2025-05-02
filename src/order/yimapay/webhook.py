from loguru import logger
from fastapi import APIRouter, Request

from src.config import settings
from src.order.factory import process_order
from .factory import parse_yimapay_data

router = APIRouter()


@router.post("/order/yimapay/webhook/" + settings.yimapay_webhook_secret)
async def yimapay_webhook(request: Request):
    form_data = await request.form()
    logger.debug(f"form_data: {form_data}")

    key = form_data.get("key")
    if key != settings.yimapay_secret_key:
        logger.error(f"Invalid key: {key}")
        return {"code": "FAIL", "message": f"Invalid key {key}"}

    app_id = form_data.get("app_id")
    if app_id != settings.yimapay_app_id:
        logger.error(f"Invalid app_id: {app_id}")
        return {"code": "FAIL", "message": f"Invalid app_id {app_id}"}

    trade_state = form_data.get("trade_state")
    if trade_state != "success":
        logger.error(f"Invalid trade_state: {trade_state}")
        return {"code": "FAIL", "message": f"Invalid trade_state {trade_state}"}

    trade_no = form_data.get("trade_no")
    if not trade_no:
        logger.error(f"Invalid trade_no: {trade_no}")
        return {"ec": 400, "code": "FAIL", "message": f"Invalid trade_no {trade_no}"}

    order_data = parse_yimapay_data(form_data, form_data)
    if not order_data:
        logger.error(f"Parse order data failed, trade_no: {trade_no}")
        return {"code": "FAIL", "message": f"Parse order data failed: {trade_no}"}

    success, message = await process_order(order_data)
    if not success:
        logger.error(f"Process order failed, trade_no: {trade_no}, message: {message}")
        return {
            "code": "FAIL",
            "message": f"Process order failed: {trade_no} {message}",
        }

    logger.success(f"Process order success, trade_no: {trade_no}")
    return {"code": "SUCCESS", "message": "Success"}
