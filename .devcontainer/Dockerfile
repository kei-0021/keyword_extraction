FROM python:3.11

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

RUN mkdir -p /usr/local/etc \
 && ln -sf /usr/lib/x86_64-linux-gnu/mecab/mecabrc /usr/local/etc/mecabrc

RUN useradd -ms /bin/zsh vscode \
 && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

ENV SHELL=/bin/zsh
ENV PATH="/usr/lib/mecab:${PATH}"

WORKDIR /workspace
USER vscode
