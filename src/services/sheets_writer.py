"""Google Sheetsに頻出単語の出現回数を記録するモジュール."""

from collections import Counter

import gspread
from google.oauth2 import service_account
from gspread import Spreadsheet, Worksheet


def connect_to_sheet(creds_path: str, sheet_name: str) -> Worksheet:
    """Google Sheetsに接続し、最初のワークシートを返す."""

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=scope
    )
    client = gspread.authorize(creds)

    # Spreadsheetとして開き、最初のWorksheetを取得
    spreadsheet: Spreadsheet = client.open(sheet_name)
    worksheet: Worksheet = spreadsheet.get_worksheet(0)

    return worksheet


def write_word_count(
    worksheet: Worksheet, word_count: Counter[str], top_n: int = 5
) -> None:
    """頻出単語の上位をスプレッドシートに書き込む."""

    # object型で定義（文字列と数値の混在を許容）
    rows: list[list[object]] = [["単語", "出現回数"]]

    for word, count in word_count.most_common(top_n):
        rows.append([word, count])

    end_row = top_n + 1
    cell_range = f"A1:B{end_row}"

    worksheet.update(values=rows, range_name=cell_range)

    # 古い行をクリア
    all_values: list[list[str]] = worksheet.get_all_values()
    current_rows = len(all_values)

    if current_rows > end_row:
        clear_range = f"A{end_row + 1}:B{current_rows}"
        worksheet.batch_clear([clear_range])
