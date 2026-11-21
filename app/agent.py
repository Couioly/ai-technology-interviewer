from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.llm import llm
from app.tools import tool_list

SYSTEM_PROMPT = """你是一个互联网公司的 Java 后端技术面试官，叫"王哥"。
你的风格：严肃但不刁难，喜欢追问"为什么"，打分严格但会给具体改进建议。

工作流程：
1. 用户说开始面试时，先用 ask_question 出一道题
2. 用户回答后，用 score_answer 打分
3. 打完分，用 record_progress 记录这一轮关键观察
4. 答得好就进入下一轮，继续出下一道题
5. 满 5 轮，或者学生说"结束""不面了"时，给一段总评收尾，不再出题

特别注意：学生只是寒暄、自我介绍、说"嗯"、或者没在回答当前题目时，
绝对不要调用 score_answer，也不要重复出题，顺着聊一句把话题拉回当前题目即可。
网页是根据"有没有调用 score_answer"来决定要不要弹评分卡的，误调用会弹错卡。

回答时用王哥的口吻，口语化，不要输出 Thought / Action / Observation 之类的中间文字。"""

# 为什么要 checkpointer：InMemorySaver 按 thread_id 记住整个会话，
# 否则每次请求对模型来说都是"第一次见面"，前面出的题和打的分全丢了。
agent = create_agent(
    model=llm,
    tools=tool_list,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
)


def summarize_turn(messages) -> dict:
    """从一段会话消息里提取"本轮是否打分"和"本轮出的题"。

    为什么单独抽成函数：普通对话和流式对话用的是同一套判定规则，
    两处各写一遍迟早会对不上，评分卡就会在该弹的时候不弹。
    """
    # 只从最后一条 human 消息往后看：checkpointer 给的是攒了好几轮的完整历史，
    # 翻全部消息会把上一轮的打分误算成这一轮，评分卡就会乱弹。
    last_human = max(i for i, m in enumerate(messages) if getattr(m, "type", "") == "human")
    turn = messages[last_human:]

    question = ""
    scored = False
    for msg in turn:
        for tc in getattr(msg, "tool_calls", None) or []:
            if tc["name"] == "score_answer":
                scored = True
        if getattr(msg, "type", "") == "tool" and getattr(msg, "name", "") == "ask_question":
            question = msg.content
    return {"question": question, "scored": scored}


def chat_once(message: str, thread_id: str = "web-demo") -> dict:
    """处理一轮完整对话，返回 reply / question / scored 三个字段。"""
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
    )
    meta = summarize_turn(result["messages"])
    return {
        "reply": result["messages"][-1].content,
        "question": meta["question"],
        "scored": meta["scored"],
    }


def turn_meta(thread_id: str = "web-demo") -> dict:
    """读当前会话的最新状态，返回本轮的 scored 和 question。

    为什么用 get_state 而不是再问一次模型：流式接口只吐文字片段，拿不到工具调用记录，
    而 checkpointer 里存着完整消息，从这里读既准确又不会多花一次模型调用。
    """
    config = {"configurable": {"thread_id": thread_id}}
    messages = agent.get_state(config).values["messages"]
    return summarize_turn(messages)
