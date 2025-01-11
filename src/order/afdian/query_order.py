from loguru import logger
from fastapi import APIRouter

from src.database import Bill, Plan

router = APIRouter()


@router.get("/order/afdian")
async def query_order(order_id: str):
    logger.debug(f"order_id: {order_id}")

    try:
        bill = Bill.get(Bill.platform == "afdian", Bill.order_id == order_id)
    except Exception as e:
        logger.error(f"Query bill failed, order_id: {order_id}, error: {e}")
        return {"ec": 404, "msg": "Bill not found"}

    try:
        plan = Plan.get(Plan.platform == "afdian", Plan.plan_id == bill.plan_id)
    except Exception as e:
        logger.error(f"Plan not found, order_id: {order_id}, error: {e}")
        return {"ec": 403, "msg": "Plan not found"}

    return {
        "ec": 200,
        "msg": "Success",
        "data": {
            "platform": bill.platform,
            "order_id": bill.order_id,
            "plan_id": bill.plan_id,
            "user_id": bill.user_id,
            "created_at": bill.created_at,
            "expired_at": bill.expired_at,
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
