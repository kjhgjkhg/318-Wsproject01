"""
配置模块 - 存放所有常量配置。

此模块包含所有硬编码的常量，包括路径、文件扩展名、
分类关键词、日期格式等。禁止在代码中直接使用魔法字符串/数字。
"""

import os
from typing import Set, Dict, List


# =============================================================================
# 路径配置
# =============================================================================

# 源目录（只读扫描）- 用户图片/截图存放处
SOURCE_DIR: str = "./source_data"

# 输出目录（只写）- 用于保存报告、日志
OUTPUT_DIR: str = "./output_build"

# 整理后的子目录（在源目录下创建）
ORGANIZED_SUBDIR: str = "organized"

# 受保护文件（严禁修改）
PROTECTED_FILE: str = ".do_not_touch.cfg"


# =============================================================================
# 文件扩展名配置
# =============================================================================

# 默认支持的图片扩展名
DEFAULT_IMAGE_EXTENSIONS: Set[str] = {
    "png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff", "tif"
}

# 所有支持的图片扩展名（包含大小写）
ALL_IMAGE_EXTENSIONS: Set[str] = set()
for ext in DEFAULT_IMAGE_EXTENSIONS:
    ALL_IMAGE_EXTENSIONS.add(ext.lower())
    ALL_IMAGE_EXTENSIONS.add(ext.upper())


# =============================================================================
# 分类规则配置
# =============================================================================

# 分类关键词映射
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Screenshots": [
        "截图", "screenshot", "screen shot", "snip", "snipping",
        "capture", "captura", "截屏", "屏幕截图", "snapshot"
    ],
    "Memes": [
        "meme", "梗", "表情包", "sticker", "表情", "搞笑",
        "funny", "lol", "haha", "memes"
    ],
    "Downloads": [
        "download", "下载", "saved", "保存", "img_", "image_",
        "pic_", "photo_", "微信图片", "qq图片"
    ],
}

# 默认分类（不匹配任何关键词时）
DEFAULT_CATEGORY: str = "Other"


# =============================================================================
# 日期格式配置
# =============================================================================

# 文件夹日期格式: YYYY-MM
FOLDER_DATE_FORMAT: str = "%Y-%m"

# 报告文件名日期格式: YYYYMMDD
REPORT_DATE_FORMAT: str = "%Y%m%d"

# 报告内时间戳格式
TIMESTAMP_FORMAT: str = "%Y-%m-%d %H:%M:%S"


# =============================================================================
# 报告配置
# =============================================================================

# 报告文件前缀
REPORT_PREFIX: str = "organize_report_"

# 报告文件扩展名
REPORT_EXTENSION: str = ".txt"

# 报告分隔线长度
REPORT_LINE_WIDTH: int = 70

# 报告分隔线字符
REPORT_LINE_CHAR: str = "="


# =============================================================================
# 冲突处理配置
# =============================================================================

# 文件名冲突时的后缀格式
CONFLICT_SUFFIX_FORMAT: str = "_{counter}"

# 最大冲突尝试次数
MAX_CONFLICT_ATTEMPTS: int = 999


# =============================================================================
# 日志配置
# =============================================================================

# 日志文件前缀
LOG_PREFIX: str = "organize_log_"

# 日志文件扩展名
LOG_EXTENSION: str = ".json"


# =============================================================================
# 辅助函数
# =============================================================================

def get_source_path() -> str:
    """获取绝对路径的源目录。"""
    return os.path.abspath(SOURCE_DIR)


def get_output_path() -> str:
    """获取绝对路径的输出目录。"""
    return os.path.abspath(OUTPUT_DIR)


def get_organized_path() -> str:
    """获取整理目标目录（在源目录下的organized子目录）。"""
    return os.path.join(get_source_path(), ORGANIZED_SUBDIR)


def is_image_extension(ext: str) -> bool:
    """检查扩展名是否为支持的图片格式（不区分大小写）。"""
    return ext.lower().lstrip(".") in DEFAULT_IMAGE_EXTENSIONS


def get_all_extensions_list() -> List[str]:
    """获取所有支持的扩展名列表（小写，带点前缀）。"""
    return [f".{ext}" for ext in sorted(DEFAULT_IMAGE_EXTENSIONS)]
