from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    backend_base_url: str = Field(default="http://backend:8000", alias="BACKEND_BASE_URL")
    backend_api_key: str = Field(default="dev-backend-key", alias="BACKEND_API_KEY")


settings = BotSettings.model_validate({})
