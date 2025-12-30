"""キーワード抽出処理のメインモジュール."""

import os
import tempfile
from collections import Counter
from typing import Protocol, TypedDict, cast

import kaleido
import streamlit as st
from dotenv import load_dotenv

from src.core import (
    analyse_word,
    build_user_dic_from_csv_data,
    build_user_dic_from_local_file,
    generate_bar_chart,
)
from src.services import fetch_good_things, get_supabase_client


# 型の定義
class StopWordRow(TypedDict):
    """ストップワードテーブルのレコード構造."""

    word: str


class UserDictRow(TypedDict):
    """ユーザー辞書テーブルのレコード構造."""

    word: str
    part_of_speech: str
    reading: str
    pronunciation: str


class UserLike(Protocol):
    """Supabase Userオブジェクトの最小要件を定義するプロトコル."""

    id: str | int


TOP_N = 5
DAY_LIMIT = 30


def run_keyword_extraction() -> Counter[str]:
    """
    以下の手順でキーワード抽出を行う.
    1. 環境に応じた設定（Notion/Supabase/辞書）の読み込み
    2. Notionからテキストデータを取得
    3. MeCabによる構文解析とキーワードカウント
    4. 開発環境の場合はグラフをローカル出力
    """
    is_render = os.getenv("RENDER") == "true"

    # Notion設定の初期化
    notion_token: str | None = None
    database_id: str | None = None

    if is_render:
        # 本番環境 (Render.com等)
        notion_token = os.getenv("NOTION_TOKEN")
        database_id = os.getenv("DATABASE_ID")

        supabase = get_supabase_client()

        # ユーザーID取得 (st.session_state から型安全に取得)
        user_id: str = ""
        session_user = st.session_state.get("user")

        if session_user and hasattr(session_user, "id"):
            user_id = str(cast(UserLike, session_user).id)
        else:
            user_id = os.getenv("USER_ID") or ""

        # ストップワード取得と集合化
        response_sw = (
            supabase.table("stop_words").select("word").eq("user_id", user_id).execute()
        )
        sw_list = cast(
            list[StopWordRow],
            response_sw.data if isinstance(response_sw.data, list) else [],
        )
        stop_words_set = {str(item["word"]) for item in sw_list}

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

        if not entries:
            # 辞書が空の場合は空のファイルを生成
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dic") as tmp:
                custom_dict_path = tmp.name
        else:
            # DBのデータからMeCab用ユーザー辞書(.dic)をビルド
            csv_data = "\n".join(
                [
                    f"{e['word']},{e['part_of_speech']},{e['reading']},{e['pronunciation']}"
                    for e in entries
                ]
            )
            custom_dict_path = build_user_dic_from_csv_data(
                csv_data, dic_dir="/usr/share/mecab/dic/ipadic"
            )

    else:
        # 開発環境
        load_dotenv(dotenv_path="config/.env")
        notion_token = os.getenv("NOTION_TOKEN")
        database_id = os.getenv("DATABASE_ID")

        # ローカルファイルからストップワードを読み込み
        sw_path = "custom_dict/stop_words.txt"
        if os.path.exists(sw_path):
            with open(sw_path, encoding="utf-8") as f:
                stop_words_set = {line.strip() for line in f if line.strip()}
        else:
            stop_words_set = set()

        # ローカルのユーザー辞書を確認・ビルド
        custom_dict_path = "custom_dict/user.dic"
        if not os.path.exists(custom_dict_path):
            print("ユーザー辞書が見つかりません。ビルドを実行します。")
            build_user_dic_from_local_file(
                entry_csv_path="custom_dict/user_entry.csv",
                dic_dir="/usr/share/mecab/dic/ipadic",
                output_dir="custom_dict",
            )

    # 最終的なバリデーション
    if not notion_token or not database_id:
        raise ValueError("Notion接続用の環境変数が不足しています。")

    # メインロジック
    all_text: str = fetch_good_things(notion_token, database_id, DAY_LIMIT)
    word_count = analyse_word(all_text, custom_dict_path, stop_words_set)
    print(word_count.most_common(TOP_N))

    # 開発環境のみグラフを画像として保存
    if not is_render:
        fig = generate_bar_chart(word_count)
        # Kaleidoによる画像書き出し
        kaleido.get_chrome_sync()
        os.makedirs("output", exist_ok=True)
        fig.write_image("output/keyword_chart.png")
        print("グラフの出力が完了しました")

    return word_count


if __name__ == "__main__":
    run_keyword_extraction()
