from loguru import logger
from fastapi import APIRouter, Query
from datetime import datetime, timedelta

from src.cdk.renew_cdk import renew_cdk
from src.database import Bill, Plan, Transaction, Reward

router = APIRouter()


@router.get("/order/transfer")
async def transfer_order(_from: str = Query(..., alias="from"), to: str = None):
    logger.debug(f"_from: {_from}, to: {to}")

    if not _from or not to:
        logger.error(f"_from or to is None")
        return {"ec": 400, "msg": "from and to is required"}

    to_bill = Bill.get_or_none(Bill.order_id == to)

    if not to_bill:
        logger.error(f"order not found, to: {to}")
        return {"ec": 400, "msg": "Order not found"}

    if not _from.isdigit() and not _from.startswith("YMF"): # yimapay 的脏逻辑（
        reward = await get_reward(_from, to_bill)
        if reward:
            return reward

    from_bill = Bill.get_or_none(Bill.order_id == _from)
    if not from_bill:
        logger.error(f"order not found, _from: {_from}")
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
    if from_bill.expired_at < now or from_bill.transferred < 0:
        logger.error(f"order already transferred, _from: {_from}")
        return {"ec": 403, "msg": "Order already transferred"}

    if from_bill.cdk == to_bill.cdk:
        logger.error(f"CDK is the same, _from: {_from}, to: {to}")
        return {"ec": 403, "msg": "CDK is same, Order already transferred"}

    delta = from_bill.expired_at - now

    from_bill.expired_at = now
    # cdk-backend 那边不允许过去的时间，加个10秒的缓冲
    await renew_cdk(from_bill.cdk, from_bill.expired_at + timedelta(seconds=10))

    transferred = from_bill.transferred

    # 方便查账，Bill 里搜这个 CDK 能找同时找到两条记录
    from_bill.cdk = to_bill.cdk
    from_bill.transferred = -1
    from_bill.save()


    if to_bill.expired_at > now:
        to_bill.expired_at = to_bill.expired_at + delta
    else:
        to_bill.expired_at = now + delta

    to_bill.transferred += transferred + 1

    await renew_cdk(to_bill.cdk, to_bill.expired_at)
    to_bill.save()

    Transaction.create(
        from_platform=from_bill.platform,
        from_order_id=_from,
        to_platform=to_bill.platform,
        to_order_id=to,
        transfered_at=now,
        daysdelta=delta.days,
        new_expired_at=to_bill.expired_at,
        why="transfer/other_order",
    )

    logger.success(
        f"order transferred, _from: {_from}, to: {to}, delta: {delta}, new_expired_at: {to_bill.expired_at}"
    )
    return {"ec": 200, "msg": "Success"}


async def get_reward(_from: str, to_bill):
    reward = Reward.get_or_none(Reward.reward_key == _from)
    if not reward:
        return None

    now = datetime.now()
    if reward.expired_at < now:
        logger.error(f"reward expired, _from: {_from}")
        return {
            "ec": 403,
            "msg": "Reward expired",
        }

    if reward.start_at > now:
        logger.error(f"reward not started, _from: {_from}")
        return {
            "ec": 403,
            "msg": "Reward not started",
        }

    if reward.remaining <= 0:
        logger.error(f"reward remaining <= 0, _from: {_from}")
        return {
            "ec": 403,
            "msg": "Reward remaining <= 0",
        }

    if to_bill.expired_at < now:
        logger.error(f"order expired, to: {to_bill.order_id}")
        return {
            "ec": 403,
            "msg": "Order expired",
        }

    if (
        to_bill.created_at < reward.order_created_after
        or to_bill.created_at > reward.order_created_before
    ):
        logger.error(f"The order creation time does not match, to: {to_bill.order_id}")
        return {
            "ec": 403,
            "msg": "Not meeting award requirements",
        }

    delta = timedelta(days=reward.valid_days)
    new_expired_at = to_bill.expired_at + delta

    _, created = Transaction.get_or_create(
        from_platform="reward",
        from_order_id=_from,
        to_platform=to_bill.platform,
        to_order_id=to_bill.order_id,
        defaults={
            "transfered_at": now,
            "daysdelta": delta.days,
            "new_expired_at": new_expired_at,
            "why": "transfer/reward",
        },
    )
    if not created:
        logger.error(f"reward already given, _from: {_from}, to: {to_bill.order_id}")
        return {"ec": 403, "msg": "Reward already given"}

    to_bill.expired_at = new_expired_at
    await renew_cdk(to_bill.cdk, to_bill.expired_at)
    to_bill.save()

    reward.remaining -= 1
    reward.received_count += 1
    reward.save()

    logger.success(
        f"reward transferred, _from: {_from}, to: {to_bill.order_id}, delta: {delta}, new_expired_at: {to_bill.expired_at}"
    )
    return {"ec": 200, "msg": "Success"}
