"""CSVファイルをMeCabの辞書形式に変換するためのモジュール."""

import csv
import logging
import os
import subprocess
import tempfile

from src.logs.logger import KELogger

# 内部的な詳細ログ用
_log = logging.getLogger("keyword_logger")


def build_user_dic_from_csv_data(csv_data: str, dic_dir: str) -> str:
    """本番用: Supabaseから取得したCSVデータからMeCab辞書を生成する."""
    tmpdir = tempfile.mkdtemp()  # 削除されない一時ディレクトリ
    input_csv_path = os.path.join(tmpdir, "user_entry.csv")
    output_csv_path = os.path.join(tmpdir, "user.csv")
    user_dic_path = os.path.join(tmpdir, "user.dic")

    # CSV文字列を書き出す
    with open(input_csv_path, "w", encoding="utf-8") as f:
        f.write(csv_data)

    # CSV → MeCab用CSVに変換（ヘッダーなし）
    _csv_to_dic(input_csv_path, output_csv_path, has_header=False)

    # MeCab辞書をビルド
    _build_mecab_dict(dic_dir, output_csv_path, tmpdir)

    # 存在確認
    if not os.path.exists(user_dic_path):
        raise FileNotFoundError(f"辞書ファイルが見つかりません: {user_dic_path}")

    return user_dic_path


def build_user_dic_from_local_file(entry_csv_path: str, dic_dir: str, output_dir: str):
    """開発用: ローカルCSVファイルからMeCab辞書を生成する."""
    output_csv_path = os.path.join(output_dir, "user.csv")

    # CSV → MeCab用CSVに変換（ヘッダーあり）
    _csv_to_dic(entry_csv_path, output_csv_path, has_header=True)

    # MeCab辞書をビルド
    _build_mecab_dict(dic_dir, output_csv_path, output_dir)


def _csv_to_dic(input_csv: str, output_csv: str, has_header: bool = True):
    """MeCab形式のCSVファイルを生成する."""
    with open(input_csv, "r", encoding="utf-8") as infile:
        csvreader = csv.reader(infile)
        if has_header:
            next(csvreader)  # ヘッダーをスキップ

        with open(output_csv, "w", encoding="utf-8") as outfile:
            for row in csvreader:
                word, part_of_speech, reading, pronunciation = row
                dic_line = (
                    f"{word},0,0,0,{part_of_speech},*,{part_of_speech},*,*,*,"
                    f"{reading},{pronunciation},{pronunciation}\n"
                )
                outfile.write(dic_line)


def _build_mecab_dict(dic_dir: str, csv_file: str, output_dir: str):
    """MeCabの辞書をビルドする（KELogger 準拠版）."""

    KELogger.start("MeCab辞書ビルド")

    try:
        result = subprocess.run(
            [
                "/usr/lib/mecab/mecab-dict-index",
                "-d",
                dic_dir,
                "-u",
                os.path.join(output_dir, "user.dic"),
                "-f",
                "utf-8",
                "-t",
                "utf-8",
                csv_file,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        # 成功時はデバッグログ
        _log.debug("mecab-dict-index output: %s", result.stdout)

    except subprocess.CalledProcessError as e:
        # エラー時は詳細をしっかり記録
        _log.error("MeCab辞書のビルドに失敗しました。")
        _log.error("ExitCode: %d, Stderr: %s", e.returncode, e.stderr)
        raise

    finally:
        KELogger.end("MeCab辞書ビルド")
