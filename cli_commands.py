"""
CLI命令实现模块 - 子命令具体实现（preview / run / report）。

此模块包含所有子命令的具体实现逻辑。每个命令函数接收解析后的参数，
执行相应操作，并返回退出码（0表示成功，非0表示失败）。
"""

import os
import sys
from typing import Optional, Set, List, Tuple

from utils.config import (
    get_source_path,
    get_output_path,
    get_organized_path,
    DEFAULT_IMAGE_EXTENSIONS,
)
from utils.validators import (
    validate_environment,
    validate_extensions,
    validate_yes_confirmation,
    validate_operation_preconditions,
)
from utils.helpers import (
    format_file_size,
    format_timestamp,
    create_separator,
    ensure_output_dir,
)
from organize_engine import OrganizeEngine, execute_organize, preview_organize
from core_organizer import OrganizeResult


# =============================================================================
# 辅助函数
# =============================================================================

def print_error(message: str) -> None:
    """打印错误信息。"""
    print(f"ERROR: {message}", file=sys.stderr)


def print_success(message: str) -> None:
    """打印成功信息。"""
    print(f"SUCCESS: {message}")


def print_info(message: str) -> None:
    """打印信息。"""
    print(f"INFO: {message}")


def print_warning(message: str) -> None:
    """打印警告信息。"""
    print(f"WARNING: {message}")


def format_extensions(ext_set: Set[str]) -> str:
    """格式化扩展名集合为字符串。"""
    return ", ".join(sorted(ext_set))


# =============================================================================
# Preview 命令
# =============================================================================

def cmd_preview(args) -> int:
    """
    执行 preview 子命令。
    
    预览整理计划，显示每个文件将去哪里，不实际移动。
    
    Args:
        args: 解析后的参数
        
    Returns:
        退出码（0成功，1失败）
    """
    # 校验环境
    is_valid, msg = validate_environment()
    if not is_valid:
        print_error(msg)
        return 1
    
    # 校验扩展名
    ext_set, msg = validate_extensions(args.ext)
    if msg:
        print_error(msg)
        return 1
    
    # 显示配置信息
    print()
    print(create_separator("="))
    print("ORGANIZE PREVIEW".center(70))
    print(create_separator("="))
    print(f"Source:      {get_source_path()}")
    print(f"Output:      {get_output_path()}")
    print(f"Extensions:  {format_extensions(ext_set)}")
    print(f"Mode:        PREVIEW ONLY (no changes)")
    print(create_separator("="))
    print()
    
    # 执行预览
    try:
        engine = OrganizeEngine(extensions=ext_set)
        plans, stats = engine.preview()
        
        if not plans:
            print("No image files found in source directory.")
            print(f"Searched for: {format_extensions(ext_set)}")
            return 0
        
        # 显示统计
        print(f"Found {stats['total_files']} files ({stats['total_size_formatted']})")
        print()
        
        # 按分类统计
        if stats.get('extension_counts'):
            print("By extension:")
            for ext, count in sorted(stats['extension_counts'].items()):
                print(f"  .{ext}: {count} files")
            print()
        
        # 显示预览
        preview_text = engine.get_console_preview(max_items=args.max_preview or 20)
        print(preview_text)
        
        # 提示
        print()
        print("To execute this plan, run:")
        print(f"  python main.py organize run --yes")
        if args.ext:
            print(f"  python main.py organize run --yes --ext {args.ext}")
        print()
        
        return 0
        
    except Exception as e:
        print_error(f"Preview failed: {e}")
        return 1


# =============================================================================
# Run 命令
# =============================================================================

def cmd_run(args) -> int:
    """
    执行 run 子命令。
    
    执行整理操作。需要 --yes 确认；--move 才真正移动，否则复制。
    
    Args:
        args: 解析后的参数
        
    Returns:
        退出码（0成功，1失败）
    """
    # 校验所有前提条件
    is_valid, msg, ext_set = validate_operation_preconditions(
        extensions=args.ext,
        require_confirmation=True,
        confirmed=args.yes
    )
    if not is_valid:
        print_error(msg)
        return 1
    
    # 检查是否为dry-run模式
    dry_run = args.dry_run if hasattr(args, 'dry_run') else False
    
    # 确定操作类型
    move = args.move if hasattr(args, 'move') else False
    operation = "MOVE" if move else "COPY"
    
    # 显示配置信息
    print()
    print(create_separator("="))
    print(f"ORGANIZE RUN - {operation}".center(70))
    print(create_separator("="))
    print(f"Source:      {get_source_path()}")
    print(f"Output:      {get_output_path()}")
    print(f"Target:      {get_organized_path()}")
    print(f"Extensions:  {format_extensions(ext_set)}")
    print(f"Operation:   {operation}")
    if dry_run:
        print(f"Mode:        DRY RUN (no actual changes)")
    print(create_separator("="))
    print()
    
    # 执行整理
    try:
        result = execute_organize(
            move=move,
            dry_run=dry_run,
            extensions=ext_set
        )
        
        # 显示结果
        print()
        print(create_separator("="))
        print("RESULTS".center(70))
        print(create_separator("="))
        print(f"Total files:   {len(result.plans)}")
        print(f"Successful:    {result.success_count}")
        print(f"Failed:        {result.fail_count}")
        print(f"Total size:    {format_file_size(result.total_size)}")
        
        if dry_run:
            print()
            print("NOTE: This was a dry run. No files were actually modified.")
            print("      Remove --dry-run to execute for real.")
        
        # 显示失败项
        if result.fail_count > 0:
            print()
            print(create_separator("-"))
            print("FAILED ITEMS:")
            print(create_separator("-"))
            for plan in result.plans:
                if plan.status == "failed":
                    filename = os.path.basename(plan.source_path)
                    print(f"  - {filename}: {plan.error_msg}")
        
        # 显示报告路径
        if result.report_path and not dry_run:
            print()
            print(f"Report saved: {result.report_path}")
        
        print(create_separator("="))
        print()
        
        # 返回适当的退出码
        if result.fail_count > 0:
            return 1 if result.success_count == 0 else 0
        return 0
        
    except Exception as e:
        print_error(f"Organize failed: {e}")
        return 1


# =============================================================================
# Report 命令
# =============================================================================

def find_latest_report() -> Optional[str]:
    """
    查找最新的报告文件。
    
    Returns:
        最新报告文件路径，如果没有则返回None
    """
    output_dir = get_output_path()
    
    if not os.path.exists(output_dir):
        return None
    
    report_files = []
    for filename in os.listdir(output_dir):
        if filename.startswith("organize_report_") and filename.endswith(".txt"):
            filepath = os.path.join(output_dir, filename)
            try:
                mtime = os.path.getmtime(filepath)
                report_files.append((filepath, mtime))
            except (OSError, IOError):
                pass
    
    if not report_files:
        return None
    
    # 按修改时间排序，返回最新的
    report_files.sort(key=lambda x: x[1], reverse=True)
    return report_files[0][0]


def list_all_reports() -> List[Tuple[str, float]]:
    """
    列出所有报告文件。
    
    Returns:
        (文件路径, 修改时间) 列表
    """
    output_dir = get_output_path()
    
    if not os.path.exists(output_dir):
        return []
    
    report_files = []
    for filename in os.listdir(output_dir):
        if filename.startswith("organize_report_") and filename.endswith(".txt"):
            filepath = os.path.join(output_dir, filename)
            try:
                mtime = os.path.getmtime(filepath)
                report_files.append((filepath, mtime))
            except (OSError, IOError):
                pass
    
    # 按修改时间排序
    report_files.sort(key=lambda x: x[1], reverse=True)
    return report_files


def cmd_report(args) -> int:
    """
    执行 report 子命令。
    
    生成或显示上次整理的详细报告。
    
    Args:
        args: 解析后的参数
        
    Returns:
        退出码（0成功，1失败）
    """
    # 校验输出目录
    is_valid, msg = validate_environment()
    if not is_valid:
        print_error(msg)
        return 1
    
    # 列出所有报告
    reports = list_all_reports()
    
    if not reports:
        print("No reports found.")
        print(f"Run 'organize run' first to generate a report.")
        return 1
    
    # 显示报告列表
    print()
    print(create_separator("="))
    print("AVAILABLE REPORTS".center(70))
    print(create_separator("="))
    
    for i, (filepath, mtime) in enumerate(reports[:10], 1):
        filename = os.path.basename(filepath)
        time_str = format_timestamp()[:10]  # 简化显示
        try:
            size = os.path.getsize(filepath)
            size_str = format_file_size(size)
        except (OSError, IOError):
            size_str = "Unknown"
        
        marker = " <- latest" if i == 1 else ""
        print(f"{i:2d}. {filename} ({size_str}){marker}")
    
    print(create_separator("="))
    print()
    
    # 显示最新报告内容（如果要求）
    if args.show if hasattr(args, 'show') else False:
        latest_report = reports[0][0]
        print(f"Showing latest report: {os.path.basename(latest_report)}")
        print()
        
        try:
            with open(latest_report, "r", encoding="utf-8") as f:
                content = f.read()
                print(content)
        except (OSError, IOError, PermissionError) as e:
            print_error(f"Cannot read report: {e}")
            return 1
    
    # 导出报告（如果指定了输出路径）
    if hasattr(args, 'output') and args.output:
        latest_report = reports[0][0]
        
        try:
            with open(latest_report, "r", encoding="utf-8") as f:
                content = f.read()
            
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(content)
            
            print_success(f"Report exported to: {args.output}")
        except (OSError, IOError, PermissionError) as e:
            print_error(f"Cannot export report: {e}")
            return 1
    
    return 0


# =============================================================================
# 命令映射
# =============================================================================

# 命令名称到函数的映射
COMMAND_MAP = {
    "preview": cmd_preview,
    "run": cmd_run,
    "report": cmd_report,
}


def execute_command(command: str, args) -> int:
    """
    执行指定的命令。
    
    Args:
        command: 命令名称
        args: 解析后的参数
        
    Returns:
        退出码
    """
    if command not in COMMAND_MAP:
        print_error(f"Unknown command: {command}")
        return 1
    
    return COMMAND_MAP[command](args)
