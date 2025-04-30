from loguru import logger
from fastapi import APIRouter

from src.config import settings
from .factory import process_afdian_order

router = APIRouter()


@router.post("/order/afdian/webhook/" + settings.afdian_webhook_secret)
async def afdian_webhook(webhook_body: dict):
    logger.debug(f"webhook_body: {webhook_body}")

    out_trade_no = webhook_body.get("data", {}).get("order", {}).get("out_trade_no")
    logger.info(f"out_trade_no: {out_trade_no}")

    if not out_trade_no:
        logger.error("Invalid out_trade_no")
        return {"ec": 400, "em": "Invalid out_trade_no"}

    if out_trade_no == settings.afdian_test_out_trade_no:
        logger.warning(
            f"Test order, out_trade_no: {out_trade_no}, webhook_body: {webhook_body}"
        )
        return {"ec": 200, "em": "Test success"}

    success, message = await process_afdian_order(out_trade_no)
    if not success:
        logger.error(
            f"Process order failed, out_trade_no: {out_trade_no}, message: {message}"
        )
        return {"ec": 400, "em": message}

    logger.success(
        f"Process order success, out_trade_no: {out_trade_no}, message: {message}"
    )
    return {"ec": 200, "em": message}
