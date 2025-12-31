"""キーワード抽出処理のメインモジュール."""

import json
import os
import tempfile
from collections import Counter
from datetime import datetime
from typing import Protocol, TypedDict, cast

import kaleido
import streamlit as st
from dotenv import load_dotenv

from src.core.csv_to_dic import (
    build_user_dic_from_csv_data,
    build_user_dic_from_local_file,
)
from src.core.plot import generate_bar_chart
from src.core.word_analyser import analyse_word
from src.services import (
    fetch_good_things,
    get_supabase_client,
    save_monthly_top_keywords,
)

# --- 型定義 ---


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


# --- 定数 ---

TOP_N = 5
DAY_LIMIT = 30


def run_keyword_extraction() -> Counter[str]:
    """
    以下の手順でキーワード抽出を行う.
    1. 環境に応じた設定（Notion/Supabase/辞書）の読み込み
    2. Notionからテキストデータを取得
    3. MeCabによる構文解析とキーワードカウント
    4. 統計データの保存（本番: Supabase / 開発: ローカルJSON）
    5. 開発環境の場合はグラフをローカル出力
    """
    is_render = os.getenv("RENDER") == "true"

    # 共通変数の初期化
    notion_token: str | None = None
    database_id: str | None = None
    user_id: str = ""
    stop_words_set: set[str] = set()
    custom_dict_path: str = ""

    if is_render:
        # --- 本番環境 (Render.com) ---
        notion_token = os.getenv("NOTION_TOKEN")
        database_id = os.getenv("DATABASE_ID")

        supabase = get_supabase_client()

        # ユーザーID取得 (st.session_state から型安全に取得)
        session_user = st.session_state.get("user")
        if session_user and hasattr(session_user, "id"):
            user_id = str(cast(UserLike, session_user).id)
        else:
            user_id = os.getenv("USER_ID") or ""

        # ストップワード取得
        response_sw = (
            supabase.table("stop_words").select("word").eq("user_id", user_id).execute()
        )
        sw_list = cast(
            list[StopWordRow],
            response_sw.data if isinstance(response_sw.data, list) else [],
        )
        stop_words_set = {str(item["word"]) for item in sw_list}

        # ユーザー辞書取得
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
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dic") as tmp:
                custom_dict_path = tmp.name
        else:
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
        # --- 開発環境 (Local) ---
        load_dotenv(dotenv_path="config/.env")
        notion_token = os.getenv("NOTION_TOKEN")
        database_id = os.getenv("DATABASE_ID")
        user_id = os.getenv("USER_ID") or "dev_user"

        sw_path = "custom_dict/stop_words.txt"
        if os.path.exists(sw_path):
            with open(sw_path, encoding="utf-8") as f:
                stop_words_set = {line.strip() for line in f if line.strip()}

        custom_dict_path = "custom_dict/user.dic"
        if not os.path.exists(custom_dict_path):
            print("ユーザー辞書をビルドします...")
            build_user_dic_from_local_file(
                entry_csv_path="custom_dict/user_entry.csv",
                dic_dir="/usr/share/mecab/dic/ipadic",
                output_dir="custom_dict",
            )

    # バリデーション
    if not notion_token or not database_id:
        raise ValueError("Notion接続用の環境変数が不足しています。")

    # --- メインロジック: 解析 ---
    all_text: str = fetch_good_things(notion_token, database_id, DAY_LIMIT)
    word_count = analyse_word(all_text, custom_dict_path, stop_words_set)

    # --- 統計データの保存 ---
    if is_render:
        # 本番: Supabaseに保存
        try:
            current_supabase = get_supabase_client()
            save_monthly_top_keywords(
                supabase_client=current_supabase,
                user_id=user_id,
                word_count=word_count,
                top_n=TOP_N,
            )
        except Exception as e:
            print(f"統計保存スキップ: {e}")
    else:
        # 開発: ローカルJSONに出力
        os.makedirs("output", exist_ok=True)

        # ターゲットマンスを "YYYY-MM" 形式で取得 (例: "2025-12")
        target_month = datetime.now().strftime("%Y-%m")

        debug_data = [
            {
                "user_id": user_id,
                "target_month": target_month,
                "word": word,
                "count": count,
            }
            for word, count in word_count.most_common(TOP_N)
        ]

        # ファイル名も年月を含める (例: "output/monthly_keywords_2025-12.json")
        debug_file_name = f"monthly_keywords_{target_month}.json"
        debug_file_path = os.path.join("output", debug_file_name)

        with open(debug_file_path, "w", encoding="utf-8") as f:
            json.dump(debug_data, f, indent=4, ensure_ascii=False)

        print(f"開発環境: 統計データを {debug_file_path} に出力しました", flush=True)

    # --- 後処理 ---
    print(f"解析結果 TOP {TOP_N}: {word_count.most_common(TOP_N)}")

    if not is_render:
        # 開発環境のみグラフを画像出力
        fig = generate_bar_chart(word_count)
        kaleido.get_chrome_sync()
        os.makedirs("output", exist_ok=True)
        fig.write_image("output/keyword_chart.png")
        print("グラフ画像を output/ に出力しました")

    return word_count


if __name__ == "__main__":
    run_keyword_extraction()
