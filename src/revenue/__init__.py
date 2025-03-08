from loguru import logger
from fastapi import APIRouter, Request
from datetime import datetime
from collections import defaultdict
from time import time

from src.database import Bill, CheckIn, IgnoreCheckIn, Plan
from src.cdk.validate_token import validate_token

router = APIRouter()

PLANS = {plan.plan_id: plan.title for plan in Plan.select(Plan.plan_id, Plan.title)}
data_cache = {}


@router.get("/revenue")
async def query_revenue(rid: str, request: Request):
    logger.debug(f"rid: {rid}")

    if not rid:
        logger.error("rid is required")
        return {"ec": 400, "msg": "rid is required"}

    token = request.headers.get("Authorization")
    if not token:
        logger.error("Authorization is required")
        return {"ec": 401, "msg": "Authorization is required"}

    if not await validate_token(rid, token):
        logger.error("Unauthorized")
        return {"ec": 401, "msg": "Unauthorized"}

    if IgnoreCheckIn.get_or_none(application=rid):
        logger.warning(f"ignore check_in, application: {rid}")
        return {"ec": 404, "msg": "Not Found"}

    global data_cache
    if rid in data_cache:
        data, last_update = data_cache[rid]
        if time() - last_update < 60:
            logger.debug(f"cache hit, rid: {rid}")
            return {"ec": 200, "data": data}

    data = query_db(rid)
    data_cache[rid] = (data, time())

    return {"ec": 200, "data": data}


def query_db(rid: str):
    logger.debug(f"query_db, rid: {rid}")

    now = datetime.now()
    checkins = (
        CheckIn.select(CheckIn.cdk, CheckIn.activated_at, CheckIn.user_agent)
        .where(
            CheckIn.application == rid,
            CheckIn.activated_at > datetime(now.year, now.month, 1),
        )
        .order_by(CheckIn.activated_at)
    )

    bills = Bill.select(
        Bill.plan_id, Bill.created_at, Bill.buy_count, Bill.actually_paid, Bill.cdk
    ).where(
        Bill.cdk << [checkin.cdk for checkin in checkins],
    )

    bill_dict = defaultdict(list)
    for bill in bills:
        bill_dict[bill.cdk].append(bill)

    data = []
    for checkin in checkins:
        cur_bills = bill_dict.get(checkin.cdk, [])
        if not cur_bills:
            continue

        for b in cur_bills:
            data.append(
                {
                    "activated_at": checkin.activated_at,
                    "application": rid,
                    "user_agent": checkin.user_agent,
                    "plan": PLANS[b.plan_id],
                    "buy_count": b.buy_count,
                    "amount": b.actually_paid,
                }
            )

    logger.success(f"query_db success, rid: {rid}, len(data): {len(data)}")
    return data
