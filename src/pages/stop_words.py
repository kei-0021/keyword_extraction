import streamlit as st

from src.utils.auth import require_login
from src.utils.supabase import get_supabase_client

# ログインを必須にする
require_login()

# Supabase クライアントの初期化
supabase = get_supabase_client()

# ログイン中のユーザー情報
user = st.session_state.user

st.title("ストップワード管理")


# データ取得
@st.cache_data(ttl=60)
def fetch_stop_words():
    user_id = st.session_state.user.id
    response = (
        supabase.table("stop_words").select("id, word").eq("user_id", user_id).execute()
    )
    return response.data or []


# 追加
def add_stop_word(word):
    user_id = st.session_state.user.id
    supabase.table("stop_words").insert({"user_id": user_id, "word": word}).execute()


# 削除
def delete_stop_word(word_id):
    supabase.table("stop_words").delete().eq("id", word_id).execute()


# 現在のストップワード一覧を取得
stop_words = fetch_stop_words()
existing_words = {entry["word"] for entry in stop_words}  # 重複チェック用セット

# 入力フォーム（key付きで入力内容をセッション管理）
new_word = st.text_input(
    "ストップワードを追加",
    value=st.session_state.get("new_word_input", ""),  # ここでvalue指定
    key="new_word_input",
)

if st.button("追加する") and new_word:
    cleaned_word = new_word.strip()
    if cleaned_word in existing_words:
        st.warning(f"「{cleaned_word}」は既に追加されています")
    else:
        add_stop_word(cleaned_word)
        st.success(f"「{cleaned_word}」を追加しました")
        st.cache_data.clear()
        st.session_state.new_word_input = ""
        st.rerun()  # 即時反映のため再読み込み

# ストップワード表示
st.subheader("現在のストップワード")
for entry in stop_words:
    word = entry["word"]
    word_id = entry["id"]
    col1, col2 = st.columns([8, 1])
    with col1:
        st.write(word)
    with col2:
        if st.button("削除", key=f"del_{word_id}"):
            delete_stop_word(word_id)
            st.cache_data.clear()
            st.rerun()
