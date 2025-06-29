import streamlit as st
from main import main  # main() を直接呼び出すスタイル
from utils.auth import require_login, show_login


def run_analysis():
    try:
        st.session_state.running = True
        with st.spinner("解析を実行中...お待ちください"):
            main()  # 副作用あるが、Streamlitセッションと連携して安全に実行
        st.success("解析完了！")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
    finally:
        st.session_state.running = False


def main_app():
    require_login()  # セッションが切れていれば再ログインさせる

    st.title("Keyword Extraction")

    if st.button("解析開始", disabled=st.session_state.get("running", False)):
        run_analysis()


# --- アプリ起動時のルート処理 ---
if "user" not in st.session_state:
    show_login()  # ログインページに飛ばす（セッション未初期化時）
    st.stop()
else:
    main_app()
