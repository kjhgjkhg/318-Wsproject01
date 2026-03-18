"""
整理规则引擎模块 - 核心分类逻辑和文件名生成。

此模块包含所有与文件分类、目标路径生成、整理规则相关的核心逻辑。
它是整理系统的"大脑"，负责决定文件应该去哪里。
"""

import os
from datetime import datetime
from typing import Optional, Tuple, List
from dataclasses import dataclass

from utils.config import (
    get_source_path,
    get_organized_path,
    ORGANIZED_SUBDIR,
    MAX_CONFLICT_ATTEMPTS,
)
from utils.helpers import (
    get_file_modification_date,
    format_date_for_folder,
    classify_file_by_name,
    get_unique_filename,
    sanitize_filename,
)
from utils.validators import validate_not_protected_file


# =============================================================================
# 数据类
# =============================================================================

@dataclass
class FilePlan:
    """
    单个文件的整理计划。
    
    Attributes:
        source_path: 源文件路径
        target_path: 目标文件路径
        category: 分类名称
        date_folder: 日期文件夹名称
        file_size: 文件大小（字节）
        status: 计划状态（pending/success/failed）
        error_msg: 错误信息（如果有）
    """
    source_path: str
    target_path: str
    category: str
    date_folder: str
    file_size: Optional[int]
    status: str = "pending"
    error_msg: Optional[str] = None


@dataclass
class OrganizeResult:
    """
    整理操作的结果。
    
    Attributes:
        plans: 所有文件计划列表
        success_count: 成功数量
        fail_count: 失败数量
        total_size: 总大小
        report_path: 报告文件路径
    """
    plans: List[FilePlan]
    success_count: int
    fail_count: int
    total_size: int
    report_path: Optional[str] = None


# =============================================================================
# 分类逻辑
# =============================================================================

class ClassificationEngine:
    """
    文件分类引擎。
    
    负责根据文件名、日期等属性对文件进行分类。
    """
    
    @staticmethod
    def classify(filename: str) -> str:
        """
        根据文件名判断分类。
        
        Args:
            filename: 文件名
            
        Returns:
            分类名称
        """
        return classify_file_by_name(filename)
    
    @staticmethod
    def get_date_folder(filepath: str) -> str:
        """
        根据文件修改日期获取日期文件夹名称。
        
        Args:
            filepath: 文件路径
            
        Returns:
            日期文件夹名称（YYYY-MM）
        """
        mod_date = get_file_modification_date(filepath)
        return format_date_for_folder(mod_date)


# =============================================================================
# 路径生成
# =============================================================================

class PathGenerator:
    """
    目标路径生成器。
    
    负责生成文件的目标路径，处理命名冲突。
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化路径生成器。
        
        Args:
            base_dir: 基础目录，None则使用默认organized路径
        """
        if base_dir is None:
            self.base_dir = get_organized_path()
        else:
            self.base_dir = base_dir
    
    def generate_target_path(
        self,
        source_path: str,
        category: str,
        date_folder: str,
        check_conflicts: bool = True
    ) -> Tuple[str, int]:
        """
        生成目标文件路径。
        
        Args:
            source_path: 源文件路径
            category: 分类名称
            date_folder: 日期文件夹
            check_conflicts: 是否检查命名冲突
            
        Returns:
            (目标路径, 冲突计数)
        """
        filename = os.path.basename(source_path)
        filename = sanitize_filename(filename)
        
        # 构建目标目录: base/YYYY-MM/Category/
        target_dir = os.path.join(self.base_dir, date_folder, category)
        
        if not check_conflicts:
            return os.path.join(target_dir, filename), 0
        
        # 处理命名冲突
        counter = 0
        target_path = get_unique_filename(target_dir, filename, counter)
        
        while os.path.exists(target_path) and counter < MAX_CONFLICT_ATTEMPTS:
            counter += 1
            target_path = get_unique_filename(target_dir, filename, counter)
        
        return target_path, counter
    
    def ensure_target_directory(self, target_path: str) -> Tuple[bool, str]:
        """
        确保目标目录存在。
        
        Args:
            target_path: 目标文件路径
            
        Returns:
            (是否成功, 错误信息)
        """
        target_dir = os.path.dirname(target_path)
        
        try:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            return True, ""
        except (OSError, PermissionError) as e:
            return False, str(e)


# =============================================================================
# 整理规则引擎
# =============================================================================

class OrganizeRuleEngine:
    """
    整理规则引擎。
    
    核心引擎，负责协调分类、路径生成，创建整理计划。
    """
    
    def __init__(self):
        """初始化规则引擎。"""
        self.classifier = ClassificationEngine()
        self.path_generator = PathGenerator()
    
    def create_plan(self, filepath: str) -> FilePlan:
        """
        为单个文件创建整理计划。
        
        Args:
            filepath: 文件路径
            
        Returns:
            文件整理计划
        """
        # 检查是否为受保护文件
        is_safe, error_msg = validate_not_protected_file(filepath)
        if not is_safe:
            return FilePlan(
                source_path=filepath,
                target_path="",
                category="",
                date_folder="",
                file_size=None,
                status="failed",
                error_msg=error_msg
            )
        
        # 获取分类
        filename = os.path.basename(filepath)
        category = self.classifier.classify(filename)
        
        # 获取日期文件夹
        date_folder = self.classifier.get_date_folder(filepath)
        
        # 获取文件大小
        try:
            file_size = os.path.getsize(filepath)
        except (OSError, IOError):
            file_size = None
        
        # 生成目标路径
        target_path, _ = self.path_generator.generate_target_path(
            filepath, category, date_folder
        )
        
        return FilePlan(
            source_path=filepath,
            target_path=target_path,
            category=category,
            date_folder=date_folder,
            file_size=file_size,
            status="pending"
        )
    
    def create_plans(self, filepaths: List[str]) -> List[FilePlan]:
        """
        为多个文件创建整理计划。
        
        Args:
            filepaths: 文件路径列表
            
        Returns:
            文件整理计划列表
        """
        plans = []
        for filepath in filepaths:
            plan = self.create_plan(filepath)
            plans.append(plan)
        return plans
    
    def preview_plan(self, plan: FilePlan) -> str:
        """
        生成计划的预览描述。
        
        Args:
            plan: 文件计划
            
        Returns:
            预览描述字符串
        """
        filename = os.path.basename(plan.source_path)
        size_str = f"{plan.file_size} bytes" if plan.file_size else "Unknown"
        
        lines = [
            f"File: {filename}",
            f"  Category: {plan.category}",
            f"  Date:     {plan.date_folder}",
            f"  Size:     {size_str}",
            f"  From:     {plan.source_path}",
            f"  To:       {plan.target_path}",
        ]
        
        if plan.status == "failed":
            lines.append(f"  ERROR:    {plan.error_msg}")
        
        return "\n".join(lines)


# =============================================================================
# 便捷函数
# =============================================================================

def create_single_plan(filepath: str) -> FilePlan:
    """
    为单个文件创建整理计划的便捷函数。
    
    Args:
        filepath: 文件路径
        
    Returns:
        文件整理计划
    """
    engine = OrganizeRuleEngine()
    return engine.create_plan(filepath)


def create_batch_plans(filepaths: List[str]) -> List[FilePlan]:
    """
    为多个文件创建整理计划的便捷函数。
    
    Args:
        filepaths: 文件路径列表
        
    Returns:
        文件整理计划列表
    """
    engine = OrganizeRuleEngine()
    return engine.create_plans(filepaths)


def get_relative_path(full_path: str, base_path: Optional[str] = None) -> str:
    """
    获取相对于基础路径的相对路径。
    
    Args:
        full_path: 完整路径
        base_path: 基础路径，None则使用源目录
        
    Returns:
        相对路径
    """
    if base_path is None:
        base_path = get_source_path()
    
    try:
        return os.path.relpath(full_path, base_path)
    except ValueError:
        return full_path
