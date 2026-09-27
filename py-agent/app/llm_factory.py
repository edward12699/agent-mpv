from langchain_openai import ChatOpenAI

from app.core.config import Settings


def create_default_chat_model(settings: Settings) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.agent_model,
        api_key=settings.api_key,
        base_url=settings.base_url,
        timeout=settings.llm_request_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )
