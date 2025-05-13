import csv
import os
import subprocess


# CSVファイルを読み込み、辞書形式に変換して保存する関数
def csv_to_dic(input_csv: str, output_csv: str):
    with open(input_csv, "r", encoding="utf-8") as infile:
        csvreader = csv.reader(infile)
        next(csvreader)  # ヘッダー行を読み飛ばす

        with open(output_csv, "w", encoding="utf-8") as outfile:
            for row in csvreader:
                word, part_of_speech, reading, pronunciation = row
                dic_line = (
                    f"{word},0,0,0,{part_of_speech},*,{part_of_speech},*,*,*,"
                    f"{reading},{pronunciation},{pronunciation}\n"
                )
                outfile.write(dic_line)


# mecab-dict-index を使ってCSVを辞書に変換する関数
def build_mecab_dict(dic_dir: str, csv_file: str, output_dir: str):
    try:
        subprocess.run(
            [
                "mecab-dict-index",
                "-d",
                dic_dir,  # 既存の辞書ディレクトリ（例: /usr/lib/mecab/dic/ipadic）
                "-u",
                os.path.join(output_dir, "user.dic"),  # 出力ファイル名
                "-f",
                "utf-8",  # 入力の文字コード
                "-t",
                "utf-8",  # 出力の文字コード
                csv_file,
            ],
            check=True,
        )
        print("辞書ファイル(user.dic) のビルドに成功しました。")
    except subprocess.CalledProcessError as e:
        print("辞書のビルド中にエラーが発生しました:")
        print(e)


# メイン処理
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.dirname(__file__))
    input_csv = os.path.join(project_root, "..", "custom_dict", "user_entry.csv")
    output_csv = os.path.join(project_root, "..", "custom_dict", "user.csv")
    dic_dir = "/usr/share/mecab/dic/ipadic"  # ご自身の環境に合わせて修正
    output_dir = os.path.join(project_root, "..", "custom_dict")

    csv_to_dic(input_csv, output_csv)
    print(f"CSV辞書 '{output_csv}' が生成されました。")

    build_mecab_dict(dic_dir, output_csv, output_dir)
