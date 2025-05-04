from collections import Counter
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def connect_to_sheet(creds_path: str, sheet_name: str) -> gspread.Worksheet:
    # 認証スコープを設定
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
    ]
    # 認証情報を使ってクライアントを初期化
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)

    # 指定したスプレッドシートの最初のシートを返す
    spreadsheet = client.open(sheet_name)
    return spreadsheet.sheet1


def write_word_count(worksheet: gspread.Worksheet, word_count: Counter, top_n: int) -> None:
    # ヘッダー + データをまとめる
    rows = [["単語", "出現回数"]] + [[word, count] for word, count in word_count.most_common(top_n)]

    # 必要なセル範囲だけを更新（グラフは影響を受けない）
    end_row = top_n + 1  # ヘッダー1行 + データ行数
    cell_range = f"A1:B{end_row}"
    worksheet.update(cell_range, rows)

    # 不要な古い行を手動でクリアしたい場合（オプション）
    current_rows = len(worksheet.get_all_values())
    if current_rows > end_row:
        worksheet.batch_clear([f"A{end_row + 1}:B{current_rows}"])


