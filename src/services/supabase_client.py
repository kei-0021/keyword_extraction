"""Supabaseクライアントの管理を行い、ユーザー認証を提供するモジュール."""

import os

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client


def get_supabase_client() -> Client:
    """Supabaseクライアントを生成または取得する関数."""
    if "supabase" not in st.session_state:
        load_dotenv("config/.env")
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        st.session_state.supabase = create_client(url, key)
    return st.session_state.supabase
