"""CSVファイルをMeCabの辞書形式に変換するためのモジュール."""

import csv
import os
import subprocess
import tempfile


def build_user_dic_from_csv_data(csv_data: str, dic_dir: str) -> str:
    """本番用: Supabaseから取得したCSVデータからMeCab辞書を生成する."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_csv_path = os.path.join(tmpdir, "user_entry.csv")
        output_csv_path = os.path.join(tmpdir, "user.csv")

        # CSV文字列を書き出す
        with open(input_csv_path, "w", encoding="utf-8") as f:
            f.write(csv_data)

        # CSV → MeCab用CSVに変換（ヘッダーなし）
        _csv_to_dic(input_csv_path, output_csv_path, has_header=False)

        # MeCab辞書をビルド
        _build_mecab_dict(dic_dir, output_csv_path, tmpdir)

        # 辞書ファイルのパスを返す
        return os.path.join(tmpdir, "user.dic")


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
    """MeCabの辞書をビルドする."""
    try:
        subprocess.run(
            [
                "mecab-dict-index",
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
        )
    except subprocess.CalledProcessError as e:
        print("辞書のビルド中にエラーが発生しました:")
        print(e)
