import streamlit as st

from src.core.main import main  # main() を直接呼び出すスタイル
from src.utils.auth import require_login, show_login


def run_analysis():
    try:
        st.session_state.running = True
        with st.spinner("解析を実行中...お待ちください"):
            word_count = main()  # 👈 カウントを受け取る
        st.success("解析完了！")

        # 👇 頻出単語を表示
        st.subheader("上位キーワード")
        for word, count in word_count.most_common(5):  # TOP_N と連携しても良い
            st.markdown(f"- **{word}**: {count} 回")

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
