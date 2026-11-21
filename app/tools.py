import random
from langchain.tools import tool
from app.llm import llm

QUESTION_BANK = {
    "java": [
        "HashMap 和 Hashtable 有什么区别？",
        "String、StringBuilder、StringBuffer 区别？",
        "讲一下 JVM 内存区域划分",
    ],
    "python": [
        "列表和元组的区别？",
        "什么是装饰器？写一个最简单的",
        "GIL 是什么？",
    ],
    "frontend": [
        "let、var、const 区别？",
        "什么是闭包？",
        "浏览器输入 URL 到页面展示发生了什么？",
    ],
}


@tool
def ask_question(topic: str) -> str:
    """从题库里随机抽一道技术面试题，返回题目原文。

    参数：
        topic：面试方向，只能是 java、python、frontend 三者之一。

    什么时候调用：学生说"开始面试""我准备好了"或报出技术方向、需要出一道题时调用。
    学生正在作答、或只是寒暄自我介绍时不要调用，否则会重复出题。
    """
    if topic not in QUESTION_BANK:
        return "目前只支持 java、python、frontend"
    return random.choice(QUESTION_BANK[topic])


@tool
def score_answer(question: str, answer: str) -> str:
    """给学生刚答完的这道题打分，返回自然语言版的分数和评语。

    参数：
        question：上一轮用 ask_question 出的题目原文。
        answer：学生这一轮输入的回答内容。

    什么时候调用：只有在学生确实针对当前题目作答之后才调用。
    寒暄、自我介绍、只回一个"嗯"、或者答非所问时绝对不要调用，
    因为网页会把"调用过这个工具"当成弹评分卡的信号。
    """
    prompt = f"""
你是一个严格但公正的技术面试官。
题目：{question}
学生回答：{answer}

请你：
1. 打一个 0-10 的分数
2. 用 100 字以内指出哪里答得好、哪里漏了要点
3. 严格按下面两行输出，不要加别的内容：
   分数：X/10
   评语：用 100 字以内写出答得好的点和漏掉的要点
"""
    # 为什么给这次调用单独把 temperature 绑成 0：打分要稳定可复现，
    # 同一份答案不该因为模型"发挥"而忽高忽低。bind 只改这一次调用的参数，
    # 不会动到 app/llm.py 里那个供聊天用的单例，符合"模型只来自 llm"的约定。
    return llm.bind(temperature=0).invoke(prompt).content


@tool
def record_progress(round_num: int, note: str) -> str:
    """把这一轮的面试表现打到终端日志里，方便课后回看全过程。

    参数：
        round_num：当前是第几轮，从 1 开始数。
        note：这一轮值得记下的观察，例如"线程安全那块没答上来"。

    什么时候调用：每次 score_answer 打完分之后紧跟一次，不要提前也不要重复记录。
    """
    print(f"[进度记录] 第{round_num}轮：{note}")
    return f"已记录第 {round_num} 轮表现。"


# create_agent 只认这个列表，新增工具时记得一并加进来，否则大模型看不到它。
tool_list = [ask_question, score_answer, record_progress]
