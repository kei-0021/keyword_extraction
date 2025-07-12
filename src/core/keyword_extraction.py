"""キーワード抽出処理のメインモジュール。"""

import base64
import os
import tempfile
from collections import Counter

import kaleido
import MeCab
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

TOP_N = 5  # 頻出単語の上位から数えて何個を表示するか
DAY_LIMIT = 30  # 過去何日分のデータを取得するか


@st.cache_resource
def get_tagger(custom_dict_path: str) -> MeCab.Tagger:
    """MeCab Tagger をキャッシュして取得する"""
    print("🟡 MeCab.Tagger を新規生成します（キャッシュミス）")
    return MeCab.Tagger(
        f"-r /etc/mecabrc -d /var/lib/mecab/dic/ipadic-utf8 -u {custom_dict_path}"
    )


def run_keyword_extraction() -> Counter:
    """Notionデータからキーワードを抽出し、名詞頻度のカウント結果を返す。

    - Render環境かどうかで処理を切り替える
    - Supabase上のストップワードやユーザー辞書を使用
    - Render環境ではSupabaseからユーザー辞書を取得しMeCab辞書を一時生成
    - それ以外は開発環境としてローカル辞書を利用し、なければビルドする
    """

    IS_RENDER = os.getenv("RENDER") == "true"

    if IS_RENDER:
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
            GOOGLE_CREDENTIALS_JSON = tmp.name

        supabase = get_supabase_client()
        try:
            user_id = st.session_state.user.id
        except Exception:
            user_id = os.getenv("USER_ID") or ""

        # ストップワードはSupabaseから取得
        response = (
            supabase.table("stop_words").select("word").eq("user_id", user_id).execute()
        )
        stop_words_set = set(item["word"] for item in response.data)

        # ユーザー辞書をSupabaseから取得し一時ファイルでMeCab辞書生成
        print("build_user_dic_from_db: start")
        response = (
            supabase.table("user_dict")
            .select("word, part_of_speech, reading, pronunciation")
            .eq("user_id", user_id)
            .execute()
        )
        entries = response.data or []
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
                f"{e['word']},{e['part_of_speech']},{e['reading']},{e['pronunciation']}"
                for e in entries
            )
            custom_dict_path = build_user_dic_from_csv_data(
                csv_data, dic_dir="/usr/share/mecab/dic/ipadic"
            )

    else:
        # それ以外（開発環境）：.env読み込み、ローカル辞書利用
        load_dotenv(dotenv_path="config/.env")
        NOTION_TOKEN = os.getenv("NOTION_TOKEN")
        DATABASE_ID = os.getenv("DATABASE_ID")
        GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_PATH")

        # ストップワードはローカルファイルから読み込み
        with open("custom_dict/stop_words.txt", encoding="utf-8") as f:
            stop_words_set = set(line.strip() for line in f if line.strip())

        # ローカル辞書がなければビルド
        custom_dict_path = "custom_dict/user.dic"
        if not os.path.exists(custom_dict_path):
            print("ユーザー辞書が見つかりません。ビルドを実行します。")
            build_user_dic_from_local_file(
                entry_csv_path="custom_dict/user_entry.csv",
                dic_dir="/usr/share/mecab/dic/ipadic",
                output_dir="custom_dict",
            )

    # 必須の環境変数が揃っているか確認
    if not all([NOTION_TOKEN, DATABASE_ID, GOOGLE_CREDENTIALS_JSON]):
        raise ValueError("環境変数が不足しています。.envファイルを確認してください。")

    # Notionからデータ取得
    all_text: str = fetch_good_things(NOTION_TOKEN, DATABASE_ID, DAY_LIMIT)

    # Taggerをキャッシュから取得
    print("🔵 get_tagger を呼び出します")
    tagger = get_tagger(custom_dict_path)

    # 形態素解析と頻度カウント
    word_count: Counter = analyse_word(all_text, tagger, stop_words_set)
    print(word_count.most_common(TOP_N))

    # 開発時のみグラフを出力
    if not IS_RENDER:
        fig = generate_bar_chart(word_count)
        kaleido.get_chrome_sync()
        fig.write_image("output/keyword_chart.png")
        print("グラフの出力が完了しました")

    return word_count


if __name__ == "__main__":
    run_keyword_extraction()
