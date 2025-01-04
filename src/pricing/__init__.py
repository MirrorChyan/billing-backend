from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


AFDIAN_PRICING_URL = "https://afdian.com/a/misteo?tab=shop"


@router.get("/pricing")
async def pricing():
    return RedirectResponse(AFDIAN_PRICING_URL)
