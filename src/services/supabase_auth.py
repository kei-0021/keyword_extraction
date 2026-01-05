"""Supabaseでのユーザー認証を提供するモジュール."""

import logging
import time
from typing import Protocol, TypedDict, cast

import streamlit as st

from src.services.supabase_client import get_supabase_client

MAX_SESSION_DURATION = 15 * 60  # 秒単位

_logger = logging.getLogger("keyword_logger")


# 1. ユーザーオブジェクトが持つべき構造を定義（属性アクセス用）
class UserLike(Protocol):
    id: str
    email: str | None


# 2. セッションデータの構造を定義
class SessionToken(TypedDict):
    access_token: str
    refresh_token: str


def restore_session() -> None:
    """保存されたトークンを使用してSupabaseセッションを復元する。"""

    # 1. token が存在し、user が未設定の場合のみ実行
    if "token" in st.session_state and "user" not in st.session_state:
        supabase = get_supabase_client()
        try:
            session_data = cast(SessionToken, st.session_state.token)

            # トークンを取り出す
            a_token = session_data.get("access_token")
            r_token = session_data.get("refresh_token")

            if not isinstance(a_token, str) or not isinstance(r_token, str):
                raise ValueError("Incomplete or invalid session token type")

            # 認証を有効にする
            supabase.auth.set_session(
                access_token=a_token,
                refresh_token=r_token,
            )

            # ユーザー情報を取得
            response = supabase.auth.get_user()

            # gotrue.User の代わりに UserLike(Protocol) で型を絞り込む
            current_user: UserLike | None = None
            if response is not None and hasattr(response, "user"):
                current_user = cast(UserLike, response.user)

            if current_user is not None:
                st.session_state.user = current_user
            else:
                # ユーザーが取得できなかった場合の処理
                st.error("ログインセッションが切れました。再ログインしてください。")
                st.session_state.pop("token", None)
                st.stop()

        except Exception as e:
            _logger.error(f"セッション復元エラー: {e}", exc_info=True)
            st.warning("セッションの復元に失敗しました。再ログインしてください。")
            # 整合性を保つため、中途慢端なデータは削除
            st.session_state.pop("token", None)
            st.session_state.pop("user", None)


def require_login() -> None:
    """ログインを必須とし、期限切れをチェックする。"""
    restore_session()
    login_time = st.session_state.get("login_time")
    now = time.time()

    is_expired = False
    if isinstance(login_time, (int, float)):
        if now - login_time > MAX_SESSION_DURATION:
            is_expired = True

    if not st.session_state.get("user") or is_expired:
        st.warning("セッションが切れました。再ログインしてください。")
        st.session_state.clear()
        st.stop()


def show_login() -> None:
    """ログイン画面を表示し、認証処理を行う。"""
    supabase = get_supabase_client()

    st.title("ログイン")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("ログイン"):
        try:
            # ログイン実行
            result = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            # session と user の両方が存在することを確認
            if result.session and result.user:
                # 1. ユーザー情報を保存
                st.session_state.user = result.user

                # 2. トークン情報を辞書形式で保存
                token_data: SessionToken = {
                    "access_token": result.session.access_token,
                    "refresh_token": result.session.refresh_token,
                }
                st.session_state.token = token_data
                st.session_state.login_time = time.time()

                # 3. 最新のSDK仕様に合わせてトークンを個別にセット
                supabase.auth.set_session(
                    access_token=result.session.access_token,
                    refresh_token=result.session.refresh_token,
                )

                # Streamlitの再描画
                st.rerun()
            else:
                st.error("ログインに失敗しました。認証情報をご確認ください。")

        except Exception as e:
            _logger.error(f"ログイン実行エラー (Email: {email}): {e}")
            st.error("IDとパスワードのペアが不正です。もう一度ご確認ください。")
