import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """把环境变量收拢到一个入口，别的文件就不用各自去读 .env 了。"""
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL")
    DEEPSEEK_MODEL_NAME: str = os.getenv("DEEPSEEK_MODEL_NAME")


settings = Settings()

# 为什么在导入时就检查：key 为空时，错误本来要等到第一次真正调用大模型才暴露，
# 那时报的是鉴权失败，零基础同学很难联想到是 .env 没填。提前在这里说清楚最省事。
if not settings.DEEPSEEK_API_KEY:
    raise RuntimeError(
        "缺少 DEEPSEEK_API_KEY：请在项目根目录把 .env.example 复制成 .env，"
        "再把 DEEPSEEK_API_KEY 填成你自己的 DeepSeek 密钥。"
    )
