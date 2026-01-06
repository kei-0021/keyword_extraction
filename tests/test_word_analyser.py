from collections import Counter
from typing import Any

import MeCab
import pytest

from src.core.word_analyser import analyse_word


@pytest.fixture
def mecab_tagger() -> MeCab.Tagger:
    """MeCab Taggerを準備するフィクスチャ"""

    try:
        return MeCab.Tagger(
            "-r /etc/mecabrc -d /var/lib/mecab/dic/ipadic-utf8 "
            "-u tests/custom_dict/user.dic"
        )
    except RuntimeError:
        return MeCab.Tagger("")


def test_正しく名詞が抽出される(mecab_tagger: Any):
    text = "すもももももももものうち"
    stop_words = set()

    result = analyse_word(text, mecab_tagger, stop_words)
    expected = Counter({"すもも": 1, "もも": 2, "うち": 1})

    assert result == expected


def test_ストップワードが除外されていることを確認する(mecab_tagger: Any):
    text = "今日は晴れですが、明日は雨です。"
    # 「今日」や「明日」を除外対象にする
    stop_words = {"今日", "明日"}

    result = analyse_word(text, mecab_tagger, stop_words)

    # 除外した名詞は消え、それ以外の名詞が残ることを確認
    assert "今日" not in result
    assert "明日" not in result
    assert result["晴れ"] == 1
    assert result["雨"] == 1


def test_動詞や形容詞が無視されて名詞だけが残ることを確認する(mecab_tagger: Any):
    # 「青い(形容詞)」「空(名詞)」「を」「飛ぶ(動詞)」
    text = "青い空を飛ぶ"
    stop_words = set()

    result = analyse_word(text, mecab_tagger, stop_words)

    # 名詞の「空」だけがカウントされるはず
    assert "空" in result
    assert "青い" not in result
    assert "飛ぶ" not in result
    assert len(result) == 1
