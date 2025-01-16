from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database: str
    database_host: str
    database_port: int
    database_user: str
    database_passwd: str

    afdian_query_order_api: str
    afdian_user_id: str
    afdian_api_token: str
    afdian_webhook_secret: str
    afdian_test_out_trade_no: str

    cdk_acquire_api: str

    check_in_secret: str

    class Config:
        env_file = ".env"


settings = Settings()
