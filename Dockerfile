# ベースイメージ（必要なPythonバージョンに合わせて変更可）
FROM python:3.11-slim

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    mecab \
    mecab-ipadic-utf8 \
    mecab-utils \
    libmecab-dev \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを作成
WORKDIR /app

# ソースコードをコピー
COPY . /app

# 必要なPythonパッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# MeCab 設定ファイルのリンク（必要に応じて）
RUN ln -sf /usr/lib/x86_64-linux-gnu/mecab/mecabrc /usr/local/etc/mecabrc

# ポート（Streamlit のデフォルトポート）
EXPOSE 8501

# アプリ起動コマンド（例：Streamlit の場合）
CMD ["bash", "-c", "PYTHONPATH=/app streamlit run src/app.py --server.port=8501 --server.address=0.0.0.0"]
