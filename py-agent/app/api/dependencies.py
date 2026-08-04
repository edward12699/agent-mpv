from functools import lru_cache

from app.agent_langchain import Agent
from app.services.agent_service import AgentService


@lru_cache
def get_agent() -> Agent:
    return Agent()


@lru_cache
def get_agent_service() -> AgentService:
    return AgentService(agent=get_agent())
