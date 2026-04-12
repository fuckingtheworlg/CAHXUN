from __future__ import annotations

from __future__ import annotations

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # MySQL (read-only)
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "readonly_user"
    db_password: str = ""
    db_name: str = "campus_wall"
    db_table_name: str = "posts"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # DeepSeek LLM
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # WeChat
    wechat_appid: str = ""
    wechat_secret: str = ""

    # Rate limiting
    rate_limit_per_minute: int = 5

    # Admin
    admin_username: str = "admin"
    admin_password: str = "changeme"
    admin_jwt_secret: str = "please-change-this-secret-key"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
