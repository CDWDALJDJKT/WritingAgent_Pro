import os
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
# [新增] 引入 Pydantic 用于定义结构
from pydantic import BaseModel, Field
from typing import List
import sqlite3
from src.tools import get_tools


def get_model():
    return ChatOpenAI(
        model=os.getenv("MODEL_NAME", "qwen-plus"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        temperature=0.7
    )


# === 1. [新增] 定义审核评分表 ===
class ReviewReport(BaseModel):
    """审核员必须填写的评分报告"""
    word_count: int = Field(description="文章的准确字数")
    score: int = Field(description="文章质量评分，满分100分")
    comments: List[str] = Field(description="具体的修改建议列表，每条建议一句")
    is_passed: bool = Field(description="是否达到发表标准（评分80以上且字数符合要求）")


# --- 作家智能体 (保持不变) ---
def make_writer_agent():
    model = get_model()
    return create_agent(
        model,
        tools=[],
        system_prompt="你是一名极具才华的作家。你的职责是根据指令撰写高质量的草稿。"
    )


# --- 审核智能体 (升级版) ---
def make_reviewer_agent():
    model = get_model()
    tools = get_tools()

    return create_agent(
        model,
        tools,
        # [关键修改] 告诉 AI：你的输出必须符合 ReviewReport 的格式
        # 文档依据：create_agent 会自动处理 response_format
        response_format=ReviewReport,
        system_prompt="你是一名严谨的编辑。请先使用 word_counter 统计字数，然后根据内容质量填写审核报告。"
    )


# --- 工具定义 ---

@tool
def call_writer(request: str) -> str:
    """
    【呼叫作家】当需要撰写新内容、修改文章或进行创作时，使用此工具。
    参数 request: 给作家的具体写作指令。
    """
    # ^^^ 上面这一段注释非常重要，绝对不能省！ ^^^

    print(f"\n📢 [主编] 正在给 [作家] 派活: {request}")
    agent = make_writer_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": request}]})
    return result["messages"][-1].content


@tool
def call_reviewer(content_to_review: str) -> str:
    """
    【呼叫审核员】当需要审核文章时使用。
    """
    print(f"\n📢 [主编] 正在给 [审核员] 派活: 请审核这段内容...")
    agent = make_reviewer_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": content_to_review}]})

    # [核心修改] 获取结构化数据
    # 文档依据：结构化响应将在 structured_response 键中返回
    structured_res = result.get("structured_response")

    if structured_res:
        # 这里我们拿到了真正的 Python 对象！
        # 在实际工程中，你可以把这个存入数据库，或者根据 is_passed 自动触发后续流程
        report = f"""
【审核报告】
- 字数: {structured_res.word_count}
- 评分: {structured_res.score}
- 结论: {'✅ 通过' if structured_res.is_passed else '❌ 未通过'}
- 建议: {'; '.join(structured_res.comments)}
"""
        return report
    else:
        # 兜底：万一 AI 没返回结构化数据（虽然概率很低）
        return result["messages"][-1].content


# --- 主编构建函数 (保持不变) ---
def build_team_graph(checkpointer=None):
    model = get_model()
    supervisor_tools = [call_writer, call_reviewer]

    # [逻辑升级] 兼容模式：
    # 1. 如果外部没传 (main.py 调用时)，我们就自己造个同步的 (SqliteSaver)
    # 2. 如果外部传了 (server.py 调用时)，我们就用传进来的 (AsyncSqliteSaver)
    if checkpointer is None:
        conn = sqlite3.connect("memory.sqlite", check_same_thread=False)
        checkpointer = SqliteSaver(conn)

    graph = create_agent(
        model,
        supervisor_tools,
        checkpointer=checkpointer,
        system_prompt="""你是一个编辑部的主编。
        请指挥作家写文章，然后指挥审核员进行审核。
        最终你需要把审核员的【审核报告】摘要汇报给用户。"""
    )

    return graph