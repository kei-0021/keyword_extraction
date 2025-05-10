# keyword_extraction

## ユーザー辞書の登録手順

1. `custom_dict/user_entry.csv` に登録したい単語を **1行ずつ** 記入します。  
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
- user_entry.csv を元に MeCab 形式の user.csv を生成
- mecab-dict-index を使って user.csv を user.dic に変換

4. 正常に処理されると、custom_dict/user.dic が生成されます。これは MeCab/Fugashi での形態素解析に使用されます。