from typing import Any

from app.agent_langchain import Agent


class AgentService:
    def __init__(self, agent: Agent):
        self.agent = agent

    async def chat(self, question: str) -> dict[str, Any]:
        return await self.agent.run(question.strip())
