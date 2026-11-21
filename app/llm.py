from langchain_openai import ChatOpenAI
from app.config import settings

llm = ChatOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    model=settings.DEEPSEEK_MODEL_NAME,
    temperature=0.7
)