from loguru import logger
from fastapi import APIRouter

from src.database import Bill, Plan
from .yimapay.factory import process_yimapay_order
from .afdian.factory import process_afdian_order

router = APIRouter()


@router.get("/order/query")
async def query_order(order_id: str = None, custom_order_id: str = None):
    # logger.debug(f"order_id: {order_id}, custom_order_id: {custom_order_id}")
    if order_id:
        bill = Bill.get_or_none((Bill.order_id == order_id) | (Bill.custom_order_id == order_id))
    elif custom_order_id:
        bill = Bill.get_or_none(Bill.custom_order_id == custom_order_id)
    else:
        return {"ec": 400, "code": 21001, "msg": "order_id is required"}

    if not bill:
        if not order_id:  # 通过 custom_order_id 来查的
            return {"ec": 404, "code": 21002, "msg": "order not found"}

        logger.warning(
            f"Bill not found, order_id: {order_id}, try to query from Afdian/Yimapay"
        )
        if len(order_id) == 22 and order_id.startswith("YMF"):
            bill, message = await process_yimapay_order(order_id, "")
        elif len(order_id) == 32 and order_id[:15].isdigit():
            bill, message = await process_yimapay_order("", order_id)
        elif len(order_id) == 27 and order_id.isdigit():
            bill, message = await process_afdian_order(order_id)
        else:
            return {"ec": 404, "code": 21002, "msg": "Order not found"}

        if not bill:
            return {"ec": 400, "code": 1, "msg": message}

    try:
        plan = Plan.get(Plan.plan_id == bill.plan_id)
    except Exception as e:
        logger.error(f"Plan not found, order_id: {order_id}, error: {e}")
        return {"ec": 500, "code": 21000, "msg": "Unknow error, please contact us!"}

    if not bill.cdk:
        logger.error(f"CDK not found, order_id: {order_id}")
        return {"ec": 500, "code": 21000, "msg": "Unknow error, please contact us!"}

    latest_bill = (
        Bill.select()
        .where(Bill.cdk == bill.cdk)
        .order_by(Bill.expired_at.desc())
        .get_or_none()
    )
    if not latest_bill:
        logger.error(f"CDK not found, order_id: {order_id}")
        return {"ec": 500, "code": 21000, "msg": "Unknow error, please contact us!"}

    return {
        "ec": 200,
        "code": 0,
        "msg": "Success",
        "data": {
            "platform": bill.platform,
            "order_id": bill.order_id,
            "custom_order_id": bill.custom_order_id,
            "plan_id": bill.plan_id,
            "buy_count": bill.buy_count,
            "user_id": bill.user_id,
            "created_at": bill.created_at,
            "expired_at": latest_bill.expired_at,
            "cdk": bill.cdk,
            "plan": {
                "title": plan.title,
                "valid_days": plan.valid_days,
                "group": plan.app_group,
                "applications": plan.applications,
                "modules": plan.modules,
                "cdk_number": plan.cdk_number,
            },
        },
    }
