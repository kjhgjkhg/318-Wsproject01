"""
utils/validators.py - 输入校验模块

提供路径存在校验、扩展名合法性校验、用户确认校验等功能。
所有校验函数返回布尔值或抛出明确异常。
"""
import os
from typing import List, Optional, Set

from utils.config import DEFAULT_EXTENSIONS, PROTECTED_FILE, SOURCE_DIR


def validate_path_exists(path: str, must_be_dir: bool = False) -> bool:
    """
    校验路径是否存在。

    Args:
        path: 待校验的路径
        must_be_dir: 是否必须为目录

    Returns:
        路径存在返回 True

    Raises:
        FileNotFoundError: 路径不存在
        ValueError: 路径不是目录（当 must_be_dir=True 时）
    """
    if not path:
        raise ValueError("路径不能为空")

    if not os.path.exists(path):
        raise FileNotFoundError(f"路径不存在: {path}")

    if must_be_dir and not os.path.isdir(path):
        raise ValueError(f"路径不是目录: {path}")

    return True


def validate_extensions(extensions: Optional[List[str]]) -> Set[str]:
    """
    校验并规范化扩展名列表。

    Args:
        extensions: 用户提供的扩展名列表，None 时使用默认值

    Returns:
        规范化的小写扩展名集合
    """
    if extensions is None or len(extensions) == 0:
        return DEFAULT_EXTENSIONS.copy()

    normalized: Set[str] = set()
    for ext in extensions:
        clean_ext: str = ext.strip().lower().lstrip(".")
        if clean_ext:
            normalized.add(clean_ext)

    if not normalized:
        return DEFAULT_EXTENSIONS.copy()

    return normalized


def validate_yes_confirmation(user_input: str) -> bool:
    """
    校验用户确认输入。

    Args:
        user_input: 用户输入字符串

    Returns:
        用户确认返回 True，否则返回 False
    """
    if not user_input:
        return False

    normalized: str = user_input.strip().lower()
    return normalized in ("y", "yes", "是", "确认")


def validate_source_directory(source_dir: str) -> bool:
    """
    校验源目录是否合法且可读。

    Args:
        source_dir: 源目录路径

    Returns:
        合法返回 True

    Raises:
        FileNotFoundError: 目录不存在
        PermissionError: 无读取权限
    """
    validate_path_exists(source_dir, must_be_dir=True)

    if not os.access(source_dir, os.R_OK):
        raise PermissionError(f"无读取权限: {source_dir}")

    return True


def is_protected_file(file_path: str) -> bool:
    """
    检查文件是否为受保护文件。

    Args:
        file_path: 文件完整路径

    Returns:
        是受保护文件返回 True
    """
    file_name: str = os.path.basename(file_path)
    return file_name == PROTECTED_FILE


def validate_target_directory(target_dir: str) -> bool:
    """
    校验目标目录是否可写，不存在则创建。

    Args:
        target_dir: 目标目录路径

    Returns:
        可写返回 True

    Raises:
        PermissionError: 无写入权限
        OSError: 创建目录失败
    """
    if os.path.exists(target_dir):
        if not os.path.isdir(target_dir):
            raise ValueError(f"目标路径不是目录: {target_dir}")
        if not os.access(target_dir, os.W_OK):
            raise PermissionError(f"无写入权限: {target_dir}")
        return True

    try:
        os.makedirs(target_dir, exist_ok=True)
        return True
    except OSError as e:
        raise OSError(f"无法创建目标目录: {target_dir}, 错误: {e}")


def check_file_readable(file_path: str) -> bool:
    """
    检查文件是否可读。

    Args:
        file_path: 文件完整路径

    Returns:
        可读返回 True

    Raises:
        FileNotFoundError: 文件不存在
        PermissionError: 无读取权限
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"无读取权限: {file_path}")

    return True


def check_file_writable(file_path: str) -> bool:
    """
    检查文件是否可写（用于移动操作）。

    Args:
        file_path: 文件完整路径

    Returns:
        可写返回 True
    """
    if os.path.exists(file_path):
        return os.access(file_path, os.W_OK)

    parent_dir: str = os.path.dirname(file_path)
    if parent_dir and os.path.exists(parent_dir):
        return os.access(parent_dir, os.W_OK)

    return False


def validate_not_in_source_dir(target_path: str, source_dir: str) -> bool:
    """
    校验目标路径不在源目录内（防止递归操作）。

    Args:
        target_path: 目标路径
        source_dir: 源目录路径

    Returns:
        安全返回 True

    Raises:
        ValueError: 目标路径在源目录内
    """
    abs_target: str = os.path.abspath(target_path)
    abs_source: str = os.path.abspath(source_dir)

    if abs_target.startswith(abs_source + os.sep) or abs_target == abs_source:
        raise ValueError(f"目标路径不能在源目录内: {target_path}")

    return True
