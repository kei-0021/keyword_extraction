FROM python:3.11

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    git \
    sudo \
    zsh \
    mecab \
    inotify-tools \
    libmecab-dev \
    mecab-ipadic-utf8 \
    mecab-utils \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 最初に PATH を設定
ENV PATH="/usr/lib/mecab:${PATH}"

# ここから他のコマンド
RUN echo "PATH: $PATH" && which mecab-dict-index

# ユーザー vscode を作成し、sudo 権限を付与し、ログインシェルを zsh に変更
RUN useradd -ms /bin/zsh vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR /workspace
USER vscode
