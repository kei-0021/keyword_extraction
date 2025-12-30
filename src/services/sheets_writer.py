"""Google Sheetsに頻出単語の出現回数を記録するモジュール."""

from collections import Counter
from typing import Any, cast

import gspread
from google.oauth2 import service_account


def connect_to_sheet(creds_path: str, sheet_name: str) -> Any:
    """Google Sheetsに接続し、最初のワークシートを返す."""

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=scope
    )
    client = gspread.authorize(creds)

    # 指定したスプレッドシートの最初のシートを返す
    spreadsheet = client.open(sheet_name)

    # gspreadの内部モデルのインポートが解決できないため、Anyで戻り値を定義するか
    # get_worksheetの結果を返す。
    worksheet = spreadsheet.get_worksheet(0)

    return worksheet


def write_word_count(worksheet: Any, word_count: Counter[str], top_n: int = 5) -> None:
    """頻出単語の上位をスプレッドシートに書き込む."""

    # Pylanceの厳格な型チェックを避けるため、list[list[Any]]を明示
    rows: list[list[Any]] = [["単語", "出現回数"]]

    for word, count in word_count.most_common(top_n):
        rows.append([word, count])

    end_row = top_n + 1
    cell_range = f"A1:B{end_row}"

    # ワークシートの更新
    # Worksheet型が解決できない場合、Anyとして扱うことでメソッド呼び出しを許可
    worksheet.update(cell_range, rows)

    # 古い行をクリア
    all_values = cast(list[list[Any]], worksheet.get_all_values())
    current_rows = len(all_values)

    if current_rows > end_row:
        clear_range = f"A{end_row + 1}:B{current_rows}"
        worksheet.batch_clear([clear_range])
