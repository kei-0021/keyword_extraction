"""キーワード抽出ツールのStreamlitエントリーポイント."""

import datetime
import io
from collections import Counter
from typing import cast

import pytz
import streamlit as st

from src.core import generate_bar_chart, run_keyword_extraction
from src.services import require_login, show_login
from src.services.supabase_client import get_supabase_client


def save_analysis_to_supabase(word_count, supabase, user_id, top_n=5):
    """解析結果をSupabaseに保存する（既存データは削除）."""
    supabase.table("analysis_result").delete().eq("user_id", user_id).execute()

    data = [
        {
            "user_id": user_id,
            "word": word,
            "count": count,
        }
        for word, count in word_count.most_common(top_n)
    ]
    if data:
        supabase.table("analysis_result").insert(data).execute()


def load_last_analysis(supabase, user_id):
    """最新の解析結果をSupabaseから取得する."""
    response = (
        supabase.table("analysis_result")
        .select("word, count, updated_at")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .limit(5)
        .execute()
    )
    if response.data:
        last_updated = response.data[0].get("updated_at", None)
        word_counts = Counter({item["word"]: item["count"] for item in response.data})
        return word_counts, last_updated
    return None, None


def format_jst_datetime(dt_str):
    """ISO8601文字列をJSTの日本語フォーマットに変換する."""
    import dateutil.parser

    dt = dateutil.parser.isoparse(dt_str)
    jst = dt.astimezone(pytz.timezone("Asia/Tokyo"))
    return jst.strftime("%Y年%-m月%-d日 %H:%M")


def get_month_options() -> list[str]:
    """2024年10月から現在までの年月リスト(YYYY-MM)を降順で生成."""
    start_date = datetime.date(2024, 10, 1)
    current = datetime.date.today()

    options: list[str] = []
    while current >= start_date:
        options.append(current.strftime("%Y-%m"))
        current = current.replace(day=1) - datetime.timedelta(days=1)
    return options


# --- 1. ログインガード ---
if "user" not in st.session_state:
    show_login()
    st.stop()

require_login()

# --- 2. メインUI ---
st.title("Keyword Extraction")

supabase = get_supabase_client()
user_id = st.session_state.user.id

# 前回の解析結果をセッションに読み込む
if "word_count" not in st.session_state:
    last_word_count, last_updated = load_last_analysis(supabase, user_id)
    if last_word_count:
        st.session_state["word_count"] = last_word_count
        st.session_state["last_updated"] = last_updated
    else:
        st.session_state["last_updated"] = None

# 解析設定
st.subheader("解析設定")
month_options = get_month_options()
selected_month = st.selectbox("解析対象月を選択してください", options=month_options)

is_running = st.session_state.get("running", False)

if st.button(f"{selected_month} の解析開始", disabled=is_running):
    try:
        st.session_state.running = True
        with st.spinner(f"{selected_month} のデータを取得・解析中..."):
            word_count = run_keyword_extraction(target_month=selected_month)
            st.session_state["word_count"] = word_count
            st.session_state["last_selected_month"] = selected_month

            # Supabaseに保存
            save_analysis_to_supabase(word_count, supabase, user_id, top_n=5)

            # 最新日時を取得し直し
            _, last_updated = load_last_analysis(supabase, user_id)
            st.session_state["last_updated"] = last_updated

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
    st.plotly_chart(fig, use_container_width=True)

    # ダウンロードと最終更新日時
    col1, col2 = st.columns([1, 1])
    with col1:
        img_bytes = fig.to_image(format="png")
        st.download_button(
            label="PNGをダウンロード",
            data=io.BytesIO(img_bytes),
            file_name=f"keyword_chart_{display_month}.png",
            mime="image/png",
        )

    with col2:
        if st.session_state.get("last_updated"):
            formatted_date = format_jst_datetime(st.session_state["last_updated"])
            st.write(f"最終解析日時: {formatted_date}")
