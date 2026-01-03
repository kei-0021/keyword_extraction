"""plotlyを使用して、頻出単語の棒グラフを生成するモジュール."""

import calendar
import datetime
from collections import Counter

import pandas as pd
import plotly.express as px
import pytz
from plotly.graph_objects import Figure


def generate_bar_chart(
    word_count: Counter[str], target_month: str | None = None, TOP_N: int = 5
) -> Figure:
    """頻出単語の棒グラフを生成。target_monthの有無でラベルを動的に切り替える。"""

    # データの変換
    data = [
        {"単語": word, "出現回数": count}
        for word, count in word_count.most_common(TOP_N)
    ]
    df = pd.DataFrame(data)

    # 期間ラベルの構築
    if target_month:
        # 月指定モード: その月の初日から末日まで
        y, m = map(int, target_month.split("-"))
        _, last_day = calendar.monthrange(y, m)
        start_label = f"{y}年{m:02d}月01日"
        end_label = f"{y}年{m:02d}月{last_day:02d}日"
        title_suffix = f" ({y}年{m}月)"
    else:
        # 最新モード: 実行時点の「最新データ」
        now = datetime.datetime.now(pytz.timezone("Asia/Tokyo")).date()
        start_label = "取得可能な最新"
        end_label = now.strftime("%Y年%m月%d日")
        title_suffix = " (最新データ)"

    # グラフ描画
    fig = px.bar(
        df,
        x="単語",
        y="出現回数",
        color_discrete_sequence=["#63D194"],
        title=f"頻出単語 TOP{TOP_N}{title_suffix}",
    )

    fig.update_layout(
        font=dict(family="Noto Sans CJK JP", size=16),
        xaxis_title=None,
        yaxis_title="出現回数",
        width=700,
        height=400,
    )

    # 期間の注釈を追加
    fig.add_annotation(
        text=f"データ期間: {start_label} ~ {end_label}",
        xref="paper",
        yref="paper",
        x=1,
        y=-0.25,
        showarrow=False,
        font=dict(size=12, color="gray"),
        align="right",
    )

    return fig
