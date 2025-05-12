from collections import Counter

import MeCab


# 除外リストをファイルから読み込む
def load_stop_words(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        stop_words = set(word.strip() for word in f.readlines())
    return stop_words


# メインの処理
def analyse_word(text: str, custom_dict_path: str, stop_words_path: str) -> Counter:
    # 除外リストの読み込み
    stop_words = load_stop_words(stop_words_path)

    # MeCabインスタンスを作成
    tagger = MeCab.Tagger(
        f"-r /etc/mecabrc -d /var/lib/mecab/dic/ipadic-utf8 -u {custom_dict_path}"
    )

    # 形態素解析を行い、結果を取得
    node: MeCab.Node = tagger.parseToNode(text)

    # 名詞のみを抽出
    noun_list = []
    while node:
        features = node.feature.split(",")
        if features[0] == "名詞":
            if node.surface not in stop_words and node.surface != "":
                noun_list.append(node.surface)
        node = node.next

    # 名詞のみをカウントして返す
    return Counter(noun_list)
