from fastapi import APIRouter
from schemas.chat import (
    ChatRequest,
    ChatResponse 
)

router = APIRouter()

@router.post("/chat",
 response_model=ChatResponse)
def chat(
    question: ChatRequest
):
    return ChatResponse(
        question=question.question,
        answer= "test"
    )