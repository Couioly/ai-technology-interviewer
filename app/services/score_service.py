from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.llm import llm
from app.schemas import ScoreCard

parser = PydanticOutputParser(pydantic_object=ScoreCard)

prompt = ChatPromptTemplate.from_template("""
你是严格但公正的 Java 技术面试官。
评价下面这个回答，严格按要求输出 JSON，不要任何多余解释、不要代码块包裹。

题目：{question}
学生回答：{answer}

{format_instructions}
""")

chain = prompt | llm | parser


def make_score_card(question: str, answer: str) -> ScoreCard:
    """对一道题的回答打分，返回结构化评分卡"""
    return chain.invoke({
        "question": question,
        "answer": answer,
        "format_instructions": parser.get_format_instructions()
    })