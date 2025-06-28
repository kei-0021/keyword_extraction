import os
import time

import streamlit as st
from supabase import create_client

MAX_SESSION_DURATION = 30  # 30秒（秒単位）


def require_login():
    restore_session()  # ←トークン復元ロジック（さきほどのやつ）

    login_time = st.session_state.get("login_time")
    now = time.time()
    if not st.session_state.get("user") or (
        login_time and now - login_time > MAX_SESSION_DURATION
    ):
        st.warning("セッションが切れました。再ログインしてください。")
        st.session_state.clear()
        st.stop()


def show_login():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    st.title("ログイン")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("ログイン"):
        supabase = create_client(url, key)

        try:
            result = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            if result.user:
                st.session_state.user = result.user
                st.session_state.token = (
                    result.session.access_token
                )  # 🔑 トークンを保存
                st.success("ログイン成功！")
                st.session_state.login_time = time.time()  # ⏰ ログイン時間を記録
            else:
                st.error("IDとパスワードのペアが不正です。もう一度ご確認ください。")
            if result.user:
                st.session_state.user = result.user
                st.success("ログイン成功！")
                st.rerun()  # 🔁 ここでログイン後の画面に切り替える！
        except Exception:
            # ここで特定の認証エラーならカスタムメッセージに置き換えるのも良い
            st.error("IDとパスワードのペアが不正です。もう一度ご確認ください。")


def restore_session():
    """保持されたセッション情報を復元するための関数."""
    if "token" in st.session_state and "user" not in st.session_state:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        supabase = create_client(url, key)
        try:
            user = supabase.auth.get_user(st.session_state.token).user
            if user:
                st.session_state.user = user
        except Exception:
            st.warning("セッションの復元に失敗しました。再ログインしてください。")
            st.session_state.pop("token", None)
