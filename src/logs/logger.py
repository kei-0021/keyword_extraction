import logging
import sys
import time
from datetime import datetime, timedelta, timezone


class MyLogger:
    def __init__(self, name="keyword_logger", logfile=None, level: int = logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # root loggerに送られなくなる

        if not self.logger.hasHandlers():
            # JSTタイムゾーン設定
            JST = timezone(timedelta(hours=9))

            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
            )
            # formatterのconverterを日本時間に変更
            formatter.converter = lambda *args: datetime.now(JST).timetuple()

            # sys.stdout に直接出力
            ch = logging.StreamHandler(stream=sys.stdout)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

            if logfile:
                from logging.handlers import RotatingFileHandler

                fh = RotatingFileHandler(logfile, maxBytes=10**6, backupCount=3)
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)

        self._start_times = {}

    def debug(self, msg):
        self.logger.debug(msg)

    def start(self, label: str = "default"):
        self._start_times[label] = time.time()
        self.logger.debug(f"[{label}] 処理開始")

    def end(self, label: str = "default"):
        if label not in self._start_times:
            self.logger.warning(
                f"[{label}] 処理終了呼び出し時に開始時間が見つかりません"
            )
            return
        elapsed = time.time() - self._start_times.pop(label)
        self.logger.debug(f"[{label}] 処理終了（処理時間: {elapsed:.2f}秒）")
