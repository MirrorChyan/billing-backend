import os

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from aiohttp import ClientSession
import asyncio
import time
import hashlib
import json

app = FastAPI()


AFDIAN_PRICING_URL = "https://afdian.com/a/misteo?tab=shop"
AFDIAN_QUERY_API = "https://afdian.com/api/open/query-order"

AFDIAN_USER_ID = os.getenv("AFDIAN_USER_ID")
AFDIAN_API_TOKEN = os.getenv("AFDIAN_API_TOKEN")
print(f"AFDIAN_USER_ID: {AFDIAN_USER_ID}, AFDIAN_API_TOKEN: {AFDIAN_API_TOKEN}")

if not AFDIAN_USER_ID or not AFDIAN_API_TOKEN:
    raise Exception("AFDIAN_USER_ID or AFDIAN_API_TOKEN is not set")


@app.get("/")
async def root():
    return "Hello, MaaFW!"


@app.get("/pricing")
async def pricing():
    return RedirectResponse(AFDIAN_PRICING_URL)


@app.post("/api/order/afdian")
async def api_order_afdian(webhook_body: dict):
    print(f"webhook_body: {webhook_body}")

    out_trade_no = webhook_body.get("data", {}).get("order", {}).get("out_trade_no")
    print(f"out_trade_no: {out_trade_no}")
    if not out_trade_no:
        return {"ec": 400, "em": "Invalid out_trade_no"}

    query_params = json.dumps({"out_trade_no": out_trade_no})
    query_ts = int(time.time())

    sign = (
        AFDIAN_API_TOKEN
        + "params"
        + query_params
        + "ts"
        + str(query_ts)
        + "user_id"
        + AFDIAN_USER_ID
    )
    sign = hashlib.md5(sign.encode()).hexdigest()

    query_body = {
        "user_id": AFDIAN_USER_ID,
        "params": query_params,
        "ts": query_ts,
        "sign": sign,
    }

    async with ClientSession() as session:
        async with session.post(AFDIAN_QUERY_API, json=query_body) as response:
            response = await response.json()
            print(f"response: {response}")

    return {"ec": 200, "em": ""}
