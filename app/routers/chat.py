from fastapi import APIRouter
from app.schemas import ChatRequest, ChatResponse
from app.agent import chat_once

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = chat_once(req.message)
    return ChatResponse(
        reply=result["reply"],
        question=result["question"],
        scored=result["scored"],
    )