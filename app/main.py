from fastapi import FastAPI

from app.routers import pages, chat, score, stream, report

app = FastAPI(title="AI 技术面试官")

app.include_router(pages.router)
app.include_router(chat.router)
app.include_router(score.router)
app.include_router(stream.router)
app.include_router(report.router)