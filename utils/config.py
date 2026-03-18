"""
utils/config.py - 全局配置常量模块

定义项目所需的默认路径、扩展名、分类关键词等常量。
所有路径配置集中管理，便于维护和修改。
"""
import os
from typing import Dict, List, Set

PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE_DIR: str = os.path.join(PROJECT_ROOT, "source_data")

OUTPUT_DIR: str = os.path.join(PROJECT_ROOT, "output_build")

DEFAULT_EXTENSIONS: Set[str] = {
    "png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff", "ico"
}

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Screenshots": ["截图", "screenshot", "Snip", "screen", "capture", "截屏"],
    "Memes": ["meme", "表情", "emoji", "表情包", "funny"],
    "Downloads": ["download", "下载", "saved"],
}

DATE_FORMAT: str = "%Y-%m"

REPORT_DATE_FORMAT: str = "%Y%m%d"

PROTECTED_FILE: str = ".do_not_touch.cfg"

SUCCESS_LOG_FILE: str = "last_organize_success.json"

REPORT_PREFIX: str = "organize_report_"

REPORT_SUFFIX: str = ".txt"

MAX_FILENAME_LENGTH: int = 255

CONFLICT_SUFFIX_PATTERN: str = "_{}"
