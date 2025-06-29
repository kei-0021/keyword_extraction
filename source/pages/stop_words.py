import streamlit as st
from utils.auth import require_login
from utils.supabase import get_supabase_client

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


# 入力フォーム
new_word = st.text_input("ストップワードを追加")
if st.button("追加する") and new_word:
    add_stop_word(new_word)
    st.success(f"「{new_word}」を追加しました")
    st.cache_data.clear()

# 現在のストップワード表示
st.subheader("現在のストップワード")
stop_words = fetch_stop_words()
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
            st.experimental_rerun()
