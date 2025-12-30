"""Notionから「良かったこと」を取得するモジュール."""

from typing import Any, cast

from notion_client import Client


def fetch_good_things(token: str, database_id: str, limit: int = 30) -> str:
    # Notion APIのクライアントを初期化
    client = Client(auth=token)

    # データベースから最新○件を「日付」降順で取得
    response = cast(
        dict[str, Any],
        client.databases.query(
            database_id=database_id,
            sorts=[{"property": "日付", "direction": "descending"}],
            page_size=limit,
        ),
    )

    all_good_things: list[str] = []

    # 各ページから「良かったこと1〜3」を抽出・結合
    for result in response["results"]:
        props = result["properties"]
        good1: list[Any] = props["良かったこと１"]["rich_text"]
        good2: list[Any] = props["良かったこと２"]["rich_text"]
        good3: list[Any] = props["良かったこと３"]["rich_text"]

        # 空白区切りで1文にまとめてリストに追加
        combined_text = (
            f"{_extract_text(good1)} {_extract_text(good2)} {_extract_text(good3)}"
        )
        all_good_things.append(combined_text)

    # 全ての良かったことを1つの文字列に結合（単語解析用）
    all_text: str = " ".join(all_good_things)

    return all_text


# Notionのrich_textプロパティからプレーンテキストを抽出する関数
def _extract_text(rich_text_array: list[Any]) -> str:
    return "".join([rt["text"]["content"] for rt in rich_text_array])
