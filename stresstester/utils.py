from datetime import datetime
import re
import os
from typing import Iterable


def datetime_now_str():
    return datetime.now().strftime("%y%m%d_%H%M%S")


def is_str_truthful(s: str):
    return s.lower() in ("true", "yes", "1", "y")


def replace_unsafe_filename_chars(s: str):
    return re.sub(r'[\\/:*?"<>|\s]', '_', s)


def pick_latest_file(files: Iterable[str]):
    return max(
        files,
        key=os.path.getctime
    )


def normalize_trail_name(t):
    return t.__class__.__name__.lower()
