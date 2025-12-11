import dotenv
from src.editorial_team import build_team_graph

dotenv.load_dotenv()


def main():
    print("🚀 全能编辑部 (Pro版 - 流式直播) 已启动...")

    agent = build_team_graph()

    # 保持 thread_id 不变，继续利用你的 sqlite 记忆
    config = {"configurable": {"thread_id": "team_thread_001"}}

    user_input = "请再帮我写一段关于'Python'的短评，这次要幽默一点，写完记得查字数。"
    print(f"User: {user_input}\n")
    print("--- 正在连接编辑部直播间 ---")

    # === [核心修改] 开启流式传输 ===
    # 1. 使用 stream_mode="messages"
    #    根据文档：这允许我们在 LLM 生成 token 时直接获取它们

    events = agent.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config,
        stream_mode="messages"  # 关键改动！
    )

    # 用于记录上一个打印的节点，方便分段
    last_node = None

    for msg, metadata in events:
        # metadata 中包含了当前是谁在说话 (langgraph_node)
        # 比如 'agent' (主编), 'call_writer' (工具/子智能体) 等
        current_node = metadata.get('langgraph_node')

        # 如果切换了说话人，打印个换行分隔一下
        if current_node != last_node:
            print(f"\n\n[{current_node}]: ", end="", flush=True)
            last_node = current_node

        # 判断消息类型
        # 如果是 AIMessageChunk (AI 的碎片)，它包含 .content
        if msg.content:
            # end="" 表示不换行，flush=True 表示立即输出不要缓存
            print(msg.content, end="", flush=True)

        # 进阶观察：你甚至可以看到工具调用的碎片 (tool_call_chunks)
        # 如果你想看它怎么构造工具参数的，可以把下面这行注释打开
        # if msg.tool_call_chunks:
        #     print(f"⚙️", end="", flush=True)

    print("\n\n--- 流程结束 ---")


if __name__ == "__main__":
    main()