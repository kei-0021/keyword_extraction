FROM python:3.11

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    mecab \
    mecab-ipadic-utf8 \
    mecab-utils \
    libmecab-dev \
    build-essential \
    libnss3 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    fonts-noto-cjk \
    wget \
    gnupg \
 && rm -rf /var/lib/apt/lists/*

# Google Chrome のインストール
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-linux-signing-key.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y --no-install-recommends google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを作成
WORKDIR /app

# ソースコードをコピー
COPY . /app

# 必要な Python パッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# MeCab 設定ファイルのリンク（必要に応じて）
RUN ln -sf /usr/lib/x86_64-linux-gnu/mecab/mecabrc /usr/local/etc/mecabrc

# ポート（Streamlit のデフォルトポート）
EXPOSE 8501

# アプリ起動コマンド（例：Streamlit の場合）
CMD ["bash", "-c", "PYTHONPATH=/app streamlit run src/app.py --server.port=8501 --server.address=0.0.0.0"]
