"""過去の解析結果を表示するページモジュール."""

from typing import TypedDict, cast

import streamlit as st

from src.services import get_supabase_client, require_login


# 記録データの型定義
class MonthlyKeywordEntry(TypedDict):
    id: int
    target_month: str
    word: str
    count: int


# ログイン必須
require_login()
supabase = get_supabase_client()
user_id = st.session_state.user.id

# --- ヘッダーエリア ---
col_title, col_btn = st.columns([4, 1])
with col_title:
    st.title("過去の解析記録")
with col_btn:
    st.write("")
    if st.button("🔄 更新", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# --- データ取得ロジック ---
@st.cache_data(ttl=60)
def fetch_monthly_history(u_id: str) -> list[MonthlyKeywordEntry]:
    """Supabaseから全履歴を取得."""
    try:
        response = (
            supabase.table("monthly_keywords")
            .select("id, target_month, word, count")
            .eq("user_id", u_id)
            .order("target_month", desc=True)
            .order("count", desc=True)
            .execute()
        )
        return cast(list[MonthlyKeywordEntry], response.data or [])
    except Exception as e:
        st.error(f"データ取得に失敗しました: {e}")
        return []


history_data = fetch_monthly_history(user_id)

if not history_data:
    st.info("過去の解析記録はまだありません。メイン画面から解析を実行してください。")
    st.stop()

# --- 年の抽出と選択 ---
# target_month ("YYYY-MM-DD" または "YYYY-MM") から年だけを抽出
all_years = sorted(
    list({item["target_month"][:4] for item in history_data}), reverse=True
)
selected_year = st.selectbox("表示する年を選択", options=all_years)

# 選択された年のデータのみに絞り込み
yearly_data = [
    item for item in history_data if item["target_month"].startswith(selected_year)
]
# その年の中に存在する月を特定
months_in_year = sorted(
    list({item["target_month"] for item in yearly_data}), reverse=True
)

st.subheader(f"📅 {selected_year} 年の記録")
st.write(f"この年は {len(months_in_year)} ヶ月分のデータがあります。")
st.divider()

# --- メインコンテンツ：選択された年の月をループ ---
for month in months_in_year:
    month_data = [item for item in yearly_data if item["target_month"] == month]

    # 月ごとの表示
    with st.container():
        # 月の表示を少しオシャレに (例: 2025-01 -> 1月)
        month_label = month.split("-")[1].lstrip("0") + "月"
        st.markdown(f"### 📍 {month_label}")

        display_list = [
            {"キーワード": item["word"], "出現回数": item["count"]}
            for item in month_data
        ]

        st.table(display_list)
        st.write("")

st.divider()
st.caption("※同じ月の解析を再度実行すると、記録は自動的に最新の情報に更新されます。")
