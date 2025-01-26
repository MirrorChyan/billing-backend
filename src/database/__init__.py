from loguru import logger
from peewee import (
    MySQLDatabase,
    CompositeKey,
    Model,
    CharField,
    TextField,
    DateTimeField,
    IntegerField,
    BooleanField,
)
from playhouse.shortcuts import ReconnectMixin

from src.config import settings


class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    pass


db = ReconnectMySQLDatabase(
    database=settings.database,
    host=settings.database_host,
    port=settings.database_port,
    user=settings.database_user,
    password=settings.database_passwd,
    charset="utf8mb4",
)

if not db.connect():
    logger.error("Database connection failed")
    raise ValueError("Database connection failed")


class Plan(Model):
    platform = CharField()
    plan_id = CharField()

    title = TextField()
    valid_days = IntegerField()
    applications = TextField()
    modules = TextField()
    cdk_number = IntegerField()

    class Meta:
        database = db
        table_name = "plan"
        primary_key = CompositeKey("platform", "plan_id")


class Bill(Model):
    # from platform

    platform = CharField()
    order_id = CharField()
    custom_order_id = CharField()

    plan_id = CharField()
    user_id = CharField()
    created_at = DateTimeField()
    buy_count = IntegerField()
    actually_paid = CharField()
    original_price = CharField()
    raw_data = TextField()

    # from plan
    expired_at = DateTimeField()

    # from backend
    cdk = CharField()

    class Meta:
        database = db
        table_name = "bill"
        primary_key = CompositeKey("platform", "order_id")


class CheckIn(Model):
    cdk = CharField()
    activated_at = DateTimeField()
    application = CharField()
    module = CharField()
    user_agent = CharField()
    renew = BooleanField(default=False)

    class Meta:
        database = db
        table_name = "checkin"


Plan.create_table()
Bill.create_table()
CheckIn.create_table()
