from datetime import datetime
from typing import Counter, Protocol, runtime_checkable

from postgrest import SyncRequestBuilder
from postgrest.exceptions import APIError


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
    word_count: Counter[str],
    top_n: int = 5,
) -> None:
    """TOP N の単語と頻度を月次データとして Supabase に保存する."""
    if not user_id:
        raise ValueError("user_id が空です。")

    target_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")

    # TypedDict を使わずとも、ここで構造を固定
    data_to_insert = [
        {"user_id": user_id, "target_month": target_month, "word": word, "count": count}
        for word, count in word_count.most_common(top_n)
    ]

    if not data_to_insert:
        return

    try:
        # Protocol により、.table().upsert().execute() の連鎖が型安全になる
        response = (
            supabase_client.table("monthly_keywords").upsert(data_to_insert).execute()
        )

        inserted_count = len(response.data)
        print(f"Successfully saved {inserted_count} keywords.")

    except APIError as e:
        raise RuntimeError(f"Supabase persistence failed: {e.message}") from e
