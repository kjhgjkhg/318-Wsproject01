"""
辅助工具模块 - 提供文件属性获取、报告格式化、日志写入等功能。

此模块包含所有与文件系统交互、格式化输出、日志记录相关的工具函数。
所有函数都是纯函数或具有明确副作用的工具函数。
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from utils.config import (
    TIMESTAMP_FORMAT,
    FOLDER_DATE_FORMAT,
    REPORT_DATE_FORMAT,
    REPORT_PREFIX,
    REPORT_EXTENSION,
    LOG_PREFIX,
    LOG_EXTENSION,
    REPORT_LINE_WIDTH,
    REPORT_LINE_CHAR,
    CATEGORY_KEYWORDS,
    DEFAULT_CATEGORY,
    get_output_path,
)


# =============================================================================
# 文件属性获取
# =============================================================================

def get_file_modification_date(filepath: str) -> Optional[datetime]:
    """
    获取文件的最后修改时间。
    
    Args:
        filepath: 文件路径
        
    Returns:
        datetime对象，如果失败返回None
    """
    try:
        if not os.path.exists(filepath):
            return None
        mtime = os.path.getmtime(filepath)
        return datetime.fromtimestamp(mtime)
    except (OSError, IOError, PermissionError):
        return None


def get_file_size(filepath: str) -> Optional[int]:
    """
    获取文件大小（字节）。
    
    Args:
        filepath: 文件路径
        
    Returns:
        文件大小（字节），如果失败返回None
    """
    try:
        if not os.path.exists(filepath):
            return None
        return os.path.getsize(filepath)
    except (OSError, IOError, PermissionError):
        return None


def format_file_size(size_bytes: Optional[int]) -> str:
    """
    将字节大小格式化为人类可读字符串。
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化后的字符串（如 "1.5 MB"）
    """
    if size_bytes is None:
        return "Unknown"
    
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名（小写，不带点）。
    
    Args:
        filename: 文件名
        
    Returns:
        小写扩展名（不带点）
    """
    _, ext = os.path.splitext(filename)
    return ext.lstrip(".").lower()


# =============================================================================
# 文件分类判断
# =============================================================================

def classify_file_by_name(filename: str) -> str:
    """
    根据文件名判断文件分类。
    
    Args:
        filename: 文件名（不含路径）
        
    Returns:
        分类名称（Screenshots/Memes/Downloads/Other）
    """
    filename_lower = filename.lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in filename_lower:
                return category
    
    return DEFAULT_CATEGORY


# =============================================================================
# 日期格式化
# =============================================================================

def format_date_for_folder(dt: Optional[datetime]) -> str:
    """
    将日期格式化为文件夹名称格式（YYYY-MM）。
    
    Args:
        dt: datetime对象
        
    Returns:
        格式化后的日期字符串
    """
    if dt is None:
        return "Unknown"
    return dt.strftime(FOLDER_DATE_FORMAT)


def format_date_for_report_filename() -> str:
    """
    生成报告文件名中的日期部分（YYYYMMDD）。
    
    Returns:
        日期字符串
    """
    return datetime.now().strftime(REPORT_DATE_FORMAT)


def format_timestamp() -> str:
    """
    生成当前时间戳字符串。
    
    Returns:
        时间戳字符串
    """
    return datetime.now().strftime(TIMESTAMP_FORMAT)


# =============================================================================
# 报告格式化
# =============================================================================

def create_separator(char: str = REPORT_LINE_CHAR, width: int = REPORT_LINE_WIDTH) -> str:
    """
    创建分隔线。
    
    Args:
        char: 分隔线字符
        width: 分隔线宽度
        
    Returns:
        分隔线字符串
    """
    return char * width


def format_report_header(title: str) -> str:
    """
    格式化报告头部。
    
    Args:
        title: 报告标题
        
    Returns:
        格式化后的头部字符串
    """
    lines = [
        create_separator(),
        title.center(REPORT_LINE_WIDTH),
        create_separator(),
        f"Generated: {format_timestamp()}",
        create_separator("-"),
        "",
    ]
    return "\n".join(lines)


def format_report_footer(total_files: int, success_count: int, fail_count: int) -> str:
    """
    格式化报告尾部。
    
    Args:
        total_files: 总文件数
        success_count: 成功数
        fail_count: 失败数
        
    Returns:
        格式化后的尾部字符串
    """
    lines = [
        "",
        create_separator("-"),
        "SUMMARY",
        create_separator("-"),
        f"Total Files:    {total_files}",
        f"Successful:     {success_count}",
        f"Failed:         {fail_count}",
        f"Success Rate:   {(success_count/total_files*100 if total_files > 0 else 0):.1f}%",
        create_separator(),
    ]
    return "\n".join(lines)


def format_file_entry(
    index: int,
    old_path: str,
    new_path: str,
    file_size: Optional[int],
    status: str = "PENDING"
) -> str:
    """
    格式化单个文件条目。
    
    Args:
        index: 序号
        old_path: 原路径
        new_path: 新路径
        file_size: 文件大小
        status: 状态
        
    Returns:
        格式化后的条目字符串
    """
    old_name = os.path.basename(old_path)
    new_dir = os.path.dirname(new_path)
    size_str = format_file_size(file_size)
    
    lines = [
        f"[{index:03d}] {status}",
        f"      File:     {old_name}",
        f"      Size:     {size_str}",
        f"      From:     {old_path}",
        f"      To:       {new_dir}/",
        "",
    ]
    return "\n".join(lines)


def format_error_entry(index: int, filepath: str, error_msg: str) -> str:
    """
    格式化错误条目。
    
    Args:
        index: 序号
        filepath: 文件路径
        error_msg: 错误信息
        
    Returns:
        格式化后的错误条目字符串
    """
    filename = os.path.basename(filepath)
    lines = [
        f"[{index:03d}] ERROR",
        f"      File:     {filename}",
        f"      Path:     {filepath}",
        f"      Error:    {error_msg}",
        "",
    ]
    return "\n".join(lines)


# =============================================================================
# 报告文件写入
# =============================================================================

def generate_report_filename() -> str:
    """
    生成报告文件名。
    
    Returns:
        完整的报告文件路径
    """
    date_str = format_date_for_report_filename()
    filename = f"{REPORT_PREFIX}{date_str}{REPORT_EXTENSION}"
    return os.path.join(get_output_path(), filename)


def ensure_output_dir() -> bool:
    """
    确保输出目录存在。
    
    Returns:
        是否成功创建或已存在
    """
    try:
        output_path = get_output_path()
        if not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def write_report(content: str, filepath: Optional[str] = None) -> Tuple[bool, str]:
    """
    写入报告文件。
    
    Args:
        content: 报告内容
        filepath: 指定文件路径，None则自动生成
        
    Returns:
        (是否成功, 文件路径或错误信息)
    """
    if not ensure_output_dir():
        return False, "Failed to create output directory"
    
    if filepath is None:
        filepath = generate_report_filename()
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True, filepath
    except (OSError, IOError, PermissionError) as e:
        return False, str(e)


# =============================================================================
# 日志写入（JSON格式）
# =============================================================================

def generate_log_filename() -> str:
    """
    生成日志文件名。
    
    Returns:
        完整的日志文件路径
    """
    date_str = format_date_for_report_filename()
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"{LOG_PREFIX}{date_str}_{timestamp}{LOG_EXTENSION}"
    return os.path.join(get_output_path(), filename)


def write_json_log(data: Dict[str, Any], filepath: Optional[str] = None) -> Tuple[bool, str]:
    """
    写入JSON格式日志。
    
    Args:
        data: 要记录的数据字典
        filepath: 指定文件路径，None则自动生成
        
    Returns:
        (是否成功, 文件路径或错误信息)
    """
    if not ensure_output_dir():
        return False, "Failed to create output directory"
    
    if filepath is None:
        filepath = generate_log_filename()
    
    try:
        # 添加时间戳
        log_data = {
            "timestamp": format_timestamp(),
            **data
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        return True, filepath
    except (OSError, IOError, PermissionError, TypeError) as e:
        return False, str(e)


# =============================================================================
# 路径处理
# =============================================================================

def sanitize_filename(filename: str) -> str:
    """
    清理文件名中的非法字符。
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # Windows非法字符: < > : " / \ | ? *
    illegal_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(illegal_chars, "_", filename)
    # 去除首尾空格和点
    sanitized = sanitized.strip(" .")
    # 如果为空，返回默认名
    if not sanitized:
        return "unnamed"
    return sanitized


def get_unique_filename(directory: str, filename: str, counter: int = 0) -> str:
    """
    生成唯一的文件路径（处理重名）。
    
    Args:
        directory: 目标目录
        filename: 原始文件名
        counter: 计数器（0表示第一次尝试）
        
    Returns:
        唯一的文件路径
    """
    if counter == 0:
        full_path = os.path.join(directory, filename)
    else:
        name, ext = os.path.splitext(filename)
        new_name = f"{name}_{counter}{ext}"
        full_path = os.path.join(directory, new_name)
    
    return full_path


def is_safe_path(base_path: str, target_path: str) -> bool:
    """
    检查目标路径是否在基础路径之下（防止目录遍历）。
    
    Args:
        base_path: 基础路径
        target_path: 目标路径
        
    Returns:
        是否安全
    """
    try:
        base_abs = os.path.abspath(os.path.normpath(base_path))
        target_abs = os.path.abspath(os.path.normpath(target_path))
        # 确保目标路径以基础路径开头
        return target_abs.startswith(base_abs + os.sep) or target_abs == base_abs
    except (OSError, ValueError):
        return False
