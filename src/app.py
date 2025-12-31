import datetime
import io
from collections import Counter
from typing import cast

import streamlit as st

from src.core import generate_bar_chart, run_keyword_extraction

# --- (ログイン処理はそのまま) ---

st.title("Keyword Extraction")


# --- 月選択UIの追加 ---
def get_month_options():
    """2024年10月から現在までの年月リスト(YYYY-MM)を生成"""
    start_date = datetime.date(2024, 10, 1)
    end_date = datetime.date.today()

    options = []
    current = end_date
    while current >= start_date:
        options.append(current.strftime("%Y-%m"))
        # 前月の1日に移動
        first_of_month = current.replace(day=1)
        current = first_of_month - datetime.timedelta(days=1)
    return options


month_options = get_month_options()
selected_month = st.selectbox("解析対象月を選択してください", options=month_options)

# 解析ボタンの状態
is_running = st.session_state.get("running", False)

# ボタン押下で解析実行
if st.button(f"{selected_month} の解析開始", disabled=is_running):
    try:
        st.session_state.running = True
        with st.spinner(f"{selected_month} のデータを取得・解析中..."):
            # 選択された月を引数に渡す
            word_count = run_keyword_extraction(target_month=selected_month)
            st.session_state["word_count"] = word_count
            st.session_state["last_selected_month"] = selected_month  # 保存用
        st.success(f"{selected_month} の解析完了！")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
    finally:
        st.session_state.running = False

# 解析結果の表示（グラフ）
if "word_count" in st.session_state:
    word_count = cast(Counter[str], st.session_state["word_count"])
    # 保存しておいた月情報を取得
    display_month = st.session_state.get("last_selected_month", selected_month)

    # グラフ生成（target_monthを渡してラベルを最適化）
    fig = generate_bar_chart(word_count, target_month=display_month)
    st.plotly_chart(fig, use_container_width=True)

    # ダウンロードボタンのファイル名も動的に
    img_bytes = fig.to_image(format="png")
    st.download_button(
        label="PNG画像をダウンロード",
        data=io.BytesIO(img_bytes),
        file_name=f"keyword_chart_{display_month}.png",
        mime="image/png",
    )
