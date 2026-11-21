from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """前端发来的聊天请求"""
    message: str = Field(description="用户说的话")


class ChatResponse(BaseModel):
    """后端返回的聊天结果"""
    reply: str = Field(description="面试官的回复")
    question: str = Field(default="", description="本轮新出的题目，没有就空字符串")
    # 为什么必须在这里声明：FastAPI 会按 response_model 裁剪字段，
    # 少了这一行，chat_once 算出的 scored 会被静默丢掉，前端永远弹不出评分卡。
    scored: bool = Field(default=False, description="本轮是否真的给学生打了分，前端据此决定是否弹评分卡")


class ScoreRequest(BaseModel):
    """前端发来的评分请求"""
    question: str = Field(description="题目")
    answer: str = Field(description="学生的回答")


class ScoreCard(BaseModel):
    """评分卡：结构化输出，前端按字段渲染"""
    score: int = Field(description="分数，0-10 的整数")
    pass_flag: bool = Field(description="是否通过本轮，6 分及以上为 true")
    strengths: list[str] = Field(description="答得好的地方，1-3 条")
    weaknesses: list[str] = Field(description="漏掉的要点，1-3 条")
    suggestion: str = Field(description="一句话改进建议")
