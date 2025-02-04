from loguru import logger
from fastapi import APIRouter

from src.database import Bill, Plan
from .factory import process_order

router = APIRouter()


@router.get("/order/afdian")
async def query_order(order_id: str = None, custom_order_id: str = None):
    logger.debug(f"order_id: {order_id}, custom_order_id: {custom_order_id}")

    if not order_id and not custom_order_id:
        logger.error(f"order_id and custom_order_id is None")
        return {"ec": 400, "msg": "order_id is required"}

    if order_id:
        bill = Bill.get_or_none(Bill.platform == "afdian", Bill.order_id == order_id)
    elif custom_order_id:
        bill = Bill.get_or_none(
            Bill.platform == "afdian", Bill.custom_order_id == custom_order_id
        )
    else:
        return {"ec": 400, "msg": "order_id is required"}

    if not bill and order_id:
        # 如果订单号是正确的，能走到这里说明没收到爱发电的推送
        # 主动去爱发电查一下
        # logger.warning(
        #     f"Bill not found, order_id: {order_id}, custom_order_id: {custom_order_id}"
        # )
        bill, message = await process_order(order_id)
        if not bill:
            # logger.error(f"order not found, order_id: {order_id}")
            return {"ec": 400, "msg": message}

    try:
        plan = Plan.get(Plan.platform == "afdian", Plan.plan_id == bill.plan_id)
    except Exception as e:
        logger.error(f"Plan not found, order_id: {order_id}, error: {e}")
        return {"ec": 500, "msg": "Plan not found"}

    if not bill.cdk:
        logger.error(f"CDK not found, order_id: {order_id}")
        return {"ec": 500, "msg": "Unknow error, please contact us!"}

    latest_bill = (
        Bill.select()
        .where(Bill.cdk == bill.cdk)
        .order_by(Bill.expired_at.desc())
        .get_or_none()
    )
    if not latest_bill:
        logger.error(f"CDK not found, order_id: {order_id}")
        return {"ec": 500, "msg": "Unknow error, please contact us!"}

    return {
        "ec": 200,
        "msg": "Success",
        "data": {
            "platform": bill.platform,
            "order_id": bill.order_id,
            "plan_id": bill.plan_id,
            "buy_count": bill.buy_count,
            "user_id": bill.user_id,
            "created_at": bill.created_at,
            "expired_at": latest_bill.expired_at,
            "cdk": bill.cdk,
            "plan": {
                "title": plan.title,
                "valid_days": plan.valid_days,
                "applications": plan.applications,
                "modules": plan.modules,
                "cdk_number": plan.cdk_number,
            },
        },
    }
