import subprocess

import streamlit as st
from utils.auth import show_login


def run_analysis():
    st.session_state.running = True
    with st.spinner("解析を実行中...お待ちください"):
        result = subprocess.run(
            ["python3", "source/main.py"], capture_output=True, text=True
        )
    st.session_state.running = False
    if result.returncode == 0:
        st.success("解析完了！")
        st.code(result.stdout)
    else:
        st.error("エラー発生")
        st.code(result.stderr)


# 認証状態を確認
if "user" not in st.session_state:
    show_login()  # ログインフォームなどを表示して return で終了させるとよい
    st.stop()  # ← これ重要：ログインページの後ろは描画されないようにする
else:
    # ログイン済みのユーザーにだけ見せる画面
    st.title("Keyword Extraction")

    if st.button("解析開始"):
        run_analysis()
