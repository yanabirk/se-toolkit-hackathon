from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = Field(default="study-planner-backend", alias="NAME")
    debug: bool = Field(default=True, alias="DEBUG")
    address: str = Field(default="0.0.0.0", alias="ADDRESS")
    port: int = Field(default=8000, alias="PORT")
    reload: bool = Field(default=False, alias="RELOAD")

    cors_origins_raw: str = Field(default='["*"]', alias="CORS_ORIGINS")
    api_key: str = Field(default="dev-backend-key", alias="LMS_API_KEY")

    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="study_planner", alias="DB_NAME")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: str = Field(default="postgres", alias="DB_PASSWORD")

    storage_root: str = Field(default="/app/storage", alias="STORAGE_ROOT")

    llm_base_url: str = Field(default="http://localhost:8080/v1", alias="LLM_API_BASE_URL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="qwen", alias="LLM_API_MODEL")
    llm_timeout_seconds: float = Field(default=120.0, alias="LLM_TIMEOUT_SECONDS")
    llm_provider: str = Field(default="qwen", alias="LLM_PROVIDER")

    max_material_chars: int = Field(default=120_000, alias="MAX_MATERIAL_CHARS")

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized == "release":
                return False
            if normalized == "debug":
                return True
        return value

    @property
    def cors_origins(self) -> list[str]:
        raw = self.cors_origins_raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            import json

            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                pass
        return [part.strip() for part in raw.split(",") if part.strip()]


settings = Settings.model_validate({})
