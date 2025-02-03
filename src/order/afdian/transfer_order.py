from loguru import logger
from fastapi import APIRouter, Query
from datetime import datetime, timedelta

from src.cdk.renew_cdk import renew_cdk
from src.database import Bill, Plan

router = APIRouter()


@router.get("/order/afdian/transfer")
async def query_order(_from: str = Query(..., alias="from"), to: str = None):
    logger.debug(f"_from: {_from}, to: {to}")

    if not _from or not to:
        logger.error(f"_from or to is None")
        return {"ec": 400, "msg": "from and to is required"}

    from_bill = Bill.get_or_none(Bill.platform == "afdian", Bill.order_id == _from)
    to_bill = Bill.get_or_none(Bill.platform == "afdian", Bill.order_id == to)

    if not from_bill or not to_bill:
        logger.error(f"order not found, _from: {_from}, to: {to}")
        return {"ec": 400, "msg": "Order not found"}

    now = datetime.now()

    # 超过3天的订单不允许合并
    if (now - from_bill.created_at).days > 3:
        logger.error(f"order expired, _from: {_from}")
        return {
            "ec": 403,
            "msg": "Order older than 3 days",
        }

    # 已经转过一次了
    if from_bill.expired_at < now:
        logger.error(f"order already transferred, _from: {_from}")
        return {"ec": 403, "msg": "Order already transferred"}

    if from_bill.cdk == to_bill.cdk:
        logger.error(f"CDK is the same, _from: {_from}, to: {to}")
        return {"ec": 403, "msg": "CDK is same, Order already transferred"}

    try:
        from_plan = Plan.get(
            Plan.platform == "afdian", Plan.plan_id == from_bill.plan_id
        )
    except Exception as e:
        logger.error(f"Plan not found, order_id: {from_bill.order_id}, error: {e}")
        return {"ec": 500, "msg": "Plan not found"}

    from_bill.expired_at = now
    # cdk-backend 那边不允许过去的时间，加个10秒的缓冲
    await renew_cdk(from_bill.cdk, from_bill.expired_at + timedelta(seconds=10))

    # 方便查账，Bill 里搜这个 CDK 能找同时找到两条记录
    from_bill.cdk = to_bill.cdk
    from_bill.save()

    delta = timedelta(days=from_plan.valid_days * from_bill.buy_count)

    if to_bill.expired_at > now:
        to_bill.expired_at = to_bill.expired_at + delta
    else:
        to_bill.expired_at = now + delta

    await renew_cdk(to_bill.cdk, to_bill.expired_at)
    to_bill.save()

    return {"ec": 200, "msg": "Success"}
