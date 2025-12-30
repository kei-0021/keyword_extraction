"""各種バックエンド処理を行うためのパッケージ."""

from src.core.csv_to_dic import (
    build_user_dic_from_csv_data,
    build_user_dic_from_local_file,
)
from src.core.keyword_extraction import run_keyword_extraction
from src.core.plot import generate_bar_chart
from src.core.word_analyser import analyse_word
from src.services import fetch_good_things, get_supabase_client

__all__ = [
    "run_keyword_extraction",
    "generate_bar_chart",
    "build_user_dic_from_csv_data",
    "build_user_dic_from_local_file",
    "analyse_word",
    "fetch_good_things",
    "get_supabase_client",
]
