from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
        description="The question to ask the AI model.",
        examples=["找2023年金额最大的合同"],
    )
    thread_id: str | None = Field(
        default=None,
        description="LangGraph checkpoint thread id。不传则自动生成。",
    )


class AgentStep(BaseModel):
    tool: str
    args: dict[str, Any]
    result: Any


class ChatResponse(BaseModel):
    question: str
    steps: list[AgentStep]
    answer: str
    route: str | None = None
    thread_id: str | None = None
