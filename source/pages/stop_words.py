import os

import streamlit as st
from utils.auth import require_login

STOP_WORDS_FILE = "custom_dict/stop_words.txt"


def load_stop_words():
    if not os.path.exists(STOP_WORDS_FILE):
        return []
    with open(STOP_WORDS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def save_stop_word(word):
    with open(STOP_WORDS_FILE, "a", encoding="utf-8") as f:
        f.write(word + "\n")


def delete_stop_word(word):
    words = load_stop_words()
    words = [w for w in words if w != word]
    with open(STOP_WORDS_FILE, "w", encoding="utf-8") as f:
        for w in words:
            f.write(w + "\n")


require_login()
st.title("ストップワード管理")

new_word = st.text_input("ストップワードを追加")
if st.button("追加する") and new_word:
    save_stop_word(new_word)
    st.success(f"'{new_word}' を追加しました！")

st.subheader("現在のストップワード")

stop_words = load_stop_words()
for word in stop_words:
    col1, col2 = st.columns([8, 1])
    with col1:
        st.write(word)
    with col2:
        # keyにユニークな文字列を指定
        if st.button("削除", key=f"del_{word}"):
            delete_stop_word(word)
            st.experimental_rerun()
