import datetime
from collections import Counter
from typing import Any

from src.core.plot import generate_bar_chart


def test_グラフのタイトルとラベルが正しく設定される():
    word_count = Counter({"Python": 10})
    fig = generate_bar_chart(word_count, target_month="2026-01")

    # Anyにキャストして辞書アクセス
    f: Any = fig
    assert "2026年1月" in f["layout"]["title"]["text"]
    assert "2026年01月01日" in f["layout"]["annotations"][0]["text"]


def test_最新モードで本日の日付がラベルに含まれる():
    word_count = Counter({"テスト": 1})
    fig = generate_bar_chart(word_count, target_month=None)

    # ここも Any を通さないと .layout でエラーが出る
    f: Any = fig
    today_str = datetime.datetime.now().strftime("%Y年%m月%d日")

    assert "取得可能な最新" in f["layout"]["annotations"][0]["text"]
    assert today_str in f["layout"]["annotations"][0]["text"]


def test_データの件数がTOP_Nに制限されている():
    word_count = Counter({f"word_{i}": i for i in range(10)})
    top_n = 3
    fig = generate_bar_chart(word_count, TOP_N=top_n)

    # データ部分 (fig.data) も Any 経由でアクセス
    f: Any = fig
    assert len(f["data"][0]["x"]) == top_n
    assert f["data"][0]["x"][0] == "word_9"
