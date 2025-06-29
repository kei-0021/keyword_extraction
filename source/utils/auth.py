import time

import streamlit as st
from utils.supabase import get_supabase_client

MAX_SESSION_DURATION = 5 * 60  # 秒単位


def restore_session():
    if "token" in st.session_state and "user" not in st.session_state:
        supabase = get_supabase_client()
        try:
            supabase.auth.set_session(st.session_state.token)  # ✅ 認証を有効にする
            user = supabase.auth.get_user().user
            if user:
                st.session_state.user = user
        except Exception:
            st.warning("セッションの復元に失敗しました。再ログインしてください。")
            st.session_state.pop("token", None)


def require_login():
    restore_session()
    login_time = st.session_state.get("login_time")
    now = time.time()
    if not st.session_state.get("user") or (
        login_time and now - login_time > MAX_SESSION_DURATION
    ):
        st.warning("セッションが切れました。再ログインしてください。")
        st.session_state.clear()
        st.stop()


def show_login():
    supabase = get_supabase_client()

    st.title("ログイン")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("ログイン"):
        try:
            result = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if result.user:
                st.session_state.user = result.user
                st.session_state.token = result.session.access_token
                st.session_state.login_time = time.time()
                supabase.auth.set_session(result.session)  # ✅ 必ずトークンを有効に
                st.rerun()
            else:
                st.error("IDとパスワードのペアが不正です。もう一度ご確認ください。")

        except Exception:
            st.error("IDとパスワードのペアが不正です。もう一度ご確認ください。")
