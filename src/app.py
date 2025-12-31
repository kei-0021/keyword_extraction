"""キーワード抽出ツールのStreamlitエントリーポイント."""

import datetime
import io
from collections import Counter
from typing import cast

import streamlit as st

from src.core import generate_bar_chart, run_keyword_extraction
from src.services import require_login, show_login

# --- 1. ログインガード ---
# このブロックが st.selectbox 等のUI定義より前にあることが必須
if "user" not in st.session_state:
    show_login()
    st.stop()  # 未ログイン時はここで処理を中断し、以降のUIを描画させない

# ログイン済みの場合の処理
require_login()

# --- 2. ログイン後のみ表示されるメインUI ---
st.title("Keyword Extraction")


def get_month_options() -> list[str]:
    """2024年10月から現在までの年月リスト(YYYY-MM)を降順で生成."""
    start_date = datetime.date(2024, 10, 1)
    current = datetime.date.today()

    options: list[str] = []
    while current >= start_date:
        options.append(current.strftime("%Y-%m"))
        # 前月の末日に移動
        current = current.replace(day=1) - datetime.timedelta(days=1)
    return options


# サイドバーまたはメインエリアに設定を配置
st.subheader("解析設定")
month_options = get_month_options()
selected_month = st.selectbox("解析対象月を選択してください", options=month_options)

# 解析実行ボタン
is_running = st.session_state.get("running", False)

if st.button(f"{selected_month} の解析開始", disabled=is_running):
    try:
        st.session_state.running = True
        with st.spinner(f"{selected_month} のデータを取得・解析中..."):
            # コアロジックの呼び出し
            word_count = run_keyword_extraction(target_month=selected_month)
            st.session_state["word_count"] = word_count
            st.session_state["last_selected_month"] = selected_month
        st.success(f"{selected_month} の解析が完了しました！")
    except Exception as e:
        st.error(f"解析中にエラーが発生しました: {e}")
    finally:
        st.session_state.running = False

st.divider()

# --- 3. 解析結果の表示 ---
if "word_count" in st.session_state:
    word_count = cast(Counter[str], st.session_state["word_count"])
    display_month = st.session_state.get("last_selected_month", selected_month)

    st.subheader(f"解析結果: {display_month}")

    # グラフ生成
    fig = generate_bar_chart(word_count, target_month=display_month)
    st.plotly_chart(fig, width="content")

    # ダウンロードエリア
    col1, col2 = st.columns([1, 3])
    with col1:
        img_bytes = fig.to_image(format="png")
        st.download_button(
            label="PNGをダウンロード",
            data=io.BytesIO(img_bytes),
            file_name=f"keyword_chart_{display_month}.png",
            mime="image/png",
        )
