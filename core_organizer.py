"""
core_organizer.py - 整理规则引擎模块

负责文件分类逻辑、目标路径生成、冲突文件名处理等核心规则。
不执行实际文件操作，仅生成整理计划。
"""
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from utils.config import (
    CONFLICT_SUFFIX_PATTERN,
    MAX_FILENAME_LENGTH,
    OUTPUT_DIR,
    SOURCE_DIR
)
from utils.helpers import (
    get_file_category,
    get_file_extension,
    get_file_modified_date,
    get_file_size,
    sanitize_filename
)
from utils.validators import is_protected_file


class OrganizeRule:
    """
    整理规则类，封装单个文件的整理规则计算。
    """

    def __init__(
        self,
        use_date_folder: bool = True,
        use_category_folder: bool = True,
        date_by_modified: bool = True
    ) -> None:
        """
        初始化整理规则。

        Args:
            use_date_folder: 是否按日期创建文件夹
            use_category_folder: 是否按类型创建子文件夹
            date_by_modified: True 使用修改日期，False 使用创建日期
        """
        self.use_date_folder = use_date_folder
        self.use_category_folder = use_category_folder
        self.date_by_modified = date_by_modified

    def get_date_folder(self, file_path: str) -> str:
        """
        获取文件对应的日期文件夹名。

        Args:
            file_path: 文件完整路径

        Returns:
            日期文件夹名 (YYYY-MM)
        """
        if self.date_by_modified:
            return get_file_modified_date(file_path)
        else:
            from utils.helpers import get_file_created_date
            return get_file_created_date(file_path)

    def get_category_folder(self, file_name: str) -> str:
        """
        获取文件对应的分类文件夹名。

        Args:
            file_name: 文件名

        Returns:
            分类文件夹名
        """
        if not self.use_category_folder:
            return ""
        return get_file_category(file_name)


class OrganizerEngine:
    """
    整理计划生成引擎，生成完整的文件整理计划。
    """

    def __init__(
        self,
        source_dir: str = SOURCE_DIR,
        output_base: str = SOURCE_DIR,
        rule: Optional[OrganizeRule] = None
    ) -> None:
        """
        初始化整理引擎。

        Args:
            source_dir: 源扫描目录
            output_base: 整理输出基础目录
            rule: 整理规则实例
        """
        self.source_dir = os.path.abspath(source_dir)
        self.output_base = os.path.abspath(output_base)
        self.rule = rule or OrganizeRule()

    def generate_target_path(
        self,
        file_path: str,
        existing_targets: Optional[Dict[str, int]] = None
    ) -> Tuple[str, Dict[str, str]]:
        """
        生成文件的目标路径。

        Args:
            file_path: 源文件完整路径
            existing_targets: 已存在的目标路径计数（用于冲突处理）

        Returns:
            (目标路径, 元数据字典)
        """
        if existing_targets is None:
            existing_targets = {}

        file_name: str = os.path.basename(file_path)
        file_ext: str = get_file_extension(file_name)

        date_folder: str = self.rule.get_date_folder(file_path)
        category_folder: str = self.rule.get_category_folder(file_name)

        target_dir: str = self.output_base
        if self.rule.use_date_folder:
            target_dir = os.path.join(target_dir, date_folder)
        if self.rule.use_category_folder and category_folder:
            target_dir = os.path.join(target_dir, category_folder)

        target_name: str = sanitize_filename(file_name)
        target_path: str = os.path.join(target_dir, target_name)

        target_path, target_name = self._handle_conflict(
            target_path, target_dir, target_name, file_ext, existing_targets
        )

        metadata: Dict[str, str] = {
            "original_name": file_name,
            "target_name": target_name,
            "date_folder": date_folder,
            "category": category_folder,
            "extension": file_ext,
            "size": str(get_file_size(file_path))
        }

        return target_path, metadata

    def _handle_conflict(
        self,
        target_path: str,
        target_dir: str,
        target_name: str,
        file_ext: str,
        existing_targets: Dict[str, int]
    ) -> Tuple[str, str]:
        """
        处理文件名冲突。

        Args:
            target_path: 原始目标路径
            target_dir: 目标目录
            target_name: 目标文件名
            file_ext: 文件扩展名
            existing_targets: 已存在目标计数

        Returns:
            (处理后的目标路径, 处理后的文件名)
        """
        base_key: str = target_path.lower()

        if base_key in existing_targets or os.path.exists(target_path):
            counter: int = existing_targets.get(base_key, 1)

            name_without_ext: str = target_name
            if file_ext:
                name_without_ext = target_name[:-len(file_ext)-1]

            while True:
                new_name: str = f"{name_without_ext}{CONFLICT_SUFFIX_PATTERN.format(counter)}.{file_ext}" if file_ext else f"{name_without_ext}{CONFLICT_SUFFIX_PATTERN.format(counter)}"
                new_path: str = os.path.join(target_dir, new_name)

                if not os.path.exists(new_path) and new_path.lower() not in existing_targets:
                    existing_targets[new_path.lower()] = 1
                    return new_path, new_name

                counter += 1

        existing_targets[base_key] = 1
        return target_path, target_name

    def create_plan(
        self,
        files: List[str]
    ) -> List[Dict[str, str]]:
        """
        为文件列表创建整理计划。

        Args:
            files: 文件路径列表

        Returns:
            整理计划列表，每项包含源路径、目标路径、元数据
        """
        plan: List[Dict[str, str]] = []
        existing_targets: Dict[str, int] = {}

        for file_path in files:
            if is_protected_file(file_path):
                continue

            try:
                target_path, metadata = self.generate_target_path(
                    file_path, existing_targets
                )

                plan.append({
                    "source_path": file_path,
                    "target_path": target_path,
                    "original_name": metadata["original_name"],
                    "target_name": metadata["target_name"],
                    "date_folder": metadata["date_folder"],
                    "category": metadata["category"],
                    "size": metadata["size"]
                })
            except Exception as e:
                plan.append({
                    "source_path": file_path,
                    "target_path": "",
                    "error": str(e),
                    "original_name": os.path.basename(file_path)
                })

        return plan


def classify_file(file_name: str) -> str:
    """
    根据文件名分类文件（独立函数，便于外部调用）。

    Args:
        file_name: 文件名

    Returns:
        分类名称
    """
    return get_file_category(file_name)


def build_target_directory(
    base_dir: str,
    date_folder: Optional[str] = None,
    category: Optional[str] = None
) -> str:
    """
    构建目标目录路径。

    Args:
        base_dir: 基础目录
        date_folder: 日期文件夹名
        category: 分类文件夹名

    Returns:
        完整目标目录路径
    """
    target: str = base_dir

    if date_folder:
        target = os.path.join(target, date_folder)

    if category:
        target = os.path.join(target, category)

    return target
