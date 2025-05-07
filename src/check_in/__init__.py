from loguru import logger
from fastapi import APIRouter
from datetime import datetime

from src.config import settings
from src.database import CheckIn, IgnoreCheckIn


router = APIRouter()


@router.post("/check_in/" + settings.check_in_secret)
async def check_in(body: dict):
    # logger.debug(f"body: {body}")

    now = datetime.now()

    ret = True
    if "list" in body:
        for item in body["list"]:
            ret &= check_in_single(item, now)

    else:
        ret = check_in_single(body, now)

    if not ret:
        return {"ec": 500, "em": f"some failed to checkin, body: {body}"}

    return {"ec": 200, "em": "OK"}


def check_in_single(item, now) -> bool:
    cdk = item.get("cdk", "")
    application = item.get("application", "")
    if not cdk or not application:
        logger.error(f"no cdk or application field")
        return False

    module = item.get("module", "")
    user_agent = item.get("user_agent", "")

    if application and IgnoreCheckIn.get_or_none(application=application):
        logger.warning(f"ignore check_in, application: {application}")
        return True
    
    if module and IgnoreCheckIn.get_or_none(module=module):
        logger.warning(f"ignore check_in, module: {module}")
        return True
    
    if user_agent and IgnoreCheckIn.get_or_none(user_agent=user_agent):
        logger.warning(f"ignore check_in, user_agent: {user_agent}")
        return True

    try:
        checkin, created = CheckIn.get_or_create(
            cdk=cdk,
            defaults={
                "activated_at": now,
                "application": application,
                "module": module,
                "user_agent": user_agent,
            },
        )
    except Exception as e:
        logger.error(
            f"check_in failed, cdk: {cdk}, application: {application}, error: {e}"
        )
        return False

    if created:
        logger.success(
            f"check_in success, cdk: {cdk}, application: {application}, module: {module}, user_agent: {user_agent}"
        )

    return True
