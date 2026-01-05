import json
import logging
import os
from typing import Counter, Protocol, runtime_checkable

from postgrest import SyncRequestBuilder
from postgrest.exceptions import APIError

from src.logs.logger import KELogger

_logger = logging.getLogger("keyword_logger")


@runtime_checkable
class SupabaseTable(Protocol):
    """supabase.table() が返すオブジェクトの型を定義."""

    def upsert(self, json: list[dict[str, object]]) -> "SupabaseTable": ...
    def execute(self) -> "APIResponseLike": ...


@runtime_checkable
class SupabaseClientLike(Protocol):
    """
    Client型と互換性を持たせるためのプロトコル。
    実際の Client.table は SyncRequestBuilder を返すので、それに合わせる。
    """

    def table(self, table_name: str) -> SyncRequestBuilder: ...


class APIResponseLike(Protocol):
    """execute() が返すレスポンスの最小限の構造."""

    data: list[dict[str, object]]


def save_monthly_top_keywords(
    supabase_client: SupabaseClientLike,
    user_id: str,
    target_month: str,
    word_count: Counter[str],
    top_n: int = 5,
) -> None:
    """既存の月のデータを全削除してから、TOP N のデータを新規登録する."""
    if not user_id:
        raise ValueError("user_id が空です。")

    # 1. 保存するデータのリストを作成
    data_to_insert = [
        {"user_id": user_id, "target_month": target_month, "word": word, "count": count}
        for word, count in word_count.most_common(top_n)
    ]

    if not data_to_insert:
        _logger.warning(f"保存対象のデータがありませんでした ({target_month})")
        return

    # ここから計測開始
    KELogger.start("Supabase統計保存")
    try:
        # 2. 既存のデータを削除 (そのユーザーの、その月のデータのみ)
        supabase_client.table("monthly_keywords").delete().eq("user_id", user_id).eq(
            "target_month", target_month
        ).execute()

        # 3. 新しくデータをインサート
        supabase_client.table("monthly_keywords").insert(data_to_insert).execute()

    except APIError as e:
        _logger.error(f"Supabaseへの保存に失敗しました: {e.message}")
        raise RuntimeError(f"Supabase persistence failed: {e.message}") from e
    finally:
        # 成功しても失敗しても計測終了
        KELogger.end("Supabase統計保存")


def save_monthly_top_keywords_local(
    user_id: str,
    target_month: str,
    word_count: Counter[str],
    top_n: int = 5,
    output_dir: str = "output",
) -> str:
    """解析結果をローカルのJSONファイルとして保存する."""
    os.makedirs(output_dir, exist_ok=True)

    debug_data = [
        {"user_id": user_id, "target_month": target_month, "word": w, "count": c}
        for w, c in word_count.most_common(top_n)
    ]

    file_path = os.path.join(output_dir, f"monthly_keywords_{target_month}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(debug_data, f, indent=4, ensure_ascii=False)

    return file_path
