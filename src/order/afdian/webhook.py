import os
from loguru import logger
from fastapi import APIRouter

from .factory import process_order

router = APIRouter()


AFDIAN_WEBHOOK_SECRET = os.getenv("AFDIAN_WEBHOOK_SECRET")
AFDIAN_TEST_OUT_TRADE_NO = os.getenv("AFDIAN_TEST_OUT_TRADE_NO")

if not AFDIAN_WEBHOOK_SECRET:
    raise ValueError("AFDIAN_WEBHOOK_SECRET is not set")


@router.post("/order/afdian/webhook/" + AFDIAN_WEBHOOK_SECRET)
async def afdian_webhook(webhook_body: dict):
    logger.debug(f"webhook_body: {webhook_body}")

    out_trade_no = webhook_body.get("data", {}).get("order", {}).get("out_trade_no")
    if AFDIAN_TEST_OUT_TRADE_NO:
        logger.warning(
            f"AFDIAN_TEST_OUT_TRADE_NO is set, using it for testing: {AFDIAN_TEST_OUT_TRADE_NO}"
        )
        out_trade_no = AFDIAN_TEST_OUT_TRADE_NO

    logger.info(f"out_trade_no: {out_trade_no}")
    if not out_trade_no:
        logger.error("Invalid out_trade_no")
        return {"ec": 400, "em": "Invalid out_trade_no"}

    success, message = await process_order(out_trade_no)
    if not success:
        logger.error(
            f"Process order failed, out_trade_no: {out_trade_no}, message: {message}"
        )
        return {"ec": 400, "em": message}

    logger.success(
        f"Process order success, out_trade_no: {out_trade_no}, message: {message}"
    )
    return {"ec": 200, "em": message}
