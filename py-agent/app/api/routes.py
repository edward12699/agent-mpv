from fastapi import APIRouter, Depends, HTTPException, status
from app.api.schemas.chat import (
    AgentStep,
    ChatRequest,
    ChatResponse,
)
import logging
from typing import Annotated
from app.agent_langchain import Agent
from app.api.dependencies import get_agent

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
async def chat(
    request: ChatRequest,
    # ???
    agent: Annotated[Agent, Depends(get_agent)],
) -> ChatResponse:
    try:
        result = await agent.run(request.question)
        return result

    # 这个要在前面，不然timeouteror也会被当成exception处理
    except TimeoutError as exc:
        logger.warning(
            "Agent 执行超时，question=%s",
            request.question,
        )

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Agent 响应超时，请稍后重试",
        ) from exc
    
    except Exception as exc:
        logger.exception(
            "Agent 执行失败，question=%s",
            request.question,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent 执行失败，请稍后重试",
        ) from exc