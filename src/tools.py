from langchain.tools import tool
"""
定义工具
"""

@tool
def word_counter(text: str) -> str:
    """
    统计文本字数。
    参数 text: 需要统计的文本内容。
    """
    return f"当前文本字数：{len(text)} 字。"

# 导出工具列表，方便 agent.py 调用
def get_tools():
    return [word_counter]