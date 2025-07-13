import pytz
import streamlit as st

from src.core.keyword_extraction import run_keyword_extraction
from src.core.plot import generate_bar_chart
from src.services.supabase_auth import require_login, show_login
from src.services.supabase_client import get_supabase_client


def save_analysis_to_supabase(word_count, supabase, user_id, top_n=5):
    # 既存データ削除（ユーザーの解析結果を全部消す）
    supabase.table("analysis_result").delete().eq("user_id", user_id).execute()

    # 上位top_nだけ保存（updated_atはSupabase側で自動設定）
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
    # 最新の解析結果を取得（updated_at付き）
    response = (
        supabase.table("analysis_result")
        .select("word, count, updated_at")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .limit(5)
        .execute()
    )
    if response.data:
        from collections import Counter

        # updated_atは全行同じと仮定し、先頭のレコードから取得
        last_updated = response.data[0].get("updated_at", None)

        word_counts = Counter({item["word"]: item["count"] for item in response.data})
        return word_counts, last_updated
    return None, None


def format_jst_datetime(dt_str):
    # ISO8601のUTC文字列を受けてJSTの日本語フォーマットに変換

    import dateutil.parser

    dt = dateutil.parser.isoparse(dt_str)
    # JSTタイムゾーンに変換
    jst = dt.astimezone(pytz.timezone("Asia/Tokyo"))
    return jst.strftime("%Y年%-m月%-d日 %H:%M")


# --- アプリ起動時のルート処理 ---
if "user" not in st.session_state:
    show_login()
    st.stop()

require_login()

st.title("Keyword Extraction")

supabase = get_supabase_client()
user_id = st.session_state.user.id

# まず前回の解析結果を読み込む
if "word_count" not in st.session_state:
    last_word_count, last_updated = load_last_analysis(supabase, user_id)
    if last_word_count:
        st.session_state["word_count"] = last_word_count
        st.session_state["last_updated"] = last_updated
    else:
        st.session_state["last_updated"] = None

# 解析ボタンの状態
is_running = st.session_state.get("running", False)

if st.button("解析開始", disabled=is_running):
    try:
        st.session_state.running = True
        with st.spinner("解析を実行中...お待ちください"):
            word_count = run_keyword_extraction()
            st.session_state["word_count"] = word_count

            # Supabaseに保存（updated_atは自動）
            save_analysis_to_supabase(word_count, supabase, user_id, top_n=5)

            # 保存後は改めて最新日時を取得し直すのがおすすめ
            _, last_updated = load_last_analysis(supabase, user_id)
            st.session_state["last_updated"] = last_updated

        st.success("解析完了！")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

    finally:
        st.session_state.running = False

# 解析結果の表示（グラフ）
if "word_count" in st.session_state:
    fig = generate_bar_chart(st.session_state["word_count"])
    st.plotly_chart(fig, use_container_width=True)


# 最終解析日時の表示
if "last_updated" in st.session_state and st.session_state["last_updated"]:
    formatted_date = format_jst_datetime(st.session_state["last_updated"])
    st.write(f"最終解析日時: {formatted_date}")
