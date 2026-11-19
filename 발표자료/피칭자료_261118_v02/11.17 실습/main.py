from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from orchestrator import handle_message

app = FastAPI()


@app.get("/")
def index():
    # 채팅 UI 페이지 제공
    return FileResponse("static/index.html")


class ChatRequest(BaseModel):
    message: str


class Step(BaseModel):
    agent: str
    action: str
    detail: dict


class ChatResponse(BaseModel):
    reply: str
    steps: list[Step]


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # 오케스트레이터에게 메시지를 넘기고 최종 응답 + 에이전트 호출 기록을 받아 반환
    result = handle_message(request.message)
    return ChatResponse(**result)
