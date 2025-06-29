import base64
import os
import tempfile
from collections import Counter

import streamlit as st
from dotenv import load_dotenv
from notion_handler import fetch_good_things
from sheets_writer import connect_to_sheet, write_word_count
from utils.supabase import get_supabase_client
from word_analyser import analyse_word

TOP_N = 5  # 頻出単語の上位から数えて何個を表示するか
DAY_LINIT = 30  # 過去何日分のデータを取得するか


def main() -> Counter:
    if os.getenv("RENDER") == "true":
        # Render環境（環境変数から取得し、jsonを一時ファイルに保存）
        NOTION_TOKEN = os.getenv("NOTION_TOKEN")
        DATABASE_ID = os.getenv("DATABASE_ID")

        b64_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not b64_creds:
            raise ValueError("GOOGLE_CREDENTIALS_JSON が設定されていません")

        decoded = base64.b64decode(b64_creds)
        with tempfile.NamedTemporaryFile(
            mode="w+b", delete=False, suffix=".json"
        ) as tmp:
            tmp.write(decoded)
            GOOGLE_CREDENTIALS_JSON = tmp.name  # 👈 tempファイルのパスをセット
    else:
        # ローカル開発環境（.envファイルから読み込み）
        load_dotenv(dotenv_path="config/.env")
        NOTION_TOKEN = os.getenv("NOTION_TOKEN")
        DATABASE_ID = os.getenv("DATABASE_ID")
        GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_PATH")

    supabase = get_supabase_client()

    # 必須の環境変数が揃っているか確認
    if not all([NOTION_TOKEN, DATABASE_ID, GOOGLE_CREDENTIALS_JSON]):
        raise ValueError("環境変数が不足しています。.envファイルを確認してください。")

    # Notionから「良かったこと1〜3」のテキストを抽出・結合
    all_text: str = fetch_good_things(NOTION_TOKEN, DATABASE_ID, DAY_LINIT)

    # supabaseデータベースからストップワードを取得
    user_id = st.session_state.user.id
    response = (
        supabase.table("stop_words").select("word").eq("user_id", user_id).execute()
    )

    stop_words_set: set[str] = set(item["word"] for item in response.data)

    # 単語の出現頻度を解析
    word_count: Counter = analyse_word(all_text, "custom_dict/user.dic", stop_words_set)

    # Google Sheetsに接続（指定したスプレッドシート名を開く）
    worksheet = connect_to_sheet(GOOGLE_CREDENTIALS_JSON, "Keyword Extraction")

    # 頻出単語とその出現回数をスプレッドシートに書き込む
    write_word_count(worksheet, word_count, TOP_N)

    return word_count
