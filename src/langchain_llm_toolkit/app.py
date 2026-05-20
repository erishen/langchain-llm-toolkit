import contextlib
import os
import tempfile
import time
from datetime import datetime

import streamlit as st

from langchain_llm_toolkit.auth import AuthManager
from langchain_llm_toolkit.conversation import ConversationManager
from langchain_llm_toolkit.conversation_store import Conversation, ConversationStore
from langchain_llm_toolkit.hybrid_retriever import HybridRAGSystem
from langchain_llm_toolkit.rag import RAGSystem

st.set_page_config(
    page_title="LangChain LLM Toolkit",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp { max-width: 1400px; margin: 0 auto; }
    .chat-message { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .chat-message.user { background-color: #f0f2f6; }
    .chat-message.assistant { background-color: #e8f4f8; }
    .streaming-text { border-left: 3px solid #4CAF50; padding-left: 10px; }
    .doc-card { padding: 1rem; border: 1px solid #ddd; border-radius: 0.5rem; margin-bottom: 0.5rem; }
    .conv-item { padding: 0.5rem; border-radius: 0.25rem; cursor: pointer; }
    .conv-item:hover { background-color: #f0f2f6; }
    .conv-item.active { background-color: #e8f4f8; border-left: 3px solid #4CAF50; }
    .metric-card { padding: 1rem; background: #f8f9fa; border-radius: 0.5rem; text-align: center; }
    .metric-value { font-size: 2rem; font-weight: bold; color: #4CAF50; }
    .metric-label { font-size: 0.9rem; color: #666; }
</style>
""",
    unsafe_allow_html=True,
)

if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.conversation_manager = ConversationManager()
    st.session_state.messages = []
    st.session_state.rag_system = None
    st.session_state.mode = "chat"
    st.session_state.vector_store_type = "qdrant"
    st.session_state.embedding_model = "snowflake-arctic-embed2"
    st.session_state.use_streaming = True
    st.session_state.use_hybrid = False
    st.session_state.current_conversation_id = None
    st.session_state.conversation_store = ConversationStore()
    st.session_state.auth_manager = AuthManager()
    st.session_state.current_user = None
    st.session_state.jwt_token = None
    st.session_state.saved_conversations = []
    st.session_state.uploaded_docs = []
    st.session_state.page = "chat"


def init_rag_system():
    if st.session_state.rag_system is None:
        st.session_state.rag_system = RAGSystem(
            vector_store_type=st.session_state.vector_store_type,
            embedding_model=st.session_state.embedding_model,
        )
        with contextlib.suppress(Exception):
            st.session_state.rag_system.load_vector_store()


def stream_response(text: str, placeholder):
    """模拟流式输出"""
    displayed = ""
    for char in text:
        displayed += char
        placeholder.markdown(
            f'<div class="streaming-text">{displayed}▌</div>', unsafe_allow_html=True
        )
        time.sleep(0.01)
    placeholder.markdown(displayed)


def render_sidebar():
    with st.sidebar:
        st.title("🤖 LangChain Toolkit")
        st.markdown("---")

        page = st.radio(
            "导航",
            ["💬 智能对话", "📚 RAG 问答", "📝 对话管理", "📄 文档管理", "🔑 账户设置"],
            index=[
                "💬 智能对话",
                "📚 RAG 问答",
                "📝 对话管理",
                "📄 文档管理",
                "🔑 账户设置",
            ].index(st.session_state.get("page_label", "💬 智能对话")),
        )
        st.session_state.page_label = page

        if page == "💬 智能对话":
            st.session_state.page = "chat"
        elif page == "📚 RAG 问答":
            st.session_state.page = "rag"
        elif page == "📝 对话管理":
            st.session_state.page = "conversations"
        elif page == "📄 文档管理":
            st.session_state.page = "documents"
        elif page == "🔑 账户设置":
            st.session_state.page = "settings"

        st.markdown("---")

        st.subheader("⚙️ 模型配置")
        model_options = {
            "Ollama - gemma4 (推荐)": "ollama/gemma4",
            "Ollama - gemma3": "ollama/gemma3",
            "Ollama - llama3.1": "ollama/llama3.1:8b",
            "Ollama - deepseek-r1": "ollama/deepseek-r1:7b",
            "Ollama - deepseek-v3": "ollama/deepseek-v3",
            "OpenAI - gpt-5.3 (最新)": "gpt-5.3",
            "OpenAI - gpt-4o": "gpt-4o",
            "OpenAI - gpt-3.5-turbo": "gpt-3.5-turbo",
            "DeepSeek - V4 (最新)": "deepseek-chat",
            "DeepSeek - R1 推理": "deepseek-reasoner",
        }
        selected_model = st.selectbox("模型", list(model_options.keys()), index=0)
        model = model_options[selected_model]
        st.session_state.conversation_manager.set_model(model)

        temperature = st.slider("温度", 0.0, 2.0, 0.7, 0.1)
        st.session_state.conversation_manager.set_temperature(temperature)

        st.markdown("---")

        st.subheader("🎛️ 高级选项")
        st.session_state.use_streaming = st.checkbox("流式输出", value=True)
        if st.session_state.page == "rag":
            st.session_state.use_hybrid = st.checkbox("混合检索", value=False)

        st.markdown("---")

        if st.button("🗑️ 清空当前对话"):
            st.session_state.messages = []
            st.session_state.conversation_manager.clear_history()
            st.rerun()


def render_chat_page():
    st.title("💬 智能对话")
    st.markdown("---")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("输入你的问题..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("思考中...")

            try:
                response = st.session_state.conversation_manager.converse(prompt)

                if st.session_state.use_streaming:
                    stream_response(response, placeholder)
                else:
                    placeholder.markdown(response)

                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

            except Exception as e:
                error_msg = f"❌ 错误: {e!s}"
                placeholder.markdown(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )


def render_rag_page():
    st.title("📚 RAG 文档问答")
    st.markdown("---")

    init_rag_system()

    if st.session_state.rag_system.vector_store is not None:
        info = st.session_state.rag_system.get_collection_info()
        st.success(f"✅ 向量存储已加载: {info.get('points_count', 0)} 个向量点")
    else:
        st.warning("⚠️ 向量存储未加载，请上传文档")

    col1, col2 = st.columns([2, 1])

    with col1:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("sources"):
                    with st.expander("📖 参考文档"):
                        for src in message["sources"]:
                            source_name = src.get("source", "未知来源")
                            content = src.get("content", "")
                            st.markdown(f"**📄 {source_name}**")
                            st.markdown(
                                f"> {content[:400]}{'...' if len(content) > 400 else ''}"
                            )
                            st.markdown("")

        if prompt := st.chat_input("输入你的问题..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.markdown("思考中...")

                try:
                    init_rag_system()

                    if st.session_state.rag_system.vector_store is None:
                        placeholder.markdown("⚠️ 请先上传文档！")
                        return

                    if st.session_state.use_hybrid:
                        hybrid = HybridRAGSystem(st.session_state.rag_system)
                        answer, docs = hybrid.generate_answer(prompt)
                    else:
                        answer, docs = st.session_state.rag_system.generate_answer(
                            prompt
                        )

                    if st.session_state.use_streaming:
                        stream_response(answer, placeholder)
                    else:
                        placeholder.markdown(answer)

                    sources = [
                        {
                            "content": d.page_content,
                            "source": d.metadata.get("source", "未知"),
                        }
                        for d in docs
                    ]
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "sources": sources,
                        }
                    )

                    if docs:
                        with st.expander("📖 相关文档片段", expanded=True):
                            for i, doc in enumerate(docs[:3]):
                                source = doc.metadata.get("source", "未知来源")
                                content = doc.page_content
                                st.markdown(f"**📄 来源 {i + 1}:** `{source}`")
                                st.markdown(
                                    f"> {content[:500]}{'...' if len(content) > 500 else ''}"
                                )
                                st.markdown("")

                except Exception as e:
                    error_msg = f"❌ 错误: {e!s}"
                    placeholder.markdown(error_msg)

    with col2:
        st.subheader("📄 快速上传")
        uploaded_file = st.file_uploader("上传文档", type=["pdf", "txt", "docx", "md"])

        if uploaded_file and st.button("处理文档"):
            with st.spinner("处理中..."):
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
                )
                temp_file.write(uploaded_file.getbuffer())
                temp_file.close()

                init_rag_system()
                docs = st.session_state.rag_system.load_and_process_documents(
                    [temp_file.name]
                )
                st.session_state.rag_system.create_vector_store(docs)
                st.session_state.rag_system.save_vector_store()

                st.session_state.uploaded_docs.append(
                    {
                        "name": uploaded_file.name,
                        "size": len(uploaded_file.getbuffer()),
                        "time": datetime.now().strftime("%H:%M:%S"),
                    }
                )

                os.unlink(temp_file.name)
                st.success(f"✅ 已处理: {uploaded_file.name}")
                st.rerun()

        if st.session_state.uploaded_docs:
            st.subheader("📋 已上传文档")
            for doc in st.session_state.uploaded_docs[-5:]:
                st.markdown(f"- {doc['name']} ({doc['size'] // 1024}KB)")


def render_conversations_page():
    st.title("📝 对话管理")
    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("💾 保存对话")
        title = st.text_input("对话标题", "新对话")
        if st.button("保存当前对话"):
            conv = Conversation(
                id=st.session_state.current_conversation_id
                or datetime.now().strftime("%Y%m%d%H%M%S"),
                title=title,
                messages=[],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )
            for msg in st.session_state.messages:
                from langchain_llm_toolkit.conversation_store import Message

                conv.messages.append(
                    Message(
                        role=msg["role"],
                        content=msg["content"],
                        timestamp=datetime.now().isoformat(),
                    )
                )
            st.session_state.conversation_store.save_conversation(conv)
            st.success("✅ 对话已保存")
            st.rerun()

        st.markdown("---")
        st.subheader("📜 历史对话")

        conversations = st.session_state.conversation_store.list_conversations(limit=20)
        for conv in conversations:
            if st.button(f"📝 {conv.title[:20]}", key=f"load_{conv.id}"):
                st.session_state.current_conversation_id = conv.id
                st.session_state.messages = [
                    {"role": m.role, "content": m.content} for m in conv.messages
                ]
                st.rerun()

    with col2:
        st.subheader("📊 统计信息")
        stats = st.session_state.conversation_store.get_stats()

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                f'<div class="metric-card"><div class="metric-value">{stats["total_conversations"]}</div><div class="metric-label">总对话数</div></div>',
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                f'<div class="metric-card"><div class="metric-value">{stats["total_messages"]}</div><div class="metric-label">总消息数</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        if st.session_state.current_conversation_id:
            st.subheader("🔍 当前对话")
            conv = st.session_state.conversation_store.get_conversation(
                st.session_state.current_conversation_id
            )
            if conv:
                st.markdown(f"**标题**: {conv.title}")
                st.markdown(f"**创建时间**: {conv.created_at}")
                st.markdown(f"**消息数**: {len(conv.messages)}")

                col_del, col_export = st.columns(2)
                with col_del:
                    if st.button("🗑️ 删除对话"):
                        st.session_state.conversation_store.delete_conversation(conv.id)
                        st.session_state.current_conversation_id = None
                        st.rerun()
                with col_export:
                    if st.button("📤 导出对话"):
                        import json

                        data = conv.to_dict()
                        st.download_button(
                            "下载 JSON",
                            json.dumps(data, ensure_ascii=False, indent=2),
                            file_name=f"{conv.title}.json",
                            mime="application/json",
                        )


def render_documents_page():
    st.title("📄 文档管理")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📤 上传文档", "📋 文档列表", "⚙️ 向量存储"])

    with tab1:
        st.subheader("批量上传文档")

        embedding_options = {
            "snowflake-arctic-embed2 (推荐)": "snowflake-arctic-embed2",
            "nomic-embed-text": "nomic-embed-text",
            "mxbai-embed-large": "mxbai-embed-large",
            "qwen3-embedding:4b": "qwen3-embedding:4b",
        }
        selected_embedding = st.selectbox(
            "Embedding 模型",
            list(embedding_options.keys()),
            index=0,
            help="更换模型后需要重新上传文档",
        )
        new_embedding = embedding_options[selected_embedding]

        if new_embedding != st.session_state.embedding_model:
            st.warning("⚠️ 更换 Embedding 模型后需要重新上传文档！")
            if st.button("确认更换模型"):
                st.session_state.embedding_model = new_embedding
                st.session_state.rag_system = None
                st.success(f"✅ 已切换到 {new_embedding}")
                st.rerun()

        uploaded_files = st.file_uploader(
            "选择文档",
            type=["pdf", "txt", "docx", "md"],
            accept_multiple_files=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            vector_type = st.radio("向量存储类型", ["Qdrant（推荐）", "FAISS"], index=0)
            st.session_state.vector_store_type = (
                "qdrant" if "Qdrant" in vector_type else "faiss"
            )

        with col2:
            st.slider("分块大小", 200, 2000, 500, 100)
            st.slider("分块重叠", 0, 200, 50, 25)

        if uploaded_files and st.button("处理所有文档", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            init_rag_system()

            temp_dir = tempfile.mkdtemp()
            total = len(uploaded_files)

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"处理中: {uploaded_file.name} ({i + 1}/{total})")

                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                docs = st.session_state.rag_system.load_and_process_documents(
                    [file_path]
                )
                st.session_state.rag_system.create_vector_store(docs)

                st.session_state.uploaded_docs.append(
                    {
                        "name": uploaded_file.name,
                        "size": len(uploaded_file.getbuffer()),
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

                progress_bar.progress((i + 1) / total)

            st.session_state.rag_system.save_vector_store()
            st.success(f"✅ 成功处理 {total} 个文档！")

    with tab2:
        st.subheader("已上传文档")
        if st.session_state.uploaded_docs:
            for doc in st.session_state.uploaded_docs:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    col1.markdown(f"📄 **{doc['name']}**")
                    col2.markdown(f"📦 {doc['size'] // 1024} KB")
                    col3.markdown(f"🕐 {doc['time']}")
        else:
            st.info("暂无已上传的文档")

    with tab3:
        st.subheader("向量存储信息")
        init_rag_system()

        try:
            st.session_state.rag_system.load_vector_store()
            info = st.session_state.rag_system.get_collection_info()
            st.json(info)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-value">{info.get("points_count", 0)}</div><div class="metric-label">向量点数</div></div>',
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-value">{st.session_state.vector_store_type.upper()}</div><div class="metric-label">存储类型</div></div>',
                    unsafe_allow_html=True,
                )

            if st.button("🗑️ 清空向量存储", type="secondary"):
                st.session_state.rag_system.delete_collection()
                st.session_state.rag_system = None
                st.session_state.uploaded_docs = []
                st.success("✅ 向量存储已清空")
                st.rerun()

        except Exception:
            st.info("向量存储未初始化，请先上传文档")


def render_settings_page():
    st.title("🔑 账户设置")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🔐 认证", "🔑 API Keys", "⚙️ 系统设置"])

    with tab1:
        if st.session_state.current_user:
            st.success(f"✅ 已登录: {st.session_state.current_user['username']}")

            if st.button("退出登录"):
                st.session_state.current_user = None
                st.session_state.jwt_token = None
                st.rerun()
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("登录")
                login_user = st.text_input("用户名", key="login_user")
                login_pass = st.text_input("密码", type="password", key="login_pass")

                if st.button("登录"):
                    user = st.session_state.auth_manager.authenticate_user(
                        login_user, login_pass
                    )
                    if user:
                        token = st.session_state.auth_manager.create_access_token(user)
                        st.session_state.current_user = {
                            "id": user.id,
                            "username": user.username,
                        }
                        st.session_state.jwt_token = token
                        st.success("✅ 登录成功")
                        st.rerun()
                    else:
                        st.error("❌ 用户名或密码错误")

            with col2:
                st.subheader("注册")
                reg_user = st.text_input("用户名", key="reg_user")
                reg_email = st.text_input("邮箱", key="reg_email")
                reg_pass = st.text_input("密码", type="password", key="reg_pass")

                if st.button("注册"):
                    try:
                        user = st.session_state.auth_manager.create_user(
                            reg_user, reg_email, reg_pass
                        )
                        st.success(f"✅ 注册成功: {user.username}")
                    except ValueError as e:
                        st.error(f"❌ {e!s}")

    with tab2:
        if not st.session_state.current_user:
            st.warning("请先登录")
        else:
            st.subheader("API Keys")

            keys = st.session_state.auth_manager.store.list_api_keys(
                st.session_state.current_user["id"]
            )

            if keys:
                for key in keys:
                    col1, col2, col3 = st.columns([3, 2, 1])
                    col1.markdown(f"🔑 **{key['name']}**")
                    col2.markdown(f"🕐 {key.get('created_at', 'N/A')[:10]}")
                    if col3.button("删除", key=f"del_{key['key_id']}"):
                        st.session_state.auth_manager.store.revoke_api_key(
                            key["key_id"]
                        )
                        st.rerun()

            st.markdown("---")
            new_key_name = st.text_input("新 API Key 名称")
            if st.button("创建 API Key"):
                api_key = st.session_state.auth_manager.create_api_key(
                    st.session_state.current_user["id"],
                    new_key_name,
                )
                st.success("✅ API Key 已创建")
                st.code(api_key, language="text")
                st.warning("⚠️ 请立即保存此 Key，它只会显示一次")

    with tab3:
        st.subheader("系统设置")

        db_path = st.text_input(
            "对话数据库路径",
            value=os.environ.get("CONVERSATION_DB_PATH", "./data/conversations.db"),
        )
        rag_path = st.text_input(
            "RAG 存储路径", value=os.environ.get("RAG_QDRANT_PATH", "./qdrant_storage")
        )

        if st.button("保存设置"):
            os.environ["CONVERSATION_DB_PATH"] = db_path
            os.environ["RAG_QDRANT_PATH"] = rag_path
            st.success("✅ 设置已保存")


def main():
    render_sidebar()

    page = st.session_state.page

    if page == "chat":
        render_chat_page()
    elif page == "rag":
        render_rag_page()
    elif page == "conversations":
        render_conversations_page()
    elif page == "documents":
        render_documents_page()
    elif page == "settings":
        render_settings_page()

    st.markdown("---")
    st.markdown(
        """<div style='text-align: center; color: #666;'>
            <p>Powered by LangChain + Streamlit | v0.2.0</p>
        </div>""",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
