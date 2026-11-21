from fastapi import APIRouter
from fastapi.responses import Response

from app.agent import agent
from app.services.report_service import build_report

router = APIRouter(prefix="/api", tags=["report"])


@router.get("/report")
def report():
    """把当前会话整理成 Markdown 文件，交给浏览器下载。"""
    # 为什么用 get_state：报告只回顾已经发生过的对话，checkpointer 里存着完整消息，
    # 直接读既不用再花一次模型调用，也不会改动会话状态。
    # thread_id 必须和聊天用的那个一致，否则读到的是另一个会话的记录。
    config = {"configurable": {"thread_id": "web-demo"}}
    state = agent.get_state(config)
    # 从没聊过的会话 values 是空字典，取不到 messages 就当空历史处理。
    messages = (state.values or {}).get("messages", [])

    md = build_report(messages)
    # Content-Disposition 带 attachment，浏览器才会把响应当成文件下载而不是显示在页面上。
    return Response(
        content=md,
        media_type="text/markdown",
        headers={"Content-Disposition": 'attachment; filename="interview-report.md"'},
    )
