from loguru import logger
from fastapi import APIRouter, Request

from src.config import settings
from src.order.factory import process_order
from .factory import parse_yimapay_data
from .request_yimapay import gen_sign

router = APIRouter()


@router.post("/order/yimapay/webhook/" + settings.yimapay_webhook_secret)
async def yimapay_webhook(request: Request):
    form_data = await request.form()
    logger.debug(f"form_data: {form_data}")

    sign = form_data.get("sign")
    if not sign:
        logger.error(f"Invalid sign: {sign}")
        return {"code": "FAIL", "message": f"Invalid sign {sign}"}
    exptected_sign = gen_sign(form_data)
    if sign != exptected_sign:
        logger.error(f"Invalid sign: {sign}, expected: {exptected_sign}")
        return {"code": "FAIL", "message": f"Invalid sign {sign}"}
    

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
