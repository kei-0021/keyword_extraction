# keyword_extraction
- Webアプリケーションに対応しました。
- 開発環境でのコマンドライン処理も残しています。
- Supabaseと呼ばれるアカウント管理とDB機能を提供するサービスを用いています。
- Webアプリケーション版は 2025.7 現在非公開となっています。
- 今後、一般ユーザーの利用に対応予定です

## コマンドラインで解析
- `custom_dict`フォルダに`stop_words.txt`を置いてください。
   - こちらに除外語を登録していただけます。
- `custom_dict`フォルダに`user_entry.csv`を置いてください。
   - こちらにユーザー辞書を登録していただけます。
   - フォーマットは以下の通りです。
```
単語,品詞,読み,発音
基本情報技術者試験,名詞,キホンジョウホウギジュツシャシケン,キホンジョーホーギジュツシャシケン
```


- あらかじめプロジェクトルートに`output`フォルダを作成してください。
- 以下のコマンドで解析を実行
- `output/keyword_chart`に解析結果がグラフとして出力されます。
```
PYTHONPATH=. python3 src/core/keyword_extraction.py
```

## ローカルサーバーを立てて確認
- `Local URL: http://localhost:8501`を選択してください (2025.7 現在非公開)
```
PYTHONPATH=. python3 -m streamlit run src/app.py
```

## 本番環境
- Render上でホスティングしています
- 以下のサイトにアクセスしてください (2025.7 現在非公開)
   - https://keyword-extraction-5i0z.onrender.com/


## コード品質の担保 (開発者向け)
- 以下のコマンドで `pyright` による型チェックを行います
```
hatch run check
```
- 以下のコマンドでフォーマットを整えます
```
hatch fmt
```