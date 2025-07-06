import streamlit as st

from src.services.supabase_auth import require_login
from src.services.supabase_client import get_supabase_client

require_login()

supabase = get_supabase_client()
user_id = st.session_state.user.id

st.title("ユーザー辞書")


@st.cache_data(ttl=60)
def fetch_user_dict():
    response = (
        supabase.table("user_dict")
        .select("id, word, reading")
        .eq("user_id", user_id)
        .execute()
    )
    return response.data or []


def add_user_entry(word, reading):
    # 品詞は「名詞」、発音は読みと同じものを自動設定
    supabase.table("user_dict").insert(
        {
            "user_id": user_id,
            "word": word,
            "part_of_speech": "名詞",
            "reading": reading,
            "pronunciation": reading,
        }
    ).execute()


def delete_user_entry(entry_id):
    supabase.table("user_dict").delete().eq("id", entry_id).eq(
        "user_id", user_id
    ).execute()


user_dict = fetch_user_dict()
existing_entries = {(e["word"], e["reading"]) for e in user_dict}

col1, col2 = st.columns(2)
with col1:
    new_word = st.text_input("単語（例：基本情報技術者試験）")
with col2:
    new_reading = st.text_input("読み（例：キホンジョウホウギジュツシャシケン）")

if st.button("追加する") and new_word and new_reading:
    cleaned = (new_word.strip(), new_reading.strip())
    if cleaned in existing_entries:
        st.warning("その単語と読みの組み合わせは既に登録されています")
    else:
        add_user_entry(*cleaned)
        st.success(f"{cleaned[0]} を辞書に追加しました")
        st.cache_data.clear()
        st.rerun()

st.subheader("登録済みの単語")

user_dict_sorted = sorted(user_dict, key=lambda x: x["word"])
for entry in user_dict_sorted:
    word, reading, entry_id = entry["word"], entry["reading"], entry["id"]

    col1, col2, col3 = st.columns([4, 4, 1])
    with col1:
        st.write(word)
    with col2:
        st.write(reading)
    with col3:
        if st.button("削除", key=f"del_{entry_id}"):
            delete_user_entry(entry_id)
            st.cache_data.clear()
            st.rerun()
