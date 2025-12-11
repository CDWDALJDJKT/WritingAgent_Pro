import streamlit as st
import httpx
import json
import os
<<<<<<< HEAD
import uuid  # 引入 uuid 用于生成随机 ID
=======

>>>>>>> c1f4678ea5753baa64342355ffabad311ca1bf4b

# === 1. 基础配置 ===
st.set_page_config(
    page_title="写作智能体 Pro",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="auto"
)

# === 2. 核心逻辑配置 ===
API_URL = os.getenv("BACKEND_URL", "http://localhost:8000/chat")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "user_default"


def safe_decode(chunk):
    try:
        if isinstance(chunk, bytes):
            return chunk.decode('utf-8')
        return chunk
    except Exception:
        return ""


# === 3. 侧边栏 (极简设置) ===
with st.sidebar:
    st.header("⚙️ 设置")

    # 会话 ID 设置
    new_thread = st.text_input(
        "会话 ID",
        value=st.session_state.thread_id,
        help="修改 ID 可开启新话题"
    )
    if new_thread != st.session_state.thread_id:
        st.session_state.thread_id = new_thread
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # 功能按钮
    col1, col2 = st.columns(2)
    with col1:
        # [升级版清空] 点击清空时，自动换个新 ID，彻底解决“记忆断裂”报错
        if st.button("🗑️ 清空", type="primary", use_container_width=True):
            st.session_state.messages = []
            st.session_state.thread_id = f"user_{uuid.uuid4().hex[:8]}"
            st.rerun()
    with col2:
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()

    # [已删除] 烦人的服务器状态检测代码已移除

# === 4. 主聊天区域 ===
st.subheader(f"✍️ 全能写作智能体")
st.caption(f"当前会话: `{st.session_state.thread_id}`")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === 5. 输入处理 ===
if prompt := st.chat_input("请输入写作需求..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_box = st.empty()
        full_response = ""
<<<<<<< HEAD
        payload = {"query": prompt, "thread_id": st.session_state.thread_id}
=======

        # 定义后端 API 地址
        API_URL = os.getenv("BACKEND_URL", "http://backend:8000/chat")
        # 假设所有用户共用一个测试线程 ID，实际可以随机生成
        payload = {"query": prompt, "thread_id": "web_user_001"}
>>>>>>> c1f4678ea5753baa64342355ffabad311ca1bf4b

        try:
            with httpx.stream("POST", API_URL, json=payload, timeout=60) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if not line: continue
                        decoded_line = safe_decode(line)
                        if decoded_line.startswith("data: "):
                            json_str = decoded_line.replace("data: ", "")
                            try:
                                data = json.loads(json_str)
                                if "content" in data:
                                    full_response += data["content"]
                                    message_box.markdown(full_response + "▌")
                                elif "error" in data:
                                    st.error(f"处理出错: {data['error']}")
                            except json.JSONDecodeError:
                                continue

                    message_box.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    st.error(f"服务器请求失败: {response.status_code}")

<<<<<<< HEAD
        except httpx.ConnectError:
            st.error("无法连接到后端，请检查服务是否启动。")
        except Exception as e:
            st.error(f"发生未知错误: {str(e)}")
=======
        except httpx.RequestError as e:
            st.error(f"无法连接到后端服务，请确认 server.py 是否已启动。\n错误详情: {e}")
>>>>>>> c1f4678ea5753baa64342355ffabad311ca1bf4b
