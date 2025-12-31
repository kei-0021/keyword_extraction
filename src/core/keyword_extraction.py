"""キーワード抽出処理のメインモジュール."""

import os
import tempfile
from collections import Counter
from datetime import datetime
from typing import Protocol, TypedDict, cast

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


def run_keyword_extraction(target_month: str | None = None) -> Counter[str]:
    """
    以下の手順でキーワード抽出を行う.
    1. 実行月の確定（Noneなら今月）
    2. 環境に応じた設定（Notion/Supabase/辞書）の読み込み
    3. Notionから指定月のテキストデータを取得
    4. MeCabによる構文解析とキーワードカウント
    5. 統計データの保存（Supabase / ローカル）
    6. 画像出力（ローカル環境のみ）
    """

    # --- 1. 実行月の確定 ---
    # ここで月を固定することで、取得(Notion)と保存(Supabase)の月がズレるのを防ぐ
    if target_month is None:
        target_month = datetime.now().strftime("%Y-%m")

    # --- 2. 実行モードの判定 ---
    is_streamlit_mode = False
    try:
        # st.session_state へのアクセスで発生し得る RuntimeError に限定してキャッチ
        is_streamlit_mode = st.session_state.get("user") is not None
    except RuntimeError:
        # Streamlit のコンテキスト外（CLI実行時など）
        is_streamlit_mode = False
    except Exception as e:
        # それ以外の未知の例外はログに出すか、再送出する
        print(f"Unexpected error: {e}")
        is_streamlit_mode = False
    is_render = os.getenv("RENDER") == "true"
    use_supabase = is_render or is_streamlit_mode

    # 共通変数の初期化
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("DATABASE_ID")
    user_id = ""
    stop_words_set: set[str] = set()
    custom_dict_path = ""

    if not is_render:
        load_dotenv(dotenv_path="config/.env")

    # --- 3. 辞書とストップワードの準備 ---
    if use_supabase:
        supabase = get_supabase_client()
        session_user = st.session_state.get("user")
        user_id = (
            str(session_user.id)
            if session_user
            else (os.getenv("USER_ID") or "unknown")
        )

        # ストップワード取得
        response_sw = (
            supabase.table("stop_words").select("word").eq("user_id", user_id).execute()
        )
        sw_list = cast(list[StopWordRow], response_sw.data or [])
        stop_words_set = {str(item["word"]) for item in sw_list}

        # ユーザー辞書取得
        response_ud = (
            supabase.table("user_dict")
            .select("word,part_of_speech,reading,pronunciation")
            .eq("user_id", user_id)
            .execute()
        )
        entries = cast(list[UserDictRow], response_ud.data or [])

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
        # ローカルファイルモード
        user_id = os.getenv("USER_ID") or "dev_user"
        sw_path = "custom_dict/stop_words.txt"
        if os.path.exists(sw_path):
            with open(sw_path, encoding="utf-8") as f:
                stop_words_set = {line.strip() for line in f if line.strip()}

        custom_dict_path = "custom_dict/user.dic"
        if not os.path.exists(custom_dict_path):
            build_user_dic_from_local_file(
                "custom_dict/user_entry.csv",
                "/usr/share/mecab/dic/ipadic",
                "custom_dict",
            )

    if not notion_token or not database_id:
        raise ValueError("Notion接続用の環境変数が不足しています。")

    # --- 4. Notionからテキスト取得 ---
    # target_monthが確実に渡るため、fetch_good_things内のfilterが正しく作動する
    print(f"{target_month=}")
    all_text = fetch_good_things(notion_token, database_id, target_month)
    print(f"{all_text=}")

    if not all_text.strip():
        print(f"対象データが空です (月: {target_month})")
        return Counter()

    # --- 5. 解析実行 ---
    word_count = analyse_word(all_text, custom_dict_path, stop_words_set)

    # --- 6. 統計保存 ---
    if use_supabase:
        try:
            # 修正した「全削除してから登録」の関数を呼ぶ
            save_monthly_top_keywords(
                supabase_client=get_supabase_client(),
                user_id=user_id,
                target_month=target_month,
                word_count=word_count,
                top_n=TOP_N,
            )
        except Exception as e:
            if is_streamlit_mode:
                st.error(f"Supabaseへの保存に失敗しました: {e}")
            else:
                print(f"Supabaseへの保存に失敗しました: {e}")
    else:
        from src.services import save_monthly_top_keywords_local

        save_monthly_top_keywords_local(user_id, target_month, word_count, TOP_N)

    # --- 7. 画像出力 (CLI実行またはローカルサーバー時のみ) ---
    if not is_render:
        fig = generate_bar_chart(word_count, target_month)
        os.makedirs("output", exist_ok=True)
        fig.write_image(f"output/keyword_chart_{target_month}.png")

    return word_count
