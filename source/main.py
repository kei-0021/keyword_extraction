import os
from collections import Counter

from dotenv import load_dotenv
from notion_handler import fetch_good_things
from sheets_writer import connect_to_sheet, write_word_count
from word_analyser import analyse_word

TOP_N = 5  # 頻出単語の上位から数えて何個を表示するか
DAY_LINIT = 30  # 過去何日分のデータを取得するか


def main() -> None:
    # .envファイルから環境変数を読み込む
    load_dotenv(dotenv_path="config/.env")

    # Notion APIとGoogle Sheets API用のキー情報を取得
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DATABASE_ID = os.getenv("DATABASE_ID")
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")

    # 必須の環境変数が揃っているか確認
    if not all([NOTION_TOKEN, DATABASE_ID, creds_path]):
        raise ValueError("環境変数が不足しています。.envファイルを確認してください。")

    # Notionから「良かったこと1〜3」のテキストを抽出・結合
    all_text: str = fetch_good_things(NOTION_TOKEN, DATABASE_ID, DAY_LINIT)

    # 単語の出現頻度を解析
    word_count: Counter = analyse_word(
        all_text, "custom_dict/user.dic", "custom_dict/stop_words.txt"
    )

    # 頻出単語を表示（確認用）
    print(word_count.most_common(TOP_N))

    # Google Sheetsに接続（指定したスプレッドシート名を開く）
    worksheet = connect_to_sheet(creds_path, "Keyword Extraction")

    # 頻出単語とその出現回数をスプレッドシートに書き込む
    write_word_count(worksheet, word_count, TOP_N)

    print("処理が完了しました。")


if __name__ == "__main__":
    main()
