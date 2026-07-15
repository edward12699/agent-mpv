from fastapi import APIRouter,Depends, HTTPException, status
from app.api.schemas.chat import (
    ChatRequest,
    ChatResponse 
)
import logging
from typing import Annotated
from app.agent_langchain import Agent
from app.api.dependencies import get_agent
from app.api.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

# ???
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent",
    #  ???
    tags=["Agent"],
)

@router.post("/chat",
 response_model=ChatResponse,
 status_code=status.HTTP_200_OK
 )
def chat(
    request: ChatRequest,
    # ???
    agent: Annotated[Agent, Depends(get_agent)],
) -> ChatResponse:
    try:
        result = agent.run(request.question)
        # return ChatResponse.model_validate(result)
        return result
    except Exception as exc:
        logger.exception(
            "Agent 执行失败，question=%s",
            request.question,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent 执行失败",
        ) from exc