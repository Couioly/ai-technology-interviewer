import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas import ChatRequest
from app.llm import llm
from app.agent import agent, turn_meta

router = APIRouter(prefix="/api", tags=["stream"])

# SSE 三要素：每行以 "data: " 开头、载荷是 JSON、行尾留一个空行。
# 少了空行浏览器会把多帧粘成一帧；中文不关 ensure_ascii 会变成反斜杠 u 开头的乱码。


@router.post("/chat_stream")
def chat_stream(req: ChatRequest):
    def generate():
        for chunk in llm.stream(req.message):
            if chunk.content:
                yield f"data: {json.dumps({'text': chunk.content}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/agent_stream")
def agent_stream(req: ChatRequest):
    def generate():
        # 为什么固定同一个 thread_id：checkpointer 靠它认人，
        # 换成随机会让每次请求都变成"新学生"，前面出的题和打的分全丢。
        config = {"configurable": {"thread_id": "web-demo"}}
        for chunk, metadata in agent.stream(
            {"messages": [{"role": "user", "content": req.message}]},
            config=config,
            stream_mode="messages",
        ):
            # 为什么按节点过滤：流式里除了面试官说的话，还会混进工具节点产生的文字片段，
            # 例如评分工具返回的"分数：X/10 评语：..."。只放行 model 节点，
            # 学生才不会在打字机里看到本该由评分卡展示的内部过程。
            if metadata.get("langgraph_node", "model") != "model":
                continue
            text = getattr(chunk, "content", "")
            if text:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"

        # 文字发完再补一帧判定结果：前端靠 scored 决定要不要弹评分卡。
        # 放在最后是为了不打断打字机效果，也不会多花一次模型调用。
        meta = turn_meta("web-demo")
        yield f"data: {json.dumps({'type': 'meta', 'scored': meta['scored'], 'question': meta['question']}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
