import os
import dotenv

# 1. 先加载环境变量
dotenv.load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from src.editorial_team import build_team_graph
import json
import asyncio
# [新增] 引入异步相关库
from contextlib import asynccontextmanager
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


# === 2. 定义生命周期管理 ===
# 以前我们是在全局直接 build_team_graph()，现在不行了
# 我们需要在服务“启动时”创建异步连接，在“关闭时”断开连接
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动阶段：创建异步数据库连接
    print("🔄 正在初始化异步数据库连接...")
    async with AsyncSqliteSaver.from_conn_string("memory.sqlite") as checkpointer:
        # [关键] 建立图，并注入异步 checkpointer
        # 我们把构建好的图存在 app.state 里，全局可用
        app.state.agent_graph = build_team_graph(checkpointer=checkpointer)
        print("✅ 智能体图构建完成 (异步模式)")
        yield
    # 关闭阶段 (yield 之后)：自动清理资源
    print("👋 数据库连接已关闭")


# 3. 初始化 FastAPI (挂载 lifespan)
app = FastAPI(title="写作智能体 API 服务", lifespan=lifespan)


class ChatRequest(BaseModel):
    query: str
    thread_id: str = "default_thread"


async def generate_stream(query: str, thread_id: str, graph):  # 多传一个 graph 参数
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # 使用 graph.astream 进行异步流式传输
        async for msg, metadata in graph.astream(
                {"messages": [HumanMessage(content=query)]},
                config=config,
                stream_mode="messages"
        ):
            if msg.content:
                yield f"data: {json.dumps({'content': msg.content}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # 从 app.state 中取出我们在启动时构建好的图
    return StreamingResponse(
        generate_stream(request.query, request.thread_id, app.state.agent_graph),
        media_type="text/event-stream"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)