import logging
import sys


def get_logger(appname) -> logging.Logger:
    logger = logging.getLogger(find_logger_name())
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def find_logger_name() -> str:
    frame = sys._getframe()
    name = frame.f_globals.get("__name__") or "?"
    while name == __name__:
        if frame.f_back is None:
            name = "?"
            break
        frame = frame.f_back
        name = frame.f_globals.get("__name__") or "?"
    return name
