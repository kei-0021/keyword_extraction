import subprocess

import streamlit as st

st.title("Keyword Extraction")

if "running" not in st.session_state:
    st.session_state.running = False


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


if st.button("解析開始", disabled=st.session_state.running):
    run_analysis()
