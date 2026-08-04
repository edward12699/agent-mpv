from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Contract Agent API"
    app_version: str = "0.1.0"
    agent_debug: bool = Field(default=False, alias="PY_AGENT_DEBUG")
    dashscope_api_key: str | None = Field(default=None, alias="DASHSCOPE_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    agent_model: str = Field(default="qwen-plus", alias="PY_AGENT_MODEL")
    llm_request_timeout_seconds: float = Field(
        default=30, alias="LLM_REQUEST_TIMEOUT_SECONDS", gt=0
    )
    llm_max_retries: int = Field(default=1, alias="LLM_MAX_RETRIES", ge=0)
    agent_timeout_seconds: float = Field(
        default=60, alias="AGENT_TIMEOUT_SECONDS", gt=0
    )
    allowed_origins: str = Field(
        default="http://localhost:3002", alias="ALLOWED_ORIGINS"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def debug(self) -> bool:
        return self.agent_debug

    @property
    def api_key(self) -> str:
        value = self.dashscope_api_key or self.openai_api_key
        if not value:
            raise RuntimeError("请设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY")
        return value

    @property
    def base_url(self) -> str | None:
        if self.openai_base_url:
            return self.openai_base_url
        if self.dashscope_api_key:
            return "https://dashscope.aliyuncs.com/compatible-mode/v1"
        return None

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
