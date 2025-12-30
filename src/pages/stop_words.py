from typing import Any, cast

import streamlit as st

from src.services.supabase_auth import require_login
from src.services.supabase_client import get_supabase_client

# ログインを必須にする
require_login()

# Supabase クライアントの初期化
supabase = get_supabase_client()

# ログイン中のユーザー情報
user = st.session_state.user

st.title("ストップワード管理")


# データ取得: 内部で型を確定させてから返す
@st.cache_data(ttl=60)
def fetch_stop_words() -> list[dict[str, Any]]:
    user_id = st.session_state.user.id
    response = (
        supabase.table("stop_words").select("id, word").eq("user_id", user_id).execute()
    )

    res_data = response.data
    if isinstance(res_data, list):
        # ここで関数内部で一度だけ cast し、戻り値の型と一致させる
        return cast(list[dict[str, Any]], res_data)
    return []


# 追加
def add_stop_word(word):
    user_id = st.session_state.user.id
    supabase.table("stop_words").insert({"user_id": user_id, "word": word}).execute()


# 削除
def delete_stop_word(word_id):
    print("現在のユーザーID:", st.session_state.user.id)

    print(f"削除リクエスト: id={word_id} / type={type(word_id)}")

    response = (
        supabase.table("stop_words")
        .delete()
        .eq("id", word_id)
        .eq("user_id", st.session_state.user.id)
        .execute()
    )

    print("削除レスポンス:", response)
    print("削除レスポンス data:", response.data)


# 現在のストップワード一覧を取得
stop_words = fetch_stop_words()
existing_words = {entry["word"] for entry in stop_words}  # 重複チェック用セット


if "input_key_version" not in st.session_state:
    st.session_state.input_key_version = 0

input_key = f"new_word_input_{st.session_state.input_key_version}"

new_word = st.text_input(
    "ストップワードを追加",
    key=input_key,
    placeholder="ストップワードを入力してください",
)


if st.button("追加する") and new_word:
    cleaned_word = new_word.strip()
    if cleaned_word in existing_words:
        st.warning(f"「{cleaned_word}」は既に追加されています")
    else:
        add_stop_word(cleaned_word)
        st.success(f"「{cleaned_word}」を追加しました")
        # キーを変えてウィジェットを新規生成 → 入力欄リセット効果
        st.session_state.input_key_version += 1
        st.cache_data.clear()
        st.session_state["new_word_input"] = ""
        st.rerun()


# ストップワード表示
stop_words_sorted = sorted(stop_words, key=lambda x: x["word"])
for entry in stop_words_sorted:
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
