from fastapi import FastAPI
from src.order.afdian.webhook import router as order_afdian_webhook_router
from src.order.afdian.query_order import router as order_afdian_query_order_router
from scr.check_in import router as check_in_router

app = FastAPI()

app.include_router(order_afdian_webhook_router)
app.include_router(order_afdian_query_order_router)
app.include_router(check_in_router)
