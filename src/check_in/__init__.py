from loguru import logger
from fastapi import APIRouter
from datetime import datetime

from src.database import CheckIn


router = APIRouter()


@router.post("/check_in")
async def check_in(body: dict):
    logger.debug(f"body: {body}")
    cdk = body.get("cdk", "")
    app = body.get("app", "")
    if not cdk or not app:
        logger.error(f"no cdk or app field")
        return {"ec": 400, "em": "no cdk or app field"}

    now = datetime.now()

    try:
        CheckIn.create(
            cdk=cdk,
            activated_at=now,
            application=app,
        )

    except Exception as e:
        logger.error(f"checkin failed, cdk: {cdk}, app: {app}")
        return {"ec": 403, "em": f"checkin failed, cdk: {cdk}, app: {app}"}

    return {"ec": 200, "em": "OK"}
