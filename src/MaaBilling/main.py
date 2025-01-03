import os

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI()


PRICING_URL = "https://afdian.com/a/misteo?tab=shop"


@app.get("/pricing")
async def pricing():
    return RedirectResponse(PRICING_URL)


@app.get("/order/afdian")
async def afdian():
    return {"ec": 200, "em": ""}
