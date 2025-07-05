"""plotlyを使用して、頻出単語の棒グラフを生成するモジュール."""

import datetime
from collections import Counter

import pandas as pd
import plotly.express as px
import pytz
from plotly.graph_objects import Figure


def generate_bar_chart(
    word_count: Counter, TOP_N: int = 5, DAY_LIMIT: int = 30
) -> Figure:
    df = pd.DataFrame(word_count.most_common(TOP_N), columns=["単語", "出現回数"])

    # 今日の日付と30日前の日付を計算
    jst = pytz.timezone("Asia/Tokyo")
    now_jst = datetime.datetime.now(jst).date()
    end_date = now_jst
    start_date = end_date - datetime.timedelta(days=DAY_LIMIT)

    # Plotlyで棒グラフ作成
    fig = px.bar(
        df,
        x="単語",
        y="出現回数",
        color_discrete_sequence=["#63D194"],  # ミントグリーン
        title="過去一ヶ月における頻出単語とその出現回数",
    )

    fig.update_layout(
        font=dict(
            family="Noto Sans CJK JP",
            size=16,
        ),
        xaxis_title=None,
        yaxis_title="出現回数",
        xaxis_tickangle=0,
        width=700,
        height=400,
    )

    # ここで注釈を追加
    fig.add_annotation(
        text=f"データ期間: {start_date.strftime('%Y年%m月%d日')} ~ {end_date.strftime('%Y年%m月%d日')}",
        xref="paper",
        yref="paper",
        x=1,
        y=-0.25,
        showarrow=False,
        font=dict(size=12, color="gray"),
        align="right",
    )

    return fig
