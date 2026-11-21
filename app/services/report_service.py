"""面试报告生成服务：只回顾已经发生的对话，不调用大模型。"""

import re
from datetime import datetime

# 评分工具返回的文字形如"分数：8/10"，冒号可能是全角或半角，中间也可能带空格。
# 用正则只取数字，模型多写一句评语也不会影响解析。
SCORE_PATTERN = re.compile(r"分数[：:]\s*(\d+)\s*/\s*10")


def _field(msg, key, default=""):
    """读取一条消息里的某个字段，消息对象和字典都能处理。

    为什么不直接写 msg.content：历史消息偶尔会混进普通字典，
    点属性会抛异常；报告是"读已有记录"，宁可字段留空也不能让下载接口报错。
    """
    if isinstance(msg, dict):
        return msg.get(key, default)
    return getattr(msg, key, default)


def _text_of(msg) -> str:
    """把一条消息的正文压成干净的一行文本。"""
    content = _field(msg, "content", "")
    if content is None:
        return ""
    # 题目和回答里可能带换行，塞进 Markdown 列表项会把格式撑断，统一压成一行。
    return str(content).replace("\r", " ").replace("\n", " ").strip()


def _parse_score(content):
    """从评分工具的文字里取出 0-10 的分数，取不到就返回 None。"""
    match = SCORE_PATTERN.search(str(content or ""))
    if not match:
        return None
    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return None


def build_report(messages: list) -> str:
    """把 agent 的完整会话历史拼成一份 Markdown 报告。

    参数 messages 是 agent.invoke 返回的 result["messages"]，含全部历史。
    为什么按 ask_question 切轮：checkpointer 给的是攒了好几轮的完整历史，
    一条 human 可能是"我准备好了"这种开场白，也可能是"嗯"这种寒暄，
    按 human 数轮会多出没有题目的空轮，还容易把下一题的分数错配到上一题。
    """
    # 先转成普通列表：后面要按下标切片，生成器做不到；传 None 时也能安全当空会话处理。
    messages = list(messages or [])

    starts = [
        i for i, m in enumerate(messages)
        if _field(m, "type") == "tool" and _field(m, "name") == "ask_question"
    ]

    lines = [
        "# AI 技术面试官 · 面试报告",
        "",
        f"- 面试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 总轮数：{len(starts)}",
        "",
    ]

    scores = []
    if not starts:
        # 没出过题也要给一份能打开的文件，不能让浏览器下载到一个报错页面。
        lines += ["本场面试尚未产生题目，所有轮次均未评分。", ""]

    for idx, start in enumerate(starts):
        # 本轮的右边界是下一道题出现的位置；最后一轮就到消息末尾。
        end = starts[idx + 1] if idx + 1 < len(starts) else len(messages)
        turn = messages[start:end]

        question = _text_of(messages[start]) or "未记录"

        # 一轮里学生可能先寒暄再作答，取最后一条 human 才是真正的回答。
        answer = "未记录"
        for m in turn:
            if _field(m, "type") == "human":
                text = _text_of(m)
                if text:
                    answer = text

        # 只有评分工具的消息带分数，正文里没有就整轮记成"未评分"。
        score_text = "未评分"
        for m in turn:
            if _field(m, "type") == "tool" and _field(m, "name") == "score_answer":
                value = _parse_score(_field(m, "content", ""))
                if value is not None:
                    score_text = f"{value}/10"
                    scores.append(value)
                    break

        lines += [
            f"## 第 {idx + 1} 轮",
            "",
            f"- 题目：{question}",
            f"- 学生回答：{answer}",
            f"- 本轮得分：{score_text}",
            "",
        ]

    lines += ["## 总评", ""]
    if scores:
        total = sum(scores)
        average = total / len(scores)
        lines.append(f"累计得分 {total} 分，平均分 {average:.1f} / 10（共 {len(scores)} 轮有效评分）。")
    else:
        lines.append("未评分")
    lines.append("")

    return "\n".join(lines)
