"""
统一日志配置
"""
import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s"
LOG_DATE = "%H:%M:%S"


def _tolerate_unicode(stream) -> None:
    """让控制台输出不再因编码问题抛异常。

    Windows 控制台默认是 GBK(cp936)：中文能编码，但日志里的 emoji 编不了，
    logging.StreamHandler 会直接抛 UnicodeEncodeError。
    后台线程因此整个挂掉——services/video_gen.py:302 的
    `logger.info(f"🎬 视频生成 worker[{idx}] 启动")` 就是这么把视频生成 worker 打死的。

    这里保留原编码（GBK 下中文仍正常显示），只把无法编码的字符降级成 "?"，
    保证不崩。想让 emoji 也正常显示，启动前 `set PYTHONUTF8=1`。
    """
    try:
        stream.reconfigure(errors="replace")
    except Exception:
        pass  # 某些被替换过的流没有 reconfigure，忽略即可


_tolerate_unicode(sys.stdout)
_tolerate_unicode(sys.stderr)


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
