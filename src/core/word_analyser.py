"""形態素解析を行うモジュール."""

from collections import Counter

import MeCab


def analyse_word(text: str, tagger: MeCab.Tagger, stop_words: set[str]) -> Counter[str]:
    """
    文章を形態素解析し、名詞のみを抽出して頻度カウントを行う。

    指定されたMeCab Taggerインスタンスとストップワードを考慮し、
    名詞に限定した単語の出現回数をカウントして返す。

    Args:
        text (str): 解析対象の文章。
        tagger (MeCab.Tagger): MeCabのTaggerインスタンス。
        stop_words (set[str]): 除外対象のストップワード集合。

    Returns:
        Counter[str]: 名詞ごとの出現回数を表すカウンターオブジェクト。
    """

    # 形態素解析を行い、結果を取得
    node = tagger.parseToNode(text)

    # 名詞のみを抽出
    noun_list: list[str] = []
    while node:
        features = node.feature.split(",")
        if features[0] == "名詞":
            # ストップワードに含まれず、かつ空文字でないものを抽出
            if node.surface not in stop_words and node.surface != "":
                noun_list.append(node.surface)
        node = node.next

    # 名詞のみをカウントして返す
    return Counter(noun_list)
