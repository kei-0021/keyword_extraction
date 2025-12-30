"""Supabaseでのユーザー認証を提供するモジュール."""

import time
from typing import Any, cast

import streamlit as st

from src.services.supabase_client import get_supabase_client

MAX_SESSION_DURATION = 15 * 60  # 秒単位


def restore_session() -> None:
    """保存されたトークンを使用してSupabaseセッションを復元する。"""

    # 1. token が存在し、user が未設定の場合のみ実行
    if "token" in st.session_state and "user" not in st.session_state:
        supabase = get_supabase_client()
        try:
            # token の中身を辞書としてキャスト
            session_data = cast(dict[str, Any], st.session_state.token)

            # トークンを取り出す
            a_token = session_data.get("access_token")
            r_token = session_data.get("refresh_token")

            # 型ガード: 両方のトークンが文字列として存在することを保証
            if not isinstance(a_token, str) or not isinstance(r_token, str):
                raise ValueError("Incomplete or invalid session token type")

            # ✅ 認証を有効にする
            supabase.auth.set_session(
                access_token=a_token,
                refresh_token=r_token,
            )

            # ユーザー情報を取得
            response = supabase.auth.get_user()

            # --- Pylance対策の決定版 ---
            # 1. response 自体が None でないか
            # 2. response.user が None でないか
            # この2つを同時にローカル変数へ取り出しながらチェックします

            current_user = None
            if response is not None:
                current_user = response.user

            if current_user is not None:
                # このブロック内では current_user は確実に 'User' 型
                st.session_state.user = current_user
            else:
                # ユーザーが取得できなかった場合の処理
                st.error("ログインセッションが切れました。再ログインしてください。")
                st.session_state.pop("token", None)
                st.stop()
                return

        except Exception as e:
            # Pylance: 未使用の e を防ぐために print か logger を使用
            print(f"Session restoration failed: {e}")
            st.warning("セッションの復元に失敗しました。再ログインしてください。")
            # 整合性を保つため、中途半端なデータは削除
            st.session_state.pop("token", None)
            st.session_state.pop("user", None)


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
            # ログイン実行
            result = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            # Pylance対策：session と user の両方が存在することをチェック
            if result.session and result.user:
                # 1. ユーザー情報をセッションに保存
                st.session_state.user = result.user

                # 2. トークン情報を辞書形式で保存（restore_sessionで使いやすくするため）
                st.session_state.token = {
                    "access_token": result.session.access_token,
                    "refresh_token": result.session.refresh_token,
                }

                st.session_state.login_time = time.time()

                # 3. 最新のSDK仕様に合わせてトークンをセット
                # 個別に渡すことで「Argument missing」を回避します
                supabase.auth.set_session(
                    access_token=result.session.access_token,
                    refresh_token=result.session.refresh_token,
                )

                st.rerun()
            else:
                # session か user のどちらかが欠けている場合
                st.error("ログインに失敗しました。認証情報をご確認ください。")

        except Exception as e:
            st.error("IDとパスワードのペアが不正です。もう一度ご確認ください。")
            print(f"Login error: {e}")
