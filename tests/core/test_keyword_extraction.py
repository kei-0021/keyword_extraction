from collections import Counter
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.core.keyword_extraction import run_keyword_extraction


# pytest拡張機能のバグがあるのでフィクスチャを使わない
# unsupported operand type(s) for +=: 'int' and 'NoneType'
def test_コマンドライン_全体処理():
    # 1. 環境変数の設定
    with patch.dict(
        "os.environ",
        {
            "RENDER": "false",
            "NOTION_TOKEN": "fake_token",
            "DATABASE_ID": "fake_db_id",
            "USER_ID": "test_user",
        },
    ):
        # 2. 必要なものをすべて一括で patch
        with (
            patch("src.core.keyword_extraction.load_dotenv"),
            patch(
                "src.core.keyword_extraction.fetch_good_things",
                return_value="テスト 良いこと",
            ),
            patch("src.core.keyword_extraction.get_supabase_client"),
            patch("src.core.keyword_extraction.get_tagger", return_value=MagicMock()),
            patch(
                "src.core.keyword_extraction.analyse_word",
                return_value=Counter({"良いこと": 1}),
            ),
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="stopword")),
            patch("src.services.save_monthly_top_keywords_local"),
            patch(
                "src.core.keyword_extraction.generate_bar_chart",
                return_value=MagicMock(),
            ),
            patch("os.makedirs"),
        ):
            # 実行
            target_month = "2025-1"
            result = run_keyword_extraction(target_month)

            # アサーション
            assert isinstance(result, Counter)
            assert result["良いこと"] == 1


def test_コマンドライン_notionのテキストが空の場合_解析処理を行わない():
    # 1. 環境変数の設定
    with patch.dict(
        "os.environ",
        {
            "RENDER": "false",
            "NOTION_TOKEN": "fake_token",
            "DATABASE_ID": "fake_db_id",
            "USER_ID": "test_user",
        },
    ):
        # 2. 必要なものをすべて一括で patch
        with (
            patch("src.core.keyword_extraction.load_dotenv"),
            # テキストを「空」にして返す
            patch("src.core.keyword_extraction.fetch_good_things", return_value=""),
            patch("src.core.keyword_extraction.get_supabase_client"),
            patch("src.core.keyword_extraction.get_tagger", return_value=MagicMock()),
            patch("src.core.keyword_extraction.analyse_word") as mock_analyse,
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="stopword")),
            patch("src.services.save_monthly_top_keywords_local"),
            patch(
                "src.core.keyword_extraction.generate_bar_chart",
                return_value=MagicMock(),
            ),
            patch("os.makedirs"),
        ):
            # 実行
            target_month = "2025-1"
            result = run_keyword_extraction(target_month)

            # アサーション
            assert len(result) == 0
            # テキストが空なので、解析処理(analyse_word)が呼ばれていないことを確認
            mock_analyse.assert_not_called()


def test_コマンドライン_環境変数がない場合_ValueError():
    # 1. os.environ を一時的に空にする（もしくは必要なキーを消す）
    # patch.dict の clear=True を使うと、環境変数が存在しない状態を完璧に作れます
    with patch.dict("os.environ", {}, clear=True):
        # 2. 依存関数のパッチ
        with (
            patch("src.core.keyword_extraction.load_dotenv"),
            # ここでは os.getenv が None を返す状態をシミュレート
            patch("os.getenv", return_value=None),
        ):
            # 実行 & アサーション
            # ValueError が発生し、かつ期待したメッセージが含まれているか
            with pytest.raises(ValueError, match="Notion環境変数が不足しています"):
                run_keyword_extraction("2025-1")


def test_コマンドライン_辞書ビルドのキャッシュ機能():
    """辞書データに変更がない場合、再ビルドされないことを確認"""

    # 1. 共通の環境設定
    env_mock = {
        "RENDER": "true",  # use_supabase を True にするため
        "NOTION_TOKEN": "fake",
        "DATABASE_ID": "fake",
        "USER_ID": "test_user",
    }

    # 2. 1回目の実行（ビルドが走るはず）
    with patch.dict("os.environ", env_mock):
        with (
            patch(
                "src.core.keyword_extraction.get_supabase_client"
            ) as mock_supabase_cls,
            patch(
                "src.core.keyword_extraction.fetch_good_things", return_value="テス卜"
            ),
            patch(
                "src.core.keyword_extraction.build_user_dic_from_csv_data",
                return_value="/tmp/fake.dic",
            ) as mock_build,
            patch("src.core.keyword_extraction.get_tagger"),
            patch(
                "src.core.keyword_extraction.analyse_word",
                return_value=Counter({"テスト": 1}),
            ),
            patch("src.core.keyword_extraction.save_monthly_top_keywords"),
            patch("os.path.exists", return_value=True),
        ):
            # mock_supabase の戻り値を設定
            mock_data = [
                {
                    "word": "単語",
                    "part_of_speech": "名詞",
                    "reading": "タンゴ",
                    "pronunciation": "タンゴ",
                }
            ]

            # 段階的に return_value を設定
            execute_mock = (
                mock_supabase_cls.return_value.table.return_value.select.return_value
            )
            execute_mock.eq.return_value.execute.return_value.data = mock_data

            # 1回目実行
            run_keyword_extraction("2025-1")
            assert mock_build.call_count == 1

            # 2回目実行（同じデータ）
            run_keyword_extraction("2025-1")

            # ビルド関数が追加で呼ばれていない（call_count が 1 のまま）ことを確認
            assert mock_build.call_count == 1


def test_ローカルサーバーを立てて正しく処理が行われる():
    pass


def test_本番環境で正しく処理が行われる():
    pass
