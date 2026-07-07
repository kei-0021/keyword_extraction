import os
import shutil
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.core.csv_to_dic import _build_mecab_dict, _csv_to_dic


@pytest.fixture
def temp_dir():
    """テスト用の使い捨てディレクトリを作成するフィクスチャ."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


def test_MeCab形式のCSVファイルが生成できる(temp_dir: str):
    input_csv = os.path.join(temp_dir, "input.csv")
    output_csv = os.path.join(temp_dir, "output.csv")

    # テストデータ: 単語, 品詞, 読み, 発音
    with open(input_csv, "w", encoding="utf-8") as f:
        f.write("林檎,名詞,リンゴ,リンゴ\n")

    _csv_to_dic(input_csv, output_csv, has_header=False)

    with open(output_csv, "r", encoding="utf-8") as f:
        line = f.read()
        # MeCab形式: 表層形,左文脈ID,右文脈ID,コスト,品詞...
        assert line.startswith("林檎,0,0,0,名詞,*,名詞,*,*,*,リンゴ,リンゴ,リンゴ")


@patch("subprocess.run")
def test_MeCab辞書のビルドコマンドが正しく実行される(
    mock_run: MagicMock, temp_dir: str
):
    # 準備
    dic_dir = "/path/to/system/dic"
    csv_file = os.path.join(temp_dir, "user.csv")
    output_dir = temp_dir

    # ダミーのCSVファイルを作っておく（関数内で参照されるため）
    with open(csv_file, "w") as f:
        f.write("test")

    # 実行
    _build_mecab_dict(dic_dir, csv_file, output_dir)

    # 検証: subprocess.runが呼ばれたか
    assert mock_run.called

    # 検証: 渡された引数が正しいか
    args = mock_run.call_args[0][0]
    assert "/usr/lib/mecab/mecab-dict-index" in args
    assert "-d" in args
    assert dic_dir in args
    assert "-u" in args
    assert os.path.join(output_dir, "user.dic") in args


@patch("subprocess.run")
def test_ビルド失敗時に例外がスローされる(mock_run: MagicMock, temp_dir: str):
    # subprocess.run がエラー（CalledProcessError）を出すように設定
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="mecab-dict-index", stderr="error message"
    )

    # 実行して、例外が発生することを確認
    with pytest.raises(subprocess.CalledProcessError):
        _build_mecab_dict("dummy_dic", "dummy.csv", temp_dir)
