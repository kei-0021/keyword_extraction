import os

import streamlit as st
from supabase import Client, create_client


def get_supabase_client() -> Client:
    """Supabaseクライアントを生成または取得する関数."""
    if "supabase" not in st.session_state:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        st.session_state.supabase = create_client(url, key)
    return st.session_state.supabase
