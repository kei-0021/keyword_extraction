import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import ClassVar


@dataclass
class KELogger:
    """JST対応ロガーの設定マネージャー。"""

    _start_times: ClassVar[dict[str, float]] = {}
    """計測開始時刻を保持する辞書."""

    @staticmethod
    def setup(level: int = logging.DEBUG):
        """ロギングライブラリ全体の設定を行う（一度だけ呼べばOK）"""
        logger = logging.getLogger("keyword_logger")
        logger.setLevel(level)
        logger.propagate = False

        if not logger.hasHandlers():
            # Streamlitの抑制
            for logger_name in list(logging.root.manager.loggerDict.keys()):
                if logger_name.startswith("streamlit"):
                    logging.getLogger(logger_name).setLevel(logging.ERROR)
            logging.getLogger("streamlit").setLevel(logging.ERROR)

            # JST設定
            jst = timezone(timedelta(hours=9))
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
            )
            formatter.converter = lambda *args: datetime.now(jst).timetuple()

            # コンソール出力
            ch = logging.StreamHandler(stream=sys.stdout)
            ch.setFormatter(formatter)
            logger.addHandler(ch)

        return logger

    @classmethod
    def start(cls, label: str = "default"):
        """計測開始。ロガーはライブラリから取得。"""
        cls._start_times[label] = time.time()
        logging.getLogger("keyword_logger").info(f"[{label}] 処理開始")

    @classmethod
    def end(cls, label: str = "default"):
        """計測終了。"""
        start_time = cls._start_times.pop(label, None)
        if start_time is None:
            return
        elapsed = time.time() - start_time
        logging.getLogger("keyword_logger").info(
            f"[{label}] 処理終了（処理時間: {elapsed:.2f}秒）"
        )
