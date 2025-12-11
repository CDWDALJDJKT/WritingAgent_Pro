import os

from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from src.tools import get_tools
"""
这里负责把模型、工具、记忆拼装在一起。
"""

def build_agent_graph():
    # === 1. 准备模型 (适配阿里云千问) ===
    # 文档指出：通过指定 base_url 参数，可以对接兼容 OpenAI 协议的提供商
    model = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "qwen-plus"),  # 读取环境变量中的 qwen-plus
        api_key=os.getenv("DASHSCOPE_API_KEY"),  # 读取你的阿里 Key
        base_url=os.getenv("DASHSCOPE_BASE_URL"),  # 指向阿里的地址
        temperature=0.7
    )

    # === 2. 获取工具 ===
    tools = get_tools()

    # === 3. 准备记忆 ===
    checkpointer = InMemorySaver()

    # === [关键修改] 配置“人机交互”中间件 ===
    # 告诉它：看到 "word_counter" 这个工具时，请打断 (True)
    hitl_middleware = HumanInTheLoopMiddleware(
        interrupt_on={
            "word_counter": True  # 允许所有决策（批准/拒绝/修改）
        }
    )

    # === 4. 创建智能体图 ===
    graph = create_agent(
        model,
        tools,
        checkpointer=checkpointer,
        system_prompt="你是一个专业写作助手。如果用户问字数，必须调用 word_counter 工具。",
        # 使用 middleware 参数
        middleware=[hitl_middleware]

    )

    return graph