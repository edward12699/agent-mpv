import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_agent_service
from app.api.schemas.chat import ChatRequest, ChatResponse
from app.services.agent_service import AgentService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def chat(
    request: ChatRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> ChatResponse:
    try:
        result = await service.chat(request.question)
        return ChatResponse.model_validate(result)
    except TimeoutError as exc:
        logger.warning("Agent 执行超时，question=%s", request.question)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Agent 响应超时，请稍后重试",
        ) from exc
    except Exception as exc:
        logger.exception("Agent 执行失败，question=%s", request.question)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent 执行失败，请稍后重试",
        ) from exc
