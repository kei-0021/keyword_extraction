from janome.tokenizer import Tokenizer
from collections import Counter

# ストップワードリスト
STOPWORDS = {
    "する", "なる", "こと", "もの", "いる", "ある", "それ", "これ", "や", "と", "の", "で", "な", "なっ", "た", "です", "ます", "できる", "的", "よう", "(", ")", "者"
}

tokenizer = Tokenizer()

def analyse_word(your_data: str) -> Counter:
    # トークン化
    tokens: list = [
        token.base_form for token in tokenizer.tokenize(your_data)
        if token.part_of_speech.split(',')[0] in ['名詞'] and token.base_form not in STOPWORDS
    ]

    # 頻度カウント
    return Counter(tokens)
