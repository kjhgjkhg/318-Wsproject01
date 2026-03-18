"""
整理执行引擎模块 - 文件遍历、复制/移动操作、冲突处理、预览生成。

此模块负责实际执行文件操作，包括扫描目录、复制/移动文件、
处理冲突、生成预览等。它是整理系统的"执行者"。
"""

import os
import shutil
from typing import List, Set, Optional, Tuple, Dict, Any
from datetime import datetime

from utils.config import (
    get_source_path,
    get_organized_path,
    PROTECTED_FILE,
    ORGANIZED_SUBDIR,
)
from utils.helpers import (
    get_file_extension,
    format_file_size,
    format_report_header,
    format_report_footer,
    format_file_entry,
    format_error_entry,
    write_report,
    write_json_log,
    ensure_output_dir,
    get_unique_filename,
)
from utils.validators import (
    validate_source_directory,
    validate_not_protected_file,
    validate_file_exists,
)
from core_organizer import (
    OrganizeRuleEngine,
    PathGenerator,
    FilePlan,
    OrganizeResult,
)


# =============================================================================
# 文件扫描器
# =============================================================================

class FileScanner:
    """
    文件扫描器。
    
    负责扫描源目录，收集符合条件的图片文件。
    """
    
    def __init__(self, extensions: Optional[Set[str]] = None):
        """
        初始化文件扫描器。
        
        Args:
            extensions: 要扫描的扩展名集合，None则使用默认
        """
        self.extensions = extensions
        self.source_path = get_source_path()
    
    def is_valid_extension(self, filename: str) -> bool:
        """
        检查文件扩展名是否有效。
        
        Args:
            filename: 文件名
            
        Returns:
            是否有效
        """
        if self.extensions is None:
            return True
        
        ext = get_file_extension(filename)
        return ext in self.extensions
    
    def is_protected(self, filepath: str) -> bool:
        """
        检查文件是否受保护。
        
        Args:
            filepath: 文件路径
            
        Returns:
            是否受保护
        """
        filename = os.path.basename(filepath)
        return filename == PROTECTED_FILE
    
    def should_skip_directory(self, dirname: str) -> bool:
        """
        检查是否应该跳过该目录。
        
        Args:
            dirname: 目录名
            
        Returns:
            是否跳过
        """
        # 跳过 organized 子目录（避免递归处理已整理的文件）
        return dirname == ORGANIZED_SUBDIR
    
    def scan(self) -> List[str]:
        """
        扫描源目录，返回所有符合条件的图片文件路径。
        
        Returns:
            文件路径列表
        """
        valid, msg = validate_source_directory()
        if not valid:
            raise RuntimeError(f"Cannot scan: {msg}")
        
        files = []
        
        try:
            for root, dirs, filenames in os.walk(self.source_path):
                # 过滤掉应该跳过的目录
                dirs[:] = [d for d in dirs if not self.should_skip_directory(d)]
                
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    
                    # 跳过受保护文件
                    if self.is_protected(filepath):
                        continue
                    
                    # 检查扩展名
                    if not self.is_valid_extension(filename):
                        continue
                    
                    # 验证文件可访问
                    valid, _ = validate_file_exists(filepath)
                    if not valid:
                        continue
                    
                    files.append(filepath)
        
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Error scanning directory: {e}")
        
        return sorted(files)
    
    def scan_with_stats(self) -> Tuple[List[str], Dict[str, Any]]:
        """
        扫描并返回统计信息。
        
        Returns:
            (文件列表, 统计信息字典)
        """
        files = self.scan()
        
        total_size = 0
        extension_counts: Dict[str, int] = {}
        
        for filepath in files:
            try:
                size = os.path.getsize(filepath)
                total_size += size
                
                ext = get_file_extension(filepath)
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
            except (OSError, IOError):
                pass
        
        stats = {
            "total_files": len(files),
            "total_size": total_size,
            "total_size_formatted": format_file_size(total_size),
            "extension_counts": extension_counts,
        }
        
        return files, stats


# =============================================================================
# 文件操作执行器
# =============================================================================

class FileOperationExecutor:
    """
    文件操作执行器。
    
    负责执行实际的文件复制/移动操作。
    """
    
    def __init__(self, dry_run: bool = False):
        """
        初始化执行器。
        
        Args:
            dry_run: 是否为预览模式（不实际执行）
        """
        self.dry_run = dry_run
        self.path_generator = PathGenerator()
    
    def ensure_directory(self, target_path: str) -> Tuple[bool, str]:
        """
        确保目标目录存在。
        
        Args:
            target_path: 目标文件路径
            
        Returns:
            (是否成功, 错误信息)
        """
        if self.dry_run:
            return True, ""
        
        return self.path_generator.ensure_target_directory(target_path)
    
    def copy_file(self, plan: FilePlan) -> Tuple[bool, str]:
        """
        复制文件。
        
        Args:
            plan: 文件计划
            
        Returns:
            (是否成功, 错误信息)
        """
        try:
            # 确保目录存在
            success, msg = self.ensure_directory(plan.target_path)
            if not success:
                return False, msg
            
            if self.dry_run:
                return True, ""
            
            # 执行复制
            shutil.copy2(plan.source_path, plan.target_path)
            return True, ""
        
        except (shutil.Error, OSError, IOError, PermissionError) as e:
            return False, str(e)
    
    def move_file(self, plan: FilePlan) -> Tuple[bool, str]:
        """
        移动文件。
        
        Args:
            plan: 文件计划
            
        Returns:
            (是否成功, 错误信息)
        """
        try:
            # 确保目录存在
            success, msg = self.ensure_directory(plan.target_path)
            if not success:
                return False, msg
            
            if self.dry_run:
                return True, ""
            
            # 执行移动
            shutil.move(plan.source_path, plan.target_path)
            return True, ""
        
        except (shutil.Error, OSError, IOError, PermissionError) as e:
            return False, str(e)
    
    def execute_plan(self, plan: FilePlan, move: bool = False) -> FilePlan:
        """
        执行单个文件计划。
        
        Args:
            plan: 文件计划
            move: 是否移动（否则复制）
            
        Returns:
            更新后的文件计划
        """
        # 如果计划已经失败，直接返回
        if plan.status == "failed":
            return plan
        
        # 检查源文件
        valid, msg = validate_file_exists(plan.source_path)
        if not valid:
            plan.status = "failed"
            plan.error_msg = msg
            return plan
        
        # 检查受保护文件
        valid, msg = validate_not_protected_file(plan.source_path)
        if not valid:
            plan.status = "failed"
            plan.error_msg = msg
            return plan
        
        # 执行操作
        if move:
            success, error_msg = self.move_file(plan)
        else:
            success, error_msg = self.copy_file(plan)
        
        if success:
            plan.status = "success"
        else:
            plan.status = "failed"
            plan.error_msg = error_msg
        
        return plan
    
    def execute_plans(self, plans: List[FilePlan], move: bool = False) -> List[FilePlan]:
        """
        执行多个文件计划。
        
        Args:
            plans: 文件计划列表
            move: 是否移动
            
        Returns:
            更新后的文件计划列表
        """
        results = []
        for plan in plans:
            result = self.execute_plan(plan, move)
            results.append(result)
        return results


# =============================================================================
# 预览生成器
# =============================================================================

class PreviewGenerator:
    """
    预览生成器。
    
    负责生成整理计划的预览输出。
    """
    
    @staticmethod
    def generate_preview(plans: List[FilePlan]) -> str:
        """
        生成预览文本。
        
        Args:
            plans: 文件计划列表
            
        Returns:
            预览文本
        """
        lines = [
            format_report_header("ORGANIZE PREVIEW"),
            f"Mode: PREVIEW ONLY (no files will be modified)",
            f"Total files to process: {len(plans)}",
            "",
            "PLAN DETAILS:",
            "",
        ]
        
        for i, plan in enumerate(plans, 1):
            lines.append(format_file_entry(
                index=i,
                old_path=plan.source_path,
                new_path=plan.target_path,
                file_size=plan.file_size,
                status="PREVIEW"
            ))
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_console_preview(plans: List[FilePlan], max_items: int = 20) -> str:
        """
        生成控制台预览（简略版）。
        
        Args:
            plans: 文件计划列表
            max_items: 最大显示条目数
            
        Returns:
            简略预览文本
        """
        lines = [
            "",
            "=" * 60,
            "ORGANIZE PREVIEW",
            "=" * 60,
            f"Total files: {len(plans)}",
            "",
        ]
        
        # 显示前N个
        display_count = min(len(plans), max_items)
        for i in range(display_count):
            plan = plans[i]
            filename = os.path.basename(plan.source_path)
            size = format_file_size(plan.file_size)
            lines.append(f"  {i+1:3d}. [{plan.category}] {filename} ({size})")
            lines.append(f"       -> {plan.date_folder}/{plan.category}/")
        
        if len(plans) > max_items:
            lines.append(f"  ... and {len(plans) - max_items} more files")
        
        lines.extend([
            "",
            "=" * 60,
        ])
        
        return "\n".join(lines)


# =============================================================================
# 报告生成器
# =============================================================================

class ReportGenerator:
    """
    报告生成器。
    
    负责生成整理操作的详细报告。
    """
    
    @staticmethod
    def generate_text_report(result: OrganizeResult, operation_type: str = "COPY") -> str:
        """
        生成文本格式报告。
        
        Args:
            result: 整理结果
            operation_type: 操作类型（COPY/MOVE）
            
        Returns:
            报告文本
        """
        lines = [
            format_report_header(f"ORGANIZE REPORT - {operation_type}"),
        ]
        
        # 成功项
        success_plans = [p for p in result.plans if p.status == "success"]
        if success_plans:
            lines.extend([
                "",
                f"SUCCESSFUL OPERATIONS ({len(success_plans)}):",
                "",
            ])
            for i, plan in enumerate(success_plans, 1):
                lines.append(format_file_entry(
                    index=i,
                    old_path=plan.source_path,
                    new_path=plan.target_path,
                    file_size=plan.file_size,
                    status="SUCCESS"
                ))
        
        # 失败项
        failed_plans = [p for p in result.plans if p.status == "failed"]
        if failed_plans:
            lines.extend([
                "",
                f"FAILED OPERATIONS ({len(failed_plans)}):",
                "",
            ])
            for i, plan in enumerate(failed_plans, 1):
                lines.append(format_error_entry(
                    index=i,
                    filepath=plan.source_path,
                    error_msg=plan.error_msg or "Unknown error"
                ))
        
        # 汇总
        lines.append(format_report_footer(
            total_files=len(result.plans),
            success_count=result.success_count,
            fail_count=result.fail_count
        ))
        
        return "\n".join(lines)
    
    @staticmethod
    def save_report(result: OrganizeResult, operation_type: str = "COPY") -> Tuple[bool, str]:
        """
        保存报告到文件。
        
        Args:
            result: 整理结果
            operation_type: 操作类型
            
        Returns:
            (是否成功, 文件路径或错误信息)
        """
        report_content = ReportGenerator.generate_text_report(result, operation_type)
        return write_report(report_content)
    
    @staticmethod
    def save_json_log(result: OrganizeResult, operation_type: str = "COPY") -> Tuple[bool, str]:
        """
        保存JSON格式日志。
        
        Args:
            result: 整理结果
            operation_type: 操作类型
            
        Returns:
            (是否成功, 文件路径或错误信息)
        """
        data = {
            "operation_type": operation_type,
            "total_files": len(result.plans),
            "success_count": result.success_count,
            "fail_count": result.fail_count,
            "total_size": result.total_size,
            "files": [
                {
                    "source": p.source_path,
                    "target": p.target_path,
                    "category": p.category,
                    "date_folder": p.date_folder,
                    "size": p.file_size,
                    "status": p.status,
                    "error": p.error_msg,
                }
                for p in result.plans
            ]
        }
        
        return write_json_log(data)


# =============================================================================
# 主引擎
# =============================================================================

class OrganizeEngine:
    """
    整理主引擎。
    
    协调扫描、计划、执行、报告生成的完整流程。
    """
    
    def __init__(self, extensions: Optional[Set[str]] = None):
        """
        初始化整理引擎。
        
        Args:
            extensions: 扩展名集合
        """
        self.extensions = extensions
        self.scanner = FileScanner(extensions)
        self.rule_engine = OrganizeRuleEngine()
        self.preview_generator = PreviewGenerator()
        self.report_generator = ReportGenerator()
    
    def preview(self) -> Tuple[List[FilePlan], Dict[str, Any]]:
        """
        生成整理预览。
        
        Returns:
            (文件计划列表, 统计信息)
        """
        # 扫描文件
        files, stats = self.scanner.scan_with_stats()
        
        # 创建计划
        plans = self.rule_engine.create_plans(files)
        
        return plans, stats
    
    def run(self, move: bool = False, dry_run: bool = False) -> OrganizeResult:
        """
        执行整理操作。
        
        Args:
            move: 是否移动（否则复制）
            dry_run: 是否为预览模式
            
        Returns:
            整理结果
        """
        # 扫描文件
        files, _ = self.scanner.scan_with_stats()
        
        # 创建计划
        plans = self.rule_engine.create_plans(files)
        
        # 执行操作
        executor = FileOperationExecutor(dry_run=dry_run)
        executed_plans = executor.execute_plans(plans, move=move)
        
        # 统计结果
        success_count = sum(1 for p in executed_plans if p.status == "success")
        fail_count = sum(1 for p in executed_plans if p.status == "failed")
        total_size = sum(p.file_size or 0 for p in executed_plans if p.status == "success")
        
        result = OrganizeResult(
            plans=executed_plans,
            success_count=success_count,
            fail_count=fail_count,
            total_size=total_size
        )
        
        # 保存报告
        if not dry_run:
            operation_type = "MOVE" if move else "COPY"
            success, path = self.report_generator.save_report(result, operation_type)
            if success:
                result.report_path = path
            # 同时保存JSON日志
            self.report_generator.save_json_log(result, operation_type)
        
        return result
    
    def get_preview_text(self) -> str:
        """
        获取预览文本。
        
        Returns:
            预览文本
        """
        plans, _ = self.preview()
        return self.preview_generator.generate_preview(plans)
    
    def get_console_preview(self, max_items: int = 20) -> str:
        """
        获取控制台预览文本。
        
        Args:
            max_items: 最大显示条目数
            
        Returns:
            简略预览文本
        """
        plans, _ = self.preview()
        return self.preview_generator.generate_console_preview(plans, max_items)


# =============================================================================
# 便捷函数
# =============================================================================

def scan_images(extensions: Optional[Set[str]] = None) -> List[str]:
    """
    扫描图片文件的便捷函数。
    
    Args:
        extensions: 扩展名集合
        
    Returns:
        文件路径列表
    """
    scanner = FileScanner(extensions)
    return scanner.scan()


def preview_organize(extensions: Optional[Set[str]] = None) -> Tuple[List[FilePlan], str]:
    """
    预览整理的便捷函数。
    
    Args:
        extensions: 扩展名集合
        
    Returns:
        (文件计划列表, 预览文本)
    """
    engine = OrganizeEngine(extensions)
    plans, _ = engine.preview()
    preview_text = engine.get_preview_text()
    return plans, preview_text


def execute_organize(
    move: bool = False,
    dry_run: bool = False,
    extensions: Optional[Set[str]] = None
) -> OrganizeResult:
    """
    执行整理的便捷函数。
    
    Args:
        move: 是否移动
        dry_run: 是否预览模式
        extensions: 扩展名集合
        
    Returns:
        整理结果
    """
    engine = OrganizeEngine(extensions)
    return engine.run(move=move, dry_run=dry_run)
