import streamlit as st
from conversation import ConversationManager
from rag import RAGSystem
import os
import tempfile

# 页面配置
st.set_page_config(
    page_title="LangChain 智能助手", page_icon="🤖", layout="wide", initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown(
    """
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
    }
    .chat-message.user {
        background-color: #f0f2f6;
    }
    .chat-message.assistant {
        background-color: #e8f4f8;
    }
    .chat-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }
    .chat-content {
        flex: 1;
    }
</style>
""",
    unsafe_allow_html=True,
)

# 初始化 session state
if "conversation_manager" not in st.session_state:
    st.session_state.conversation_manager = ConversationManager()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "rag_system" not in st.session_state:
    st.session_state.rag_system = None
if "mode" not in st.session_state:
    st.session_state.mode = "chat"
if "vector_store_type" not in st.session_state:
    st.session_state.vector_store_type = "qdrant"

# 侧边栏
with st.sidebar:
    st.title("🤖 LangChain 智能助手")
    st.markdown("---")

    # 模式选择
    st.subheader("📋 功能模式")
    mode = st.radio(
        "选择模式",
        ["💬 智能对话", "📚 RAG 文档问答"],
        index=0 if st.session_state.mode == "chat" else 1,
    )
    st.session_state.mode = "chat" if mode == "💬 智能对话" else "rag"

    st.markdown("---")

    # 模型配置
    st.subheader("⚙️ 模型配置")

    # 模型选择
    model_options = {
        "Ollama - gemma3": "ollama/gemma3",
        "Ollama - llama3.1": "ollama/llama3.1:8b",
        "Ollama - deepseek-r1": "ollama/deepseek-r1:7b",
        "OpenAI - gpt-4o": "gpt-4o",
        "OpenAI - gpt-3.5-turbo": "gpt-3.5-turbo",
    }

    selected_model = st.selectbox("选择模型", list(model_options.keys()), index=0)

    model = model_options[selected_model]
    st.session_state.conversation_manager.set_model(model)

    # 温度参数
    temperature = st.slider(
        "温度参数",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="控制输出的随机性。值越高，输出越随机；值越低，输出越确定。",
    )
    st.session_state.conversation_manager.set_temperature(temperature)

    st.markdown("---")

    # RAG 模式的额外配置
    if st.session_state.mode == "rag":
        st.subheader("📄 文档管理")

        # 向量存储类型选择
        vector_store_type = st.radio(
            "向量存储类型",
            ["Qdrant（推荐）", "FAISS"],
            index=0,
            help="Qdrant 支持持久化和更好的性能，FAISS 更轻量",
        )
        st.session_state.vector_store_type = "qdrant" if "Qdrant" in vector_store_type else "faiss"

        # 文件上传
        uploaded_files = st.file_uploader(
            "上传文档",
            type=["pdf", "txt", "docx"],
            accept_multiple_files=True,
            help="支持 PDF、TXT、DOCX 格式",
        )

        if uploaded_files:
            if st.button("处理文档", type="primary"):
                with st.spinner("正在处理文档..."):
                    # 保存上传的文件
                    temp_dir = tempfile.mkdtemp()
                    file_paths = []

                    for uploaded_file in uploaded_files:
                        file_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        file_paths.append(file_path)

                    # 初始化 RAG 系统
                    if st.session_state.rag_system is None:
                        st.session_state.rag_system = RAGSystem(
                            vector_store_type=st.session_state.vector_store_type
                        )

                    # 加载和处理文档
                    documents = st.session_state.rag_system.load_and_process_documents(file_paths)
                    st.session_state.rag_system.create_vector_store(documents)

                    st.success(f"✅ 成功处理 {len(uploaded_files)} 个文档！")

                    # 显示向量存储信息
                    if st.session_state.vector_store_type == "qdrant":
                        info = st.session_state.rag_system.get_collection_info()
                        st.info(f"📊 向量存储信息: {info.get('points_count', 0)} 个向量点")

        # 显示已加载的文档
        if st.session_state.rag_system is not None:
            st.info("📚 文档已加载，可以开始提问了！")

            # 显示向量存储信息
            if st.session_state.vector_store_type == "qdrant":
                if st.button("📊 查看向量存储信息"):
                    info = st.session_state.rag_system.get_collection_info()
                    st.json(info)

    st.markdown("---")

    # 清空对话
    if st.button("🗑️ 清空对话", type="secondary"):
        st.session_state.messages = []
        st.session_state.conversation_manager.clear_history()
        st.rerun()

    # 显示对话历史
    if st.session_state.messages:
        with st.expander("📜 对话历史"):
            for msg in st.session_state.messages:
                st.markdown(f"**{msg['role']}:** {msg['content'][:100]}...")

# 主界面
st.title("🤖 LangChain 智能助手")
st.markdown(f"**当前模式**: {mode}")
st.markdown(f"**当前模型**: {selected_model}")
st.markdown("---")

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 聊天输入
if prompt := st.chat_input("输入你的问题..."):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 生成回复
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("思考中...")

        try:
            if st.session_state.mode == "chat":
                # 普通对话模式
                response = st.session_state.conversation_manager.converse(prompt)
            else:
                # RAG 模式
                if st.session_state.rag_system is None:
                    response = "⚠️ 请先上传文档！"
                else:
                    answer, relevant_docs = st.session_state.rag_system.generate_answer(prompt)
                    response = answer

                    # 显示相关文档
                    if relevant_docs:
                        with st.expander("📖 相关文档片段"):
                            for i, doc in enumerate(relevant_docs[:3]):
                                st.markdown(f"**片段 {i+1}:**")
                                st.text(doc.page_content[:200] + "...")
                                st.markdown("---")

            message_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            error_msg = f"❌ 错误: {str(e)}"
            message_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# 页脚
st.markdown("---")
st.markdown(
    """
<div style='text-align: center; color: #666;'>
    <p>Powered by LangChain + Streamlit | 当前模型: {}</p>
</div>
""".format(selected_model),
    unsafe_allow_html=True,
)
