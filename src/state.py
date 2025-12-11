from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
import operator
"""
定义记忆结构,它决定了智能体能记住什么。
"""


# 定义智能体的“大脑内存结构”
# message 列表会自动累加历史记录
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    # 你以后可以在这里加别的，比如 user_name, current_task 等