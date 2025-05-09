from fastapi import FastAPI
from src.order.query_order import router as order_query_router
from src.order.transfer_order import router as order_transfer_router
from src.order.afdian.webhook import router as order_afdian_webhook_router
from src.order.yimapay.create_order import router as order_yimapay_create_order_router
from src.order.yimapay.webhook import router as order_yimapay_webhook_router
from src.health_check import router as health_check_router
from src.check_in import router as check_in_router
from src.revenue import router as revenue_router
from src.reward import router as reward_router

app = FastAPI()

app.include_router(order_query_router)
app.include_router(order_afdian_webhook_router)
app.include_router(order_transfer_router)
app.include_router(order_yimapay_create_order_router)
app.include_router(order_yimapay_webhook_router)
app.include_router(check_in_router)
app.include_router(revenue_router)
app.include_router(health_check_router)
app.include_router(reward_router)
