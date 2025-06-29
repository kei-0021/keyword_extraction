import base64
import os
import tempfile
from collections import Counter

import streamlit as st
from dotenv import load_dotenv

from src.core.notion_handler import fetch_good_things
from src.core.sheets_writer import connect_to_sheet, write_word_count
from src.core.word_analyser import analyse_word
from src.utils.supabase import get_supabase_client

TOP_N = 5  # 頻出単語の上位から数えて何個を表示するか
DAY_LINIT = 30  # 過去何日分のデータを取得するか


def main() -> Counter:
    IS_RENDER = os.getenv("RENDER") == "true"
    IS_DEV = not IS_RENDER  # RENDERがtrueでなければ開発環境

    if not IS_DEV:
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
        # 開発環境用設定
        load_dotenv(dotenv_path="config/.env")
        NOTION_TOKEN = os.getenv("NOTION_TOKEN")
        DATABASE_ID = os.getenv("DATABASE_ID")
        GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_PATH")

    # 必須の環境変数が揃っているか確認
    if not all([NOTION_TOKEN, DATABASE_ID, GOOGLE_CREDENTIALS_JSON]):
        raise ValueError("環境変数が不足しています。.envファイルを確認してください。")

    # Notionからデータ取得
    all_text: str = fetch_good_things(NOTION_TOKEN, DATABASE_ID, DAY_LINIT)

    if IS_DEV:
        # 開発用フォルダにある stop_words.txt を読む
        with open("custom_dict/stop_words.txt", encoding="utf-8") as f:
            stop_words_set = set(line.strip() for line in f if line.strip())
    else:
        # 本番はSupabaseから取得
        supabase = get_supabase_client()
        user_id = st.session_state.user.id
        response = (
            supabase.table("stop_words").select("word").eq("user_id", user_id).execute()
        )
        stop_words_set = set(item["word"] for item in response.data)

    # 解析処理は共通
    word_count: Counter = analyse_word(all_text, "custom_dict/user.dic", stop_words_set)

    # Google Sheets接続と書き込み
    worksheet = connect_to_sheet(GOOGLE_CREDENTIALS_JSON, "Keyword Extraction")
    write_word_count(worksheet, word_count, TOP_N)

    # 開発環境ならログに頻出単語を出力
    if IS_DEV:
        print(word_count.most_common(TOP_N))

    return word_count


if __name__ == "__main__":
    main()
