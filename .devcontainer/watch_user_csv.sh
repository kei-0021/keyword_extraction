#!/bin/bash

echo "[INFO] user.csv の変更を監視中..."

cd /custom_dict || exit 1

# 初回ビルド（あれば）
if [ -f user.csv ]; then
  echo "[INFO] 初回辞書ビルド中..."
  mecab-dict-index -d /usr/share/mecab/dic/ipadic \
    -u user.dic -f utf-8 -t utf-8 user.csv
fi

# ファイル変更のたびに辞書を再ビルド
while inotifywait -e close_write user.csv; do
  echo "[INFO] user.csv に変更がありました。辞書を再ビルドします..."
  mecab-dict-index -d /usr/share/mecab/dic/ipadic \
    -u user.dic -f utf-8 -t utf-8 user.csv
done
