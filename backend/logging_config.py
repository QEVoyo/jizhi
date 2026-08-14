"""
统一日志配置
"""
import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s"
LOG_DATE = "%H:%M:%S"


def setup_logging(level: int = logging.INFO):
    root = logging.getLogger("jizhi")
    root.setLevel(level)
    if not root.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(level)
        h.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE))
        root.addHandler(h)
    return root


logger = setup_logging()
