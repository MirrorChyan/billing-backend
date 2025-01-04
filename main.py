import os

from fastapi import FastAPI
from src.index import router as index_router
from src.order.afdian.webhook import router as order_afdian_webhook_router

app = FastAPI()

app.include_router(index_router)
app.include_router(order_afdian_webhook_router)
