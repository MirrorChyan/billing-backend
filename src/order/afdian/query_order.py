from loguru import logger
from fastapi import APIRouter
from datetime import datetime

from src.database import Bill, Plan, Reward
from .factory import process_order

router = APIRouter()


@router.get("/order/afdian")
async def query_order(order_id: str = None, custom_order_id: str = None):
    # logger.debug(f"order_id: {order_id}, custom_order_id: {custom_order_id}")
    if order_id and not order_id.isdigit():
        reward = query_reward(order_id)
        if reward:
            return reward

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

    if not bill:
        if not order_id:
            return {"ec": 400, "msg": "Order not found"}

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


def query_reward(reward_key: str):
    reward = Reward.get_or_none(Reward.reward_key == reward_key)
    if not reward:
        return None

    return {
        "ec": 200,
        "msg": "Success",
        "data": {
            "cdk": "",  # for compatibility with order
            "reward_key": reward.reward_key,
            "start_at": reward.start_at,
            "expired_at": reward.expired_at,
            "title": reward.title,
            "valid_days": reward.valid_days,
            "applications": reward.applications,
            "modules": reward.modules,
            "remaining": reward.remaining,
            "order_created_after": reward.order_created_after,
            "order_created_before": reward.order_created_before,
        },
    }
