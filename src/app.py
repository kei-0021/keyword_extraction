import streamlit as st

from src.core.main import main as run_keyword_extraction
from src.utils.auth import require_login, show_login

# --- アプリ起動時のルート処理 ---
if "user" not in st.session_state:
    show_login()
    st.stop()

# ログイン済みなら以下を実行
require_login()

st.title("Keyword Extraction")

# 解析ボタンの状態
is_running = st.session_state.get("running", False)

# ボタン押下で解析実行
if st.button("解析開始", disabled=is_running):
    try:
        st.session_state.running = True
        with st.spinner("解析を実行中...お待ちください"):
            word_count = run_keyword_extraction()
            st.session_state["word_count"] = word_count
        st.success("解析完了！")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

    finally:
        st.session_state.running = False

# 解析結果の表示
if "word_count" in st.session_state:
    st.subheader("上位キーワード")
    for word, count in st.session_state["word_count"].most_common(5):
        st.markdown(f"- **{word}**: {count} 回")
