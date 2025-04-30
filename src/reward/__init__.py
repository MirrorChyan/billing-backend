from fastapi import APIRouter

from src.database import Reward

router = APIRouter()


@router.get("/reward")
def query_reward(reward_key: str):
    reward = Reward.get_or_none(Reward.reward_key == reward_key)
    if not reward:
        return {"ec": 404, "msg": "Reward not found"}

    return {
        "ec": 200,
        "msg": "Success",
        "data": {
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
