"""キーワード抽出処理のメインモジュール."""

import os
import tempfile
from collections import Counter
from datetime import datetime
from typing import Protocol, TypedDict, cast

import MeCab
import streamlit as st
from dotenv import load_dotenv

from src.core.csv_to_dic import (
    build_user_dic_from_csv_data,
    build_user_dic_from_local_file,
)
from src.core.plot import generate_bar_chart
from src.core.word_analyser import analyse_word
from src.logs.logger import MyLogger
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


@st.cache_resource
def get_tagger(custom_dict_path: str, _logger: MyLogger) -> MeCab.Tagger:
    """MeCab Tagger をキャッシュして取得する"""
    _logger.debug("MeCab.Tagger を新規生成します")
    return MeCab.Tagger(
        f"-r /etc/mecabrc -d /var/lib/mecab/dic/ipadic-utf8 -u {custom_dict_path}"
    )


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

    log = MyLogger()
    print(f"{'-' * 40} run_keyword_extraction {'-' * 40}")

    # --- 1. 実行月の確定 ---
    if target_month is None:
        target_month = datetime.now().strftime("%Y-%m")

    # --- 2. 実行モードの判定 ---
    is_streamlit_mode = False
    try:
        is_streamlit_mode = st.session_state.get("user") is not None
    except RuntimeError:
        is_streamlit_mode = False
    except Exception as e:
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
    dotenv_path = ""

    if not is_render:
        # カレントディレクトリに依存せず、絶対パスで.envを指定
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        dotenv_path = os.path.join(current_file_dir, "../../config/.env")
        load_dotenv(dotenv_path=dotenv_path)

        # 再取得
        notion_token = os.getenv("NOTION_TOKEN")
        database_id = os.getenv("DATABASE_ID")

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
        print("build_user_dic_from_db: start")
        response_ud = (
            supabase.table("user_dict")
            .select("word,part_of_speech,reading,pronunciation")
            .eq("user_id", user_id)
            .execute()
        )
        entries = cast(list[UserDictRow], response_ud.data or [])
        print(f"DBからユーザー辞書取得件数: {len(entries)}")

        if not entries:
            print("ユーザー辞書が空なので空ファイルを作成")
            temp_csv = tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False, suffix=".csv"
            )
            temp_csv.write("")
            temp_csv.close()

            temp_dic = tempfile.NamedTemporaryFile(delete=False, suffix=".dic")
            temp_dic.close()
            custom_dict_path = temp_dic.name
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
        # Ruff E501 回避のための切り出し
        p_info = os.path.abspath(dotenv_path) if dotenv_path else "None"
        print(f"DEBUG: dotenv_path used: {p_info}")
        raise ValueError("Notion接続用の環境変数が不足しています。")

    # --- 4. Notionからテキスト取得 ---
    print(f"{target_month=}")
    all_text = fetch_good_things(notion_token, database_id, target_month)
    print(f"{all_text=}")

    if not all_text.strip():
        print(f"対象データが空です (月: {target_month})")
        return Counter()

    # --- 5. 解析実行 ---
    log.debug("get_tagger を呼び出します")
    tagger = get_tagger(custom_dict_path, log)
    word_count = analyse_word(all_text, tagger, stop_words_set)
    log.debug(word_count.most_common(TOP_N))

    # --- 6. 統計保存 ---
    if use_supabase:
        try:
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

    # --- 7. 画像出力 ---
    if not is_render:
        log.start("グラフ出力")
        fig = generate_bar_chart(word_count, target_month)
        os.makedirs("output", exist_ok=True)
        fig.write_image(f"output/keyword_chart_{target_month}.png")
        log.end("グラフ出力")

    return word_count


if __name__ == "__main__":
    run_keyword_extraction()
