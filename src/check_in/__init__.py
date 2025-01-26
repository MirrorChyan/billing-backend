from loguru import logger
from fastapi import APIRouter
from datetime import datetime

from src.config import settings
from src.database import CheckIn


router = APIRouter()


@router.post("/check_in/" + settings.check_in_secret)
async def check_in(body: dict):
    logger.debug(f"body: {body}")
    cdk = body.get("cdk", "")
    application = body.get("application", "")
    if not cdk or not application:
        logger.error(f"no cdk or application field")
        return {"ec": 400, "em": "no cdk or application field"}

    now = datetime.now()

    module = body.get("module", "") 
    user_agent = body.get("user_agent", "")

    try:
        CheckIn.create(
            cdk=cdk,
            activated_at=now,
            application=application,
            module=module,
            user_agent=user_agent
        )

    except Exception as e:
        logger.error(f"check_in failed, cdk: {cdk}, application: {application}, error: {e}")
        return {"ec": 500, "em": f"check_in failed, cdk: {cdk}, application: {application}, error: {e}"}

    return {"ec": 200, "em": "OK"}
