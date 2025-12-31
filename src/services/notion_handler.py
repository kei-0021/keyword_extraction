"""Notionから「良かったこと」を取得するモジュール."""

import calendar
from typing import Literal, TypedDict, cast

from notion_client import Client

# --- Notion API レスポンス用の型定義 ---


class NotionTextContent(TypedDict):
    content: str


class NotionRichText(TypedDict):
    text: NotionTextContent


class NotionProperty(TypedDict):
    rich_text: list[NotionRichText]


class NotionPage(TypedDict):
    properties: dict[str, NotionProperty]


class NotionQueryResponse(TypedDict):
    results: list[NotionPage]


# --- クエリ引数用の厳密な型定義 ---


class NotionSort(TypedDict):
    """ソート条件の型."""

    property: str
    direction: Literal["ascending", "descending"]


class NotionDateFilterCondition(TypedDict):
    """日付フィルタの具体的な条件."""

    on_or_after: str | None
    on_or_before: str | None


class NotionDateFilter(TypedDict):
    """日付プロパティに対するフィルタ."""

    property: str
    date: NotionDateFilterCondition


NotionAndFilter = TypedDict("NotionAndFilter", {"and": list[NotionDateFilter]})


# --- メイン関数 ---
def fetch_good_things(
    token: str, database_id: str, target_month: str | None = None
) -> str:
    """
    Notionから対象月(YYYY-MM)のデータを厳密に抽出。
    JSTタイムゾーンを明示することで、境界線上の5/1混入を完全に防ぐ。
    """
    client = Client(auth=token)
    sorts_list = [{"property": "日付", "direction": "descending"}]
    filter_obj = None
    page_size = 30

    if target_month:
        try:
            year_str, month_str = target_month.split("-")
            year, month = int(year_str), int(month_str)

            # 月の最終日を計算
            last_day = calendar.monthrange(year, month)[1]

            # 開始日と終了日を ISO8601 形式（日本時間 +09:00）で指定
            # これにより、Notion内部のUTC変換による1日のズレを阻止する
            start_iso = f"{year}-{month:02d}-01T00:00:00+09:00"
            end_iso = f"{year}-{month:02d}-{last_day}T23:59:59+09:00"

            filter_obj = {
                "and": [
                    {"property": "日付", "date": {"on_or_after": start_iso}},
                    {"property": "日付", "date": {"on_or_before": end_iso}},
                ]
            }
            page_size = 100
        except ValueError as e:
            raise ValueError(f"target_month形式不正(YYYY-MM): {target_month}") from e

    # クエリパラメータ構築
    query_params = {
        "database_id": database_id,
        "sorts": sorts_list,
        "page_size": page_size,
    }
    if filter_obj:
        query_params["filter"] = filter_obj

    # クエリ実行
    response_data = client.databases.query(**query_params)

    # 型キャスト (Anyを使わず Pylance を黙らせる)
    response = cast(NotionQueryResponse, response_data)

    all_good_things: list[str] = []
    for result in response["results"]:
        props = result["properties"]

        # 抽出対象のキー
        target_keys = ["良かったこと１", "良かったこと２", "良かったこと３"]
        combined_row_texts: list[str] = []

        for key in target_keys:
            if key in props:
                # _extract_text に渡す前に型安全なリストを渡す
                text_list = props[key].get("rich_text", [])
                combined_row_texts.append(_extract_text(text_list))

        all_good_things.append(" ".join(combined_row_texts))

    return " ".join(all_good_things)


def _extract_text(rich_text_array: list) -> str:
    """rich_textプロパティからプレーンテキストを抽出する補助関数."""
    if not rich_text_array:
        return ""
    return "".join([rt.get("plain_text", "") for rt in rich_text_array])
