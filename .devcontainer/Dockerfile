FROM python:3.11

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    sudo \
    zsh \
    mecab \
    mecab-ipadic-utf8 \
    mecab-utils \
    libmecab-dev \
    inotify-tools \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# MeCab設定ファイルのリンクを作成
RUN ln -sf /usr/lib/x86_64-linux-gnu/mecab/mecabrc /usr/local/etc/mecabrc

# vscodeユーザー作成と zsh をログインシェルに設定
RUN useradd -ms /bin/zsh vscode \
 && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# シェルを明示
ENV SHELL=/bin/zsh
ENV PATH="/usr/lib/mecab:${PATH}"

# 作業ディレクトリとユーザー設定
WORKDIR /workspace
USER vscode
