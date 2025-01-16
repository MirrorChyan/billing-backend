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
    res_id = body.get("res_id", "")
    if not cdk or not res_id:
        logger.error(f"no cdk or res_id field")
        return {"ec": 400, "em": "no cdk or res_id field"}

    now = datetime.now()

    module = body.get("module", "") 
    user_agent = body.get("user_agent", "")

    try:
        CheckIn.create(
            cdk=cdk,
            activated_at=now,
            application=res_id,
            module=module,
            user_agent=user_agent
        )

    except Exception as e:
        logger.error(f"check_in failed, cdk: {cdk}, res_id: {res_id}")
        return {"ec": 403, "em": f"check_in failed, cdk: {cdk}, res_id: {res_id}"}

    return {"ec": 200, "em": "OK"}
