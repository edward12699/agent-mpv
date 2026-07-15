from pydantic import BaseModel,Field
from typing import Any


class ChatRequest(BaseModel):

    question:str = Field(
        min_length = 1,
        max_length=2000,
        description="The question to ask the AI model.",
        examples=["找2023年金额最大的合同"]
    )


class AgentStep(BaseModel):
    tool: str
    args: dict[str, Any]
    result: Any

class ChatResponse(BaseModel):

    question:str
    steps:list[AgentStep]
    answer:str