import streamlit as st
import httpx
import json
import os



# === 1. 页面配置 ===
st.set_page_config(page_title="全能写作助手", page_icon="✍️")
st.title("✍️ Pro版写作智能体")
st.caption("架构：Streamlit (前端) -> FastAPI (后端) -> LangGraph (多智能体)")

# === 2. 初始化聊天记录 ===
# Streamlit 每次操作都会重跑代码，所以要用 session_state 记住聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === 3. 处理用户输入 ===
if prompt := st.chat_input("请输入你的写作需求..."):
    # A. 显示用户的话
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B. 请求后端并显示 AI 的话
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # 定义后端 API 地址
        API_URL = os.getenv("BACKEND_URL", "http://backend:8000/chat")
        # 假设所有用户共用一个测试线程 ID，实际可以随机生成
        payload = {"query": prompt, "thread_id": "web_user_001"}

        try:
            with httpx.stream("POST", API_URL, json=payload, timeout=None) as response:
                if response.status_code == 200:
                    for chunk in response.iter_lines():
                        if chunk:
                            # [核心修改] chunk 已经是字符串了，不需要 decode
                            # 直接用它就行！
                            decoded_chunk = chunk

                            if decoded_chunk.startswith("data: "):
                                json_str = decoded_chunk.replace("data: ", "")
                                try:
                                    data = json.loads(json_str)
                                    if "content" in data:
                                        content = data["content"]
                                        full_response += content
                                        message_placeholder.markdown(full_response + "▌")
                                    elif "error" in data:
                                        st.error(f"后端报错: {data['error']}")
                                except json.JSONDecodeError:
                                    pass

                    # 只有流结束后，才把完整回复存入历史记录
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    st.error(f"服务器连接失败: {response.status_code}")

        except httpx.RequestError as e:
            st.error(f"无法连接到后端服务，请确认 server.py 是否已启动。\n错误详情: {e}")
