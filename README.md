# keyword_extraction

## セットアップ
注: Notion、Notionインテグレーション、GCP、Google Sheetsにアクセスできる前提です

1. ルートディレクトリに`config`フォルダを作ります。
2. その中に`.env`ファイルを作り、以下の内容を貼り付けます。
```
NOTION_TOKEN = ""
DATABASE_ID = ""
GOOGLE_CREDENTIALS_PATH=config/credentials.json
```

3. 必要な項目を埋めます。**※これらの項目は厳重に管理し、公開しないようにしてください**
- `NOTION_TOKEN`はNotionインテグレーションから持ってくる
- `DATABASE_ID`はNotionインテグレーションセットアップ後にデータベースメニューから取得。
- [こちらの記事](https://qiita.com/queita02/items/17de9aa12dbb47dcef96)で画像付きで解説しています。

4. `config`フォルダの中に`credenitals.json`を配置します。**※この情報も厳重に管理し、公開しないようにしてください**
- GCPのサービスアカウントキーを取得する
- ファイル名を`credenitals.json`として配置する


## 形態素解析の実行手順

1. `source/main.py`の定数を必要であれば調整します。
```
TOP_N = 5  # 頻出単語の上位から数えて何個を表示するか
DAY_LINIT = 30  # 過去何日分のデータを取得するか
```

2. 以下のコマンドを実行します:
```
python3 source/main.py
```

3. このスクリプトは以下の処理を行います:
- Notionから「良かったこと1〜3」のテキストを抽出・結合
- 単語の出現頻度を解析
   - ユーザー辞書やストップワードの定義に従います
- 頻出単語とその出現回数をスプレッドシートに書き込む


## ユーザー辞書の登録手順

1. `custom_dict/user_entry.csv` を作ります。
2. に登録したい単語を **1行ずつ** 記入します。  
   フォーマットは以下の通りです：
```
単語,品詞,読み,発音
基本情報技術者試験,名詞,キホンジョウホウギジュツシャシケン,キホンジョーホーギジュツシャシケン
応用情報技術者試験,名詞,オウヨウジョウホウギジュツシャシケン,オウヨージョーホーギジュツシャシケン
```

2. 以下のコマンドを実行します：
```
python3 source/csv_to_dic.py
```

3. このスクリプトは以下の2つの処理を自動で行います：
- `user_entry.csv` を元に MeCab 形式の `user.csv` を生成
- `mecab-dict-index` を使って `user.csv` を `user.dic` に変換

4. 正常に処理されると、`custom_dict/user.dic` が生成されます。これは MeCab/Fugashi での形態素解析に使用されます。


## ストップワードの登録手順
 
1. `custom_dict/stop_words.csv`を作ります。
2. 登録したい単語を **1行ずつ** 記入します。 
```
あれ
これ
それ
ため
こと
ところ
ほう
よう
的
人
ん
何
日
中 
1
2
3
ケ月
(
)
...
```
