from notion_client import Client


notion = Client(auth=NOTION_TOKEN)
database_id = DATABASE_ID

# データベースから「日付」プロパティで降順ソートし、5件だけ取得
response = notion.databases.query(
    database_id=database_id,
    sorts=[
        {
            "property": "日付",
            "direction": "descending"
        }
    ],
    page_size=5
)

# 各ページから「良かったこと1〜3」を抽出
for result in response["results"]:
    props = result["properties"]

    good1 = props["良かったこと１"]["rich_text"]
    good2 = props["良かったこと２"]["rich_text"]
    good3 = props["良かったこと３"]["rich_text"]

    # テキストだけ取り出す（複数ブロックがある可能性あり）
    def extract_text(rich_text_array):
        return "".join([rt["text"]["content"] for rt in rich_text_array])

    print("良かったこと1:", extract_text(good1))
    print("良かったこと2:", extract_text(good2))
    print("良かったこと3:", extract_text(good3))
    print("----------")
