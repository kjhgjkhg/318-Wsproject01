"""
输入校验模块 - 提供路径、扩展名、确认等校验功能。

此模块包含所有与用户输入和系统状态相关的校验函数。
所有校验函数返回 (bool, str) 元组，表示 (是否通过, 错误信息)。
"""

import os
import sys
from typing import Tuple, Set, Optional, List

from utils.config import (
    SOURCE_DIR,
    OUTPUT_DIR,
    PROTECTED_FILE,
    DEFAULT_IMAGE_EXTENSIONS,
    get_source_path,
    get_output_path,
    is_image_extension,
)


# =============================================================================
# 路径校验
# =============================================================================

def validate_source_directory() -> Tuple[bool, str]:
    """
    校验源目录是否存在且可读。
    
    Returns:
        (是否通过, 错误信息)
    """
    source_path = get_source_path()
    
    if not os.path.exists(source_path):
        return False, f"Source directory does not exist: {source_path}"
    
    if not os.path.isdir(source_path):
        return False, f"Source path is not a directory: {source_path}"
    
    # 检查读取权限
    try:
        os.listdir(source_path)
    except PermissionError:
        return False, f"Permission denied: cannot read source directory {source_path}"
    except OSError as e:
        return False, f"Cannot access source directory: {e}"
    
    return True, ""


def validate_output_directory() -> Tuple[bool, str]:
    """
    校验输出目录是否存在或可创建。
    
    Returns:
        (是否通过, 错误信息)
    """
    output_path = get_output_path()
    
    if os.path.exists(output_path):
        if not os.path.isdir(output_path):
            return False, f"Output path exists but is not a directory: {output_path}"
        # 检查写入权限
        try:
            test_file = os.path.join(output_path, ".write_test")
            with open(test_file, "w") as f:
                f.write("")
            os.remove(test_file)
        except PermissionError:
            return False, f"Permission denied: cannot write to output directory {output_path}"
        except OSError as e:
            return False, f"Cannot write to output directory: {e}"
    else:
        # 尝试创建目录
        try:
            os.makedirs(output_path, exist_ok=True)
        except PermissionError:
            return False, f"Permission denied: cannot create output directory {output_path}"
        except OSError as e:
            return False, f"Cannot create output directory: {e}"
    
    return True, ""


def validate_file_exists(filepath: str) -> Tuple[bool, str]:
    """
    校验指定文件是否存在。
    
    Args:
        filepath: 文件路径
        
    Returns:
        (是否通过, 错误信息)
    """
    if not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"
    
    if not os.path.isfile(filepath):
        return False, f"Path is not a file: {filepath}"
    
    return True, ""


def validate_is_within_source(filepath: str) -> Tuple[bool, str]:
    """
    校验文件路径是否在源目录内。
    
    Args:
        filepath: 文件路径
        
    Returns:
        (是否通过, 错误信息)
    """
    source_path = get_source_path()
    abs_source = os.path.abspath(source_path)
    abs_file = os.path.abspath(filepath)
    
    # 确保文件路径以源目录开头
    if not (abs_file.startswith(abs_source + os.sep) or abs_file == abs_source):
        return False, f"File is not within source directory: {filepath}"
    
    return True, ""


# =============================================================================
# 扩展名校验
# =============================================================================

def validate_extensions(ext_string: Optional[str]) -> Tuple[Set[str], str]:
    """
    校验并解析扩展名字符串。
    
    Args:
        ext_string: 逗号分隔的扩展名字符串，None则使用默认值
        
    Returns:
        (扩展名集合, 错误信息) - 如果错误，集合为空
    """
    if ext_string is None or ext_string.strip() == "":
        return DEFAULT_IMAGE_EXTENSIONS, ""
    
    extensions: Set[str] = set()
    invalid_exts: List[str] = []
    
    for ext in ext_string.split(","):
        ext = ext.strip().lstrip(".").lower()
        if not ext:
            continue
        
        if is_image_extension(ext):
            extensions.add(ext)
        else:
            invalid_exts.append(ext)
    
    if invalid_exts:
        valid_list = ", ".join(sorted(DEFAULT_IMAGE_EXTENSIONS))
        return set(), f"Invalid extensions: {', '.join(invalid_exts)}. Valid: {valid_list}"
    
    if not extensions:
        return DEFAULT_IMAGE_EXTENSIONS, ""
    
    return extensions, ""


def validate_extension_single(ext: str) -> Tuple[bool, str]:
    """
    校验单个扩展名是否有效。
    
    Args:
        ext: 扩展名
        
    Returns:
        (是否通过, 错误信息)
    """
    ext = ext.lstrip(".").lower()
    
    if not ext:
        return False, "Extension cannot be empty"
    
    if not is_image_extension(ext):
        valid_list = ", ".join(sorted(DEFAULT_IMAGE_EXTENSIONS))
        return False, f"Invalid extension '{ext}'. Valid: {valid_list}"
    
    return True, ""


# =============================================================================
# 确认校验
# =============================================================================

def validate_yes_confirmation(confirmed: bool, operation: str = "operation") -> Tuple[bool, str]:
    """
    校验用户是否已确认操作。
    
    Args:
        confirmed: 是否已确认
        operation: 操作描述
        
    Returns:
        (是否通过, 错误信息)
    """
    if not confirmed:
        return False, f"{operation} requires --yes flag to proceed. Use --dry-run first to preview."
    
    return True, ""


def prompt_user_confirmation(message: str = "Do you want to proceed?") -> bool:
    """
    交互式提示用户确认。
    
    Args:
        message: 提示消息
        
    Returns:
        用户是否确认
    """
    try:
        response = input(f"{message} [y/N]: ").strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


# =============================================================================
# 受保护文件校验
# =============================================================================

def validate_not_protected_file(filepath: str) -> Tuple[bool, str]:
    """
    校验文件是否为受保护文件。
    
    Args:
        filepath: 文件路径
        
    Returns:
        (是否通过, 错误信息) - 返回False表示是受保护文件
    """
    filename = os.path.basename(filepath)
    
    if filename == PROTECTED_FILE:
        return False, f"File is protected and cannot be modified: {filepath}"
    
    return True, ""


def validate_safe_to_modify(filepath: str) -> Tuple[bool, str]:
    """
    综合校验文件是否可以安全修改。
    
    Args:
        filepath: 文件路径
        
    Returns:
        (是否通过, 错误信息)
    """
    # 检查是否为受保护文件
    is_safe, msg = validate_not_protected_file(filepath)
    if not is_safe:
        return False, msg
    
    # 检查文件是否存在
    is_safe, msg = validate_file_exists(filepath)
    if not is_safe:
        return False, msg
    
    # 检查是否在源目录内
    is_safe, msg = validate_is_within_source(filepath)
    if not is_safe:
        return False, msg
    
    return True, ""


# =============================================================================
# 综合校验
# =============================================================================

def validate_environment() -> Tuple[bool, str]:
    """
    校验整体环境是否就绪。
    
    Returns:
        (是否通过, 错误信息)
    """
    # 校验源目录
    is_valid, msg = validate_source_directory()
    if not is_valid:
        return False, msg
    
    # 校验输出目录
    is_valid, msg = validate_output_directory()
    if not is_valid:
        return False, msg
    
    return True, ""


def validate_operation_preconditions(
    extensions: Optional[str] = None,
    require_confirmation: bool = False,
    confirmed: bool = False
) -> Tuple[bool, str, Set[str]]:
    """
    校验操作的前提条件。
    
    Args:
        extensions: 扩展名字符串
        require_confirmation: 是否需要确认
        confirmed: 是否已确认
        
    Returns:
        (是否通过, 错误信息, 扩展名集合)
    """
    # 校验环境
    is_valid, msg = validate_environment()
    if not is_valid:
        return False, msg, set()
    
    # 校验扩展名
    ext_set, msg = validate_extensions(extensions)
    if msg:  # 有错误信息
        return False, msg, set()
    
    # 校验确认
    if require_confirmation:
        is_valid, msg = validate_yes_confirmation(confirmed, "This operation")
        if not is_valid:
            return False, msg, ext_set
    
    return True, "", ext_set
