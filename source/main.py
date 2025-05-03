from notion_client import Client
from word_analyser import analyse_word
from collections import Counter


def main():
    # Notion APIのクライアントを初期化
    notion = Client(auth=NOTION_TOKEN)
    database_id = DATABASE_ID

    # データベースから「日付」プロパティで降順ソートし、30件だけ取得
    response = notion.databases.query(
        database_id=database_id,
        sorts=[
            {
                "property": "日付",
                "direction": "descending"
            }
        ],
        page_size=30
    )

    # 各ページから「良かったこと1〜3」を抽出
    all_good_things: list = []

    for result in response["results"]:
        props = result["properties"]

        good1: list = props["良かったこと１"]["rich_text"]
        good2: list = props["良かったこと２"]["rich_text"]
        good3: list = props["良かったこと３"]["rich_text"]

        # 良かったこと1〜3を空白で繋げて一つのテキストにまとめる
        all_good_things.append(extract_text(good1) + " " + extract_text(good2) + " " + extract_text(good3))

    # 良かったことのテキストをまとめて一文として抽出
    all_text: str = " ".join(all_good_things)
    
    # analyse_word() に渡して単語の出現頻度を解析
    word_count: Counter = analyse_word(all_text)

    # 結果を表示（例：出現頻度の高い単語トップ5を表示）
    print(word_count.most_common(5))


# テキストだけ取り出す（複数ブロックがある可能性あり）
def extract_text(rich_text_array) -> str:
    return "".join([rt["text"]["content"] for rt in rich_text_array])



if __name__ == "__main__":
    main()