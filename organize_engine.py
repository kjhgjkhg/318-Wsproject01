"""
organize_engine.py - 文件操作执行引擎模块

负责文件遍历、复制/移动操作、冲突处理、预览生成。
执行实际的文件系统操作。
"""
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from utils.config import (
    DEFAULT_EXTENSIONS,
    OUTPUT_DIR,
    REPORT_DATE_FORMAT,
    SOURCE_DIR
)
from utils.helpers import (
    format_file_size,
    get_file_extension,
    get_file_size,
    save_success_log,
    write_report
)
from utils.validators import (
    check_file_readable,
    is_protected_file,
    validate_target_directory
)


class FileScanner:
    """
    文件扫描器，扫描指定目录中的图片文件。
    """

    def __init__(
        self,
        source_dir: str = SOURCE_DIR,
        extensions: Optional[set] = None
    ) -> None:
        """
        初始化文件扫描器。

        Args:
            source_dir: 源扫描目录
            extensions: 允许的文件扩展名集合
        """
        self.source_dir = os.path.abspath(source_dir)
        self.extensions = extensions or DEFAULT_EXTENSIONS.copy()

    def scan(self) -> List[str]:
        """
        扫描源目录中的所有符合条件的文件。

        Returns:
            文件完整路径列表
        """
        files: List[str] = []

        if not os.path.exists(self.source_dir):
            return files

        for root, dirs, filenames in os.walk(self.source_dir):
            for filename in filenames:
                if is_protected_file(os.path.join(root, filename)):
                    continue

                ext: str = get_file_extension(filename)
                if ext in self.extensions:
                    files.append(os.path.join(root, filename))

        return files

    def scan_with_info(self) -> List[Dict[str, str]]:
        """
        扫描文件并返回详细信息。

        Returns:
            包含文件信息的字典列表
        """
        files: List[str] = self.scan()
        result: List[Dict[str, str]] = []

        for file_path in files:
            try:
                size: int = get_file_size(file_path)
                mtime: float = os.path.getmtime(file_path)
                mod_date: str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

                result.append({
                    "path": file_path,
                    "name": os.path.basename(file_path),
                    "size": format_file_size(size),
                    "size_bytes": str(size),
                    "modified": mod_date,
                    "extension": get_file_extension(file_path)
                })
            except OSError:
                continue

        return result


class FileOperator:
    """
    文件操作执行器，执行复制或移动操作。
    """

    def __init__(
        self,
        move_mode: bool = False,
        overwrite: bool = False
    ) -> None:
        """
        初始化文件操作器。

        Args:
            move_mode: True 为移动模式，False 为复制模式
            overwrite: 是否覆盖已存在文件
        """
        self.move_mode = move_mode
        self.overwrite = overwrite

    def copy_file(self, source: str, target: str) -> Tuple[bool, str]:
        """
        复制文件到目标路径。

        Args:
            source: 源文件路径
            target: 目标文件路径

        Returns:
            (是否成功, 错误信息)
        """
        try:
            target_dir: str = os.path.dirname(target)
            validate_target_directory(target_dir)

            if os.path.exists(target) and not self.overwrite:
                target = self._generate_unique_path(target)

            shutil.copy2(source, target)
            return True, ""
        except Exception as e:
            return False, str(e)

    def move_file(self, source: str, target: str) -> Tuple[bool, str]:
        """
        移动文件到目标路径。

        Args:
            source: 源文件路径
            target: 目标文件路径

        Returns:
            (是否成功, 错误信息)
        """
        try:
            target_dir: str = os.path.dirname(target)
            validate_target_directory(target_dir)

            if os.path.exists(target) and not self.overwrite:
                target = self._generate_unique_path(target)

            shutil.move(source, target)
            return True, ""
        except Exception as e:
            return False, str(e)

    def execute(self, source: str, target: str) -> Tuple[bool, str]:
        """
        执行文件操作（复制或移动）。

        Args:
            source: 源文件路径
            target: 目标文件路径

        Returns:
            (是否成功, 错误信息)
        """
        if self.move_mode:
            return self.move_file(source, target)
        return self.copy_file(source, target)

    def _generate_unique_path(self, path: str) -> str:
        """
        生成唯一的文件路径（处理冲突）。

        Args:
            path: 原始路径

        Returns:
            唯一的文件路径
        """
        directory: str = os.path.dirname(path)
        filename: str = os.path.basename(path)

        name: str = filename
        ext: str = ""
        if "." in filename:
            name, ext = filename.rsplit(".", 1)
            ext = f".{ext}"

        counter: int = 1
        while os.path.exists(path):
            new_name: str = f"{name}_{counter}{ext}"
            path = os.path.join(directory, new_name)
            counter += 1

        return path


class OrganizeExecutor:
    """
    整理执行器，整合扫描、计划生成和文件操作。
    """

    def __init__(
        self,
        source_dir: str = SOURCE_DIR,
        output_base: str = SOURCE_DIR,
        extensions: Optional[set] = None,
        move_mode: bool = False
    ) -> None:
        """
        初始化整理执行器。

        Args:
            source_dir: 源扫描目录
            output_base: 整理输出基础目录
            extensions: 允许的扩展名集合
            move_mode: 是否移动模式
        """
        self.source_dir = source_dir
        self.output_base = output_base
        self.scanner = FileScanner(source_dir, extensions)
        self.operator = FileOperator(move_mode=move_mode)

    def preview(self) -> List[Dict[str, str]]:
        """
        预览整理计划，不执行实际操作。

        Returns:
            整理计划列表
        """
        from core_organizer import OrganizeRule, OrganizerEngine

        files: List[str] = self.scanner.scan()
        rule: OrganizeRule = OrganizeRule()
        engine: OrganizerEngine = OrganizerEngine(
            source_dir=self.source_dir,
            output_base=self.output_base,
            rule=rule
        )

        return engine.create_plan(files)

    def execute(
        self,
        plan: Optional[List[Dict[str, str]]] = None,
        dry_run: bool = False
    ) -> Dict[str, any]:
        """
        执行整理操作。

        Args:
            plan: 整理计划，None 时自动生成
            dry_run: 是否仅预览

        Returns:
            执行结果字典
        """
        if plan is None:
            plan = self.preview()

        results: List[Dict[str, str]] = []
        failed: List[Dict[str, str]] = []
        success_count: int = 0
        total_count: int = len(plan)

        for item in plan:
            if "error" in item:
                failed.append({
                    "path": item.get("source_path", ""),
                    "error": item["error"]
                })
                continue

            source: str = item["source_path"]
            target: str = item["target_path"]

            if dry_run:
                results.append({
                    "old_path": source,
                    "new_path": target,
                    "size": format_file_size(int(item.get("size", 0)))
                })
                success_count += 1
                continue

            success, error = self.operator.execute(source, target)

            if success:
                results.append({
                    "old_path": source,
                    "new_path": target,
                    "size": format_file_size(int(item.get("size", 0)))
                })
                success_count += 1
            else:
                failed.append({
                    "path": source,
                    "error": error
                })

        return {
            "total": total_count,
            "success": success_count,
            "failed": len(failed),
            "records": results,
            "failed_items": failed
        }

    def generate_report(self, results: Dict[str, any]) -> str:
        """
        生成整理报告。

        Args:
            results: 执行结果字典

        Returns:
            报告文件路径
        """
        report_path: str = write_report(
            records=results.get("records", []),
            total_count=results.get("total", 0),
            success_count=results.get("success", 0),
            failed_count=results.get("failed", 0),
            failed_items=results.get("failed_items", [])
        )

        if results.get("records"):
            save_success_log(results["records"])

        return report_path
