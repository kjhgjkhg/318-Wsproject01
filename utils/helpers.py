"""
utils/helpers.py - 辅助函数模块

提供文件属性获取、类型判断、报告格式化、日志写入等辅助功能。
所有函数均为纯函数，无副作用。
"""
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from utils.config import (
    CATEGORY_KEYWORDS,
    DATE_FORMAT,
    OUTPUT_DIR,
    REPORT_DATE_FORMAT,
    REPORT_PREFIX,
    REPORT_SUFFIX,
    SUCCESS_LOG_FILE
)


def get_file_modified_date(file_path: str) -> str:
    """
    获取文件的修改日期，返回 YYYY-MM 格式字符串。

    Args:
        file_path: 文件完整路径

    Returns:
        格式化的日期字符串 (YYYY-MM)

    Raises:
        OSError: 文件不存在或无法访问
    """
    try:
        mtime: float = os.path.getmtime(file_path)
        mod_date: datetime = datetime.fromtimestamp(mtime)
        return mod_date.strftime(DATE_FORMAT)
    except OSError as e:
        raise OSError(f"无法获取文件修改时间: {file_path}, 错误: {e}")


def get_file_created_date(file_path: str) -> str:
    """
    获取文件的创建日期，返回 YYYY-MM 格式字符串。

    Args:
        file_path: 文件完整路径

    Returns:
        格式化的日期字符串 (YYYY-MM)
    """
    try:
        ctime: float = os.path.getctime(file_path)
        create_date: datetime = datetime.fromtimestamp(ctime)
        return create_date.strftime(DATE_FORMAT)
    except OSError as e:
        raise OSError(f"无法获取文件创建时间: {file_path}, 错误: {e}")


def get_file_category(file_name: str) -> str:
    """
    根据文件名判断文件分类。

    Args:
        file_name: 文件名（不含路径）

    Returns:
        分类名称: Screenshots, Memes, Downloads 或 Other
    """
    lower_name: str = file_name.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in lower_name:
                return category

    return "Other"


def get_file_extension(file_name: str) -> str:
    """
    获取文件扩展名（不含点号，小写）。

    Args:
        file_name: 文件名

    Returns:
        小写扩展名，无扩展名时返回空字符串
    """
    if "." in file_name:
        return file_name.rsplit(".", 1)[-1].lower()
    return ""


def format_file_size(size_bytes: int) -> str:
    """
    将字节大小格式化为人类可读字符串。

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化的大小字符串，如 "1.5 MB"
    """
    if size_bytes < 0:
        return "0 B"

    units: List[str] = ["B", "KB", "MB", "GB", "TB"]
    size: float = float(size_bytes)
    unit_index: int = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.2f} {units[unit_index]}"


def get_file_size(file_path: str) -> int:
    """
    获取文件大小（字节）。

    Args:
        file_path: 文件完整路径

    Returns:
        文件大小（字节）
    """
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def write_report(
    records: List[Dict[str, str]],
    total_count: int,
    success_count: int,
    failed_count: int,
    failed_items: List[Dict[str, str]]
) -> str:
    """
    生成并保存整理报告。

    Args:
        records: 成功整理的记录列表
        total_count: 总文件数
        success_count: 成功数
        failed_count: 失败数
        failed_items: 失败项详情

    Returns:
        报告文件完整路径
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    date_str: str = datetime.now().strftime(REPORT_DATE_FORMAT)
    report_file: str = os.path.join(
        OUTPUT_DIR, f"{REPORT_PREFIX}{date_str}{REPORT_SUFFIX}"
    )

    lines: List[str] = []

    lines.append("=" * 80)
    lines.append("图片整理报告 - Image Organization Report")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")

    lines.append("-" * 40)
    lines.append("统计摘要 / Summary")
    lines.append("-" * 40)
    lines.append(f"总文件数: {total_count}")
    lines.append(f"成功处理: {success_count}")
    lines.append(f"失败数量: {failed_count}")
    lines.append("")

    if records:
        lines.append("-" * 40)
        lines.append("处理详情 / Details")
        lines.append("-" * 40)
        lines.append(f"{'原路径':<40} -> {'新路径':<40} {'大小':<12}")
        lines.append("-" * 100)

        for record in records:
            old_path: str = record.get("old_path", "")
            new_path: str = record.get("new_path", "")
            size: str = record.get("size", "0 B")
            lines.append(f"{old_path:<40} -> {new_path:<40} {size:<12}")

        lines.append("")

    if failed_items:
        lines.append("-" * 40)
        lines.append("失败项 / Failed Items")
        lines.append("-" * 40)
        for item in failed_items:
            path: str = item.get("path", "")
            error: str = item.get("error", "未知错误")
            lines.append(f"文件: {path}")
            lines.append(f"错误: {error}")
            lines.append("-" * 40)

    lines.append("")
    lines.append("=" * 80)
    lines.append("报告结束")
    lines.append("=" * 80)

    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return report_file
    except IOError as e:
        raise IOError(f"无法写入报告文件: {report_file}, 错误: {e}")


def save_success_log(records: List[Dict[str, str]]) -> str:
    """
    保存成功整理记录到JSON日志文件。

    Args:
        records: 整理记录列表

    Returns:
        日志文件路径
    """
    import json

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log_file: str = os.path.join(OUTPUT_DIR, SUCCESS_LOG_FILE)

    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        return log_file
    except IOError as e:
        raise IOError(f"无法保存日志文件: {log_file}, 错误: {e}")


def load_success_log() -> List[Dict[str, str]]:
    """
    加载上次整理的成功记录。

    Returns:
        整理记录列表，无记录时返回空列表
    """
    import json

    log_file: str = os.path.join(OUTPUT_DIR, SUCCESS_LOG_FILE)

    if not os.path.exists(log_file):
        return []

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (IOError, json.JSONDecodeError):
        return []


def sanitize_filename(filename: str) -> str:
    """
    清理文件名中的非法字符。

    Args:
        filename: 原始文件名

    Returns:
        清理后的安全文件名
    """
    illegal_chars: str = r'[<>:"/\\|?*]'
    sanitized: str = re.sub(illegal_chars, "_", filename)
    return sanitized.strip()
