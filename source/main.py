from collections import Counter
from dotenv import load_dotenv
from notion_client import Client
from word_analyser import analyse_word
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    # .envファイルから環境変数を読み込む
    load_dotenv(dotenv_path="config/.env")

    # 環境変数から認証情報やデータベースIDを取得
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")  # 今後GCP用で使用
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DATABASE_ID = os.getenv("DATABASE_ID")

    # Notion APIのクライアントを初期化
    notion = Client(auth=NOTION_TOKEN)

    # データベースから最新30件を「日付」降順で取得
    response = notion.databases.query(
        database_id=DATABASE_ID,
        sorts=[
            {
                "property": "日付",
                "direction": "descending"
            }
        ],
        page_size=30
    )

    all_good_things: list = []

    # 各ページから「良かったこと1〜3」を抽出・結合
    for result in response["results"]:
        props = result["properties"]
        good1: list = props["良かったこと１"]["rich_text"]
        good2: list = props["良かったこと２"]["rich_text"]
        good3: list = props["良かったこと３"]["rich_text"]

        # 空白区切りで1文にまとめてリストに追加
        combined_text = f"{extract_text(good1)} {extract_text(good2)} {extract_text(good3)}"
        all_good_things.append(combined_text)

    # 全ての良かったことを1つの文字列に結合（単語解析用）
    all_text: str = " ".join(all_good_things)
    
    # 単語の出現頻度をカウント
    word_count: Counter = analyse_word(all_text)

    # 頻出単語トップ5を表示
    print(word_count.most_common(5))


    # 認証用のスコープとサービスアカウント認証
    # Google Sheets APIのスコープ
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',  # Google Sheetsにアクセス
        'https://www.googleapis.com/auth/drive',        # Google Driveへのアクセス
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)

    # Google Sheetsにアクセス
    spreadsheet = client.open("Word Analyser")
    worksheet = spreadsheet.sheet1  # 最初のシート

    # データを書き込み（例: 頻出単語トップ5）
    def write_to_sheet(word_count):
        # ヘッダ行を追加
        worksheet.append_row(["単語", "出現回数"])
        
        # 頻出単語をシートに追加
        for word, count in word_count.most_common(5):
            worksheet.append_row([word, count])

    # これをmain()内で呼び出す
    write_to_sheet(word_count)


# Notionのrich_textプロパティからプレーンテキストを抽出する関数
def extract_text(rich_text_array) -> str:
    return "".join([rt["text"]["content"] for rt in rich_text_array])


if __name__ == "__main__":
    main()
