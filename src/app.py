import io
from collections import Counter
from typing import cast

import streamlit as st

from src.core import generate_bar_chart, run_keyword_extraction
from src.services import require_login, show_login

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

# 解析結果の表示（グラフ）
if "word_count" in st.session_state:
    word_count = cast(Counter[str], st.session_state["word_count"])

    # グラフ生成
    fig = generate_bar_chart(word_count)
    st.plotly_chart(fig, use_container_width=True)

    # PNGデータをバイトストリームで取得
    img_bytes = fig.to_image(format="png")

    # バイトデータをBytesIOに入れる
    img_io = io.BytesIO(img_bytes)

    # ダウンロードボタン表示
    st.download_button(
        label="PNG画像をダウンロード",
        data=img_io,
        file_name="keyword_chart.png",
        mime="image/png",
    )
