"""キーワード抽出処理のメインモジュール。"""

import base64
import os
import tempfile
from collections import Counter
from typing import Optional, TypedDict, cast

import kaleido
import streamlit as st
from dotenv import load_dotenv

from src.core.csv_to_dic import (
    build_user_dic_from_csv_data,
    build_user_dic_from_local_file,
)
from src.core.plot import generate_bar_chart
from src.core.word_analyser import analyse_word
from src.services.notion_handler import fetch_good_things
from src.services.supabase_client import get_supabase_client


# 型の定義
class StopWordRow(TypedDict):
    word: str


class UserDictRow(TypedDict):
    word: str
    part_of_speech: str
    reading: str
    pronunciation: str


TOP_N = 5
DAY_LIMIT = 30


def run_keyword_extraction() -> Counter[str]:
    IS_RENDER = os.getenv("RENDER") == "true"

    notion_token: Optional[str] = None
    database_id: Optional[str] = None
    google_creds_json: Optional[str] = None

    if IS_RENDER:
        notion_token = os.getenv("NOTION_TOKEN")
        database_id = os.getenv("DATABASE_ID")

        b64_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not b64_creds:
            raise ValueError("GOOGLE_CREDENTIALS_JSON が設定されていません")

        decoded = base64.b64decode(b64_creds)
        with tempfile.NamedTemporaryFile(
            mode="w+b", delete=False, suffix=".json"
        ) as tmp:
            tmp.write(decoded)
            google_creds_json = tmp.name

        supabase = get_supabase_client()

        # ユーザーID取得の型安全化
        user_id: str = ""
        user = st.session_state.get("user")
        if user and hasattr(user, "id"):
            user_id = str(user.id)
        else:
            user_id = os.getenv("USER_ID") or ""

        # ストップワード取得
        response_sw = (
            supabase.table("stop_words").select("word").eq("user_id", user_id).execute()
        )
        sw_data = cast(
            list[StopWordRow],
            response_sw.data if isinstance(response_sw.data, list) else [],
        )
        stop_words_set = {str(item["word"]) for item in sw_data}

        # ユーザー辞書取得
        print("build_user_dic_from_db: start")
        response_ud = (
            supabase.table("user_dict")
            .select("word, part_of_speech, reading, pronunciation")
            .eq("user_id", user_id)
            .execute()
        )
        entries = cast(
            list[UserDictRow],
            response_ud.data if isinstance(response_ud.data, list) else [],
        )
        print(f"DBからユーザー辞書取得件数: {len(entries)}")

        if not entries:
            print("ユーザー辞書が空なので空ファイルを作成")
            temp_dic = tempfile.NamedTemporaryFile(delete=False, suffix=".dic")
            temp_dic.close()
            custom_dict_path = temp_dic.name
        else:
            # TypedDictにより e['word'] などのアクセスが100%安全になる
            csv_lines = [
                f"{e['word']},{e['part_of_speech']},{e['reading']},{e['pronunciation']}"
                for e in entries
            ]
            csv_data = "\n".join(csv_lines)
            custom_dict_path = build_user_dic_from_csv_data(
                csv_data, dic_dir="/usr/share/mecab/dic/ipadic"
            )

    else:
        # 開発環境
        load_dotenv(dotenv_path="config/.env")
        notion_token = os.getenv("NOTION_TOKEN")
        database_id = os.getenv("DATABASE_ID")
        google_creds_json = os.getenv("GOOGLE_CREDENTIALS_PATH")

        with open("custom_dict/stop_words.txt", encoding="utf-8") as f:
            stop_words_set = {line.strip() for line in f if line.strip()}

        custom_dict_path = "custom_dict/user.dic"
        if not os.path.exists(custom_dict_path):
            print("ユーザー辞書が見つかりません。ビルドを実行します。")
            build_user_dic_from_local_file(
                entry_csv_path="custom_dict/user_entry.csv",
                dic_dir="/usr/share/mecab/dic/ipadic",
                output_dir="custom_dict",
            )

    if not notion_token or not database_id or not google_creds_json:
        raise ValueError("環境変数が不足しています。.envファイルを確認してください。")

    all_text: str = fetch_good_things(notion_token, database_id, DAY_LIMIT)
    word_count = analyse_word(all_text, custom_dict_path, stop_words_set)
    print(word_count.most_common(TOP_N))

    if not IS_RENDER:
        fig = generate_bar_chart(word_count)
        kaleido.get_chrome_sync()
        fig.write_image("output/keyword_chart.png")
        print("グラフの出力が完了しました")

    return word_count


if __name__ == "__main__":
    run_keyword_extraction()
