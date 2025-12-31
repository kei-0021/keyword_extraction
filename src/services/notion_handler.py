"""Notionから「良かったこと」を取得するモジュール."""

import calendar
from typing import Literal, TypedDict

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


def fetch_good_things(
    token: str, database_id: str, target_month: str | None = None
) -> str:
    """Notionから対象月(YYYY-MM)または最新の「良かったこと」を抽出。

    Args:
        token: Notion APIトークン
        database_id: データベースID
        target_month: 指定月(YYYY-MM)。未指定時は最新30件。

    Returns:
        スペース区切りで結合されたテキスト
    """
    client = Client(auth=token)

    sorts_list: list[NotionSort] = [{"property": "日付", "direction": "descending"}]
    filter_obj: NotionAndFilter | None = None
    page_size: int = 30

    if target_month:
        try:
            year_str, month_str = target_month.split("-")
            year, month = int(year_str), int(month_str)
            last_day = calendar.monthrange(year, month)[1]

            start_date = f"{year}-{month:02d}-01"
            end_date = f"{year}-{month:02d}-{last_day}"

            # Notion APIのdateフィルタは一つのオブジェクトにまとめるのが確実
            # また、内部の None をこの時点でパージしておく
            date_cond = {
                k: v
                for k, v in {
                    "on_or_after": start_date,
                    "on_or_before": end_date,
                }.items()
                if v is not None
            }

            filter_obj = {
                "and": [
                    {
                        "property": "日付",
                        "date": date_cond,  # type: ignore
                    }
                ]
            }
            page_size = 100
        except ValueError as e:
            raise ValueError(f"target_month形式不正(YYYY-MM): {target_month}") from e

    # クエリパラメータを構築（Noneを除外）
    query_params = {
        "database_id": database_id,
        "sorts": sorts_list,
        "filter": filter_obj,
        "page_size": page_size,
    }
    valid_params = {k: v for k, v in query_params.items() if v is not None}

    # クエリ実行
    response_data = client.databases.query(**valid_params)
    response: NotionQueryResponse = response_data  # type: ignore

    all_good_things: list[str] = []

    for result in response["results"]:
        props = result["properties"]
        combined_row_texts: list[str] = [
            _extract_text(props[key]["rich_text"])
            for key in ["良かったこと１", "良かったこと２", "良かったこと３"]
            if key in props
        ]
        all_good_things.append(" ".join(combined_row_texts))

    return " ".join(all_good_things)


def _extract_text(rich_text_array: list[NotionRichText]) -> str:
    """rich_textプロパティからプレーンテキストを抽出する."""
    return "".join([rt["text"]["content"] for rt in rich_text_array])
