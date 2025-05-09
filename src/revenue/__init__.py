from loguru import logger
from fastapi import APIRouter, Request
from datetime import datetime
from collections import defaultdict
from time import time

from src.database import Bill, CheckIn, IgnoreCheckIn, Plan
from src.cdk.validate_token import validate_token
from src.config import settings

router = APIRouter()

cur_month_cache = {}
cur_month_ua_cache = {}
CACHE_EXPIRATION = 60  # seconds

past_month_cache = {}
past_month_ua_cache = {}

@router.get("/revenue")
async def query_revenue(rid: str, date: str, request: Request, is_ua: bool = False):
    logger.debug(f"rid: {rid}, date: {date}, is_ua: {is_ua}")

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

    if not is_ua and IgnoreCheckIn.get_or_none(application=rid):
        logger.warning(f"ignore check_in, application: {rid}")
        return {"ec": 404, "msg": "Not Found"}

    try:
        dt: datetime = datetime.strptime(date, "%Y%m")
    except ValueError:
        logger.error(f"Invalid date format: {date}")
        return {"ec": 400, "msg": "Invalid date format"}

    now = datetime.now()

    if (
        dt.year < 2025
        or dt.year > now.year
        or (dt.year == now.year and dt.month > now.month)
    ):
        logger.error(f"Invalid date: {date}")
        return {"ec": 400, "msg": "Invalid date"}

    if dt.year == now.year and dt.month == now.month:
        global cur_month_cache, cur_month_ua_cache
        # 现在月份的，可能会有新的数据进来，所以需要记录更新时间
        if is_ua:
            cache = cur_month_ua_cache
        else:
            cache = cur_month_cache

        if rid in cache:
            data, last_update = cache[rid]
            timediff = int(time() - last_update)
            if timediff < CACHE_EXPIRATION:
                logger.debug(
                    f"cur month cache hit, rid: {rid}, date: {date}, timediff: {timediff}"
                )
                return {"ec": 200, "data": data}

        data = query_db(rid, dt, is_ua)
        cache[rid] = (data, time())
        return {"ec": 200, "data": data}

    else:
        global past_month_cache, past_month_ua_cache
        # 以前月份的，不会再有变化了，获取一次就行，不用记录update时间

        if is_ua:
            cache = past_month_ua_cache
        else:
            cache = past_month_cache

        if rid not in cache:
            cache[rid] = {}

        if date in cache[rid]:
            data = cache[rid][date]
            logger.debug(f"past month cache hit, rid: {rid}, date: {date}")
        else:
            data = query_db(rid, dt, is_ua)
            cache[rid][date] = data

        return {"ec": 200, "data": data}


def query_db(rid: str, date: datetime, is_ua: bool):
    logger.debug(f"query_db, rid: {rid}, date: {date}, is_ua: {is_ua}")

    plans = {plan.plan_id: plan.title for plan in Plan.select(Plan.plan_id, Plan.title)}

    cur_month = datetime(date.year, date.month, 1)

    if date.month == 12:
        next_month = datetime(date.year + 1, 1, 1)
    else:
        next_month = datetime(date.year, date.month + 1, 1)

    if rid == settings.revenue_all_secret:
        checkins = (
            CheckIn.select(
                CheckIn.cdk,
                CheckIn.activated_at,
                CheckIn.application,
                CheckIn.user_agent,
            )
            .where(
                CheckIn.activated_at.between(cur_month, next_month),
            )
            .order_by(CheckIn.activated_at)
        )
    elif not is_ua:
        checkins = (
            CheckIn.select(
                CheckIn.cdk,
                CheckIn.activated_at,
                CheckIn.application,
                CheckIn.user_agent,
            )
            .where(
                CheckIn.application == rid,
                CheckIn.activated_at.between(cur_month, next_month),
            )
            .order_by(CheckIn.activated_at)
        )
    else: # is_ua
        checkins = (
            CheckIn.select(
                CheckIn.cdk,
                CheckIn.activated_at,
                CheckIn.application,
                CheckIn.user_agent,
            )
            .where(
                CheckIn.user_agent == rid,
                CheckIn.activated_at.between(cur_month, next_month),
            )
            .order_by(CheckIn.activated_at)
        )

    bills = Bill.select(
        Bill.platform, Bill.plan_id, Bill.created_at, Bill.buy_count, Bill.actually_paid, Bill.cdk
    ).where(
        Bill.cdk << [checkin.cdk for checkin in checkins],
        Bill.transferred >= 0,
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
            app = checkin.application
            ua = checkin.user_agent if checkin.user_agent else f"{app}-NoUA"
            data.append(
                {
                    "platform": b.platform,
                    "activated_at": checkin.activated_at,
                    "application": app,
                    "user_agent": ua,
                    "plan": plans[b.plan_id],
                    "buy_count": b.buy_count,
                    "amount": b.actually_paid,
                }
            )

    logger.success(
        f"query_db success, rid: {rid}, date: {date}, is_ua: {is_ua}, len(data): {len(data)}"
    )
    return data
