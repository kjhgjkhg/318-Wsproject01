"""
cli_commands.py - CLI子命令实现模块

实现 preview / run / report 三个子命令的具体逻辑。
处理用户交互、结果显示和错误处理。
"""
import os
from datetime import datetime
from typing import Dict, List, Optional, Set

from core_organizer import OrganizeRule, OrganizerEngine
from organize_engine import FileScanner, OrganizeExecutor
from utils.config import (
    DEFAULT_EXTENSIONS,
    OUTPUT_DIR,
    REPORT_DATE_FORMAT,
    REPORT_PREFIX,
    REPORT_SUFFIX,
    SOURCE_DIR
)
from utils.helpers import (
    format_file_size,
    load_success_log,
    write_report
)
from utils.validators import (
    validate_extensions,
    validate_path_exists,
    validate_source_directory,
    validate_yes_confirmation
)


class PreviewCommand:
    """
    preview 子命令实现：预览整理计划。
    """

    def __init__(
        self,
        source_dir: str = SOURCE_DIR,
        extensions: Optional[Set[str]] = None
    ) -> None:
        """
        初始化预览命令。

        Args:
            source_dir: 源扫描目录
            extensions: 允许的扩展名集合
        """
        self.source_dir = source_dir
        self.extensions = extensions or DEFAULT_EXTENSIONS.copy()

    def execute(self) -> Dict[str, any]:
        """
        执行预览命令。

        Returns:
            预览结果字典
        """
        validate_source_directory(self.source_dir)

        scanner: FileScanner = FileScanner(
            source_dir=self.source_dir,
            extensions=self.extensions
        )

        files: List[str] = scanner.scan()

        rule: OrganizeRule = OrganizeRule()
        engine: OrganizerEngine = OrganizerEngine(
            source_dir=self.source_dir,
            output_base=self.source_dir,
            rule=rule
        )

        plan: List[Dict[str, str]] = engine.create_plan(files)

        return {
            "total_files": len(files),
            "plan": plan,
            "source_dir": self.source_dir
        }

    def display(self, result: Dict[str, any]) -> None:
        """
        显示预览结果。

        Args:
            result: 预览结果字典
        """
        print("\n" + "=" * 80)
        print("整理预览 / Organization Preview")
        print("=" * 80)
        print(f"源目录: {result['source_dir']}")
        print(f"扫描到文件数: {result['total_files']}")
        print("-" * 80)

        plan: List[Dict[str, str]] = result.get("plan", [])

        if not plan:
            print("未找到符合条件的文件。")
            return

        print(f"\n{'序号':<6}{'原文件':<40}{'目标路径':<40}{'大小':<12}")
        print("-" * 100)

        for idx, item in enumerate(plan, 1):
            if "error" in item:
                print(f"{idx:<6}{item.get('original_name', 'N/A'):<40}{'[错误] ' + item['error']:<40}")
                continue

            old_name: str = item.get("original_name", "")
            target: str = item.get("target_path", "")
            size: str = format_file_size(int(item.get("size", 0)))

            old_display: str = old_name[:38] + ".." if len(old_name) > 40 else old_name
            target_display: str = os.path.basename(target)[:38] + ".." if len(os.path.basename(target)) > 40 else os.path.basename(target)

            print(f"{idx:<6}{old_display:<40}{target_display:<40}{size:<12}")

        print("-" * 100)
        print(f"共 {len(plan)} 个文件待整理")


class RunCommand:
    """
    run 子命令实现：执行整理操作。
    """

    def __init__(
        self,
        source_dir: str = SOURCE_DIR,
        extensions: Optional[Set[str]] = None,
        move_mode: bool = False,
        dry_run: bool = False,
        auto_confirm: bool = False
    ) -> None:
        """
        初始化运行命令。

        Args:
            source_dir: 源扫描目录
            extensions: 允许的扩展名集合
            move_mode: 是否移动模式
            dry_run: 是否仅预览
            auto_confirm: 是否自动确认
        """
        self.source_dir = source_dir
        self.extensions = extensions or DEFAULT_EXTENSIONS.copy()
        self.move_mode = move_mode
        self.dry_run = dry_run
        self.auto_confirm = auto_confirm

    def execute(self) -> Dict[str, any]:
        """
        执行运行命令。

        Returns:
            执行结果字典
        """
        validate_source_directory(self.source_dir)

        preview_cmd: PreviewCommand = PreviewCommand(
            source_dir=self.source_dir,
            extensions=self.extensions
        )
        preview_result: Dict[str, any] = preview_cmd.execute()

        if preview_result["total_files"] == 0:
            return {
                "success": True,
                "message": "未找到符合条件的文件，无需整理。",
                "total": 0,
                "success_count": 0,
                "failed_count": 0
            }

        preview_cmd.display(preview_result)

        if not self.auto_confirm:
            print("\n" + "-" * 40)
            mode_str: str = "移动" if self.move_mode else "复制"
            dry_str: str = "[预览模式] " if self.dry_run else ""
            print(f"{dry_str}即将{mode_str} {preview_result['total_files']} 个文件。")

            user_input: str = input("确认执行？(y/n): ").strip()
            if not validate_yes_confirmation(user_input):
                return {
                    "success": False,
                    "message": "用户取消操作。",
                    "total": preview_result["total_files"],
                    "success_count": 0,
                    "failed_count": 0
                }

        executor: OrganizeExecutor = OrganizeExecutor(
            source_dir=self.source_dir,
            output_base=self.source_dir,
            extensions=self.extensions,
            move_mode=self.move_mode
        )

        results: Dict[str, any] = executor.execute(
            plan=preview_result["plan"],
            dry_run=self.dry_run
        )

        report_path: str = executor.generate_report(results)

        return {
            "success": True,
            "total": results["total"],
            "success_count": results["success"],
            "failed_count": results["failed"],
            "report_path": report_path,
            "records": results.get("records", []),
            "failed_items": results.get("failed_items", [])
        }

    def display(self, result: Dict[str, any]) -> None:
        """
        显示执行结果。

        Args:
            result: 执行结果字典
        """
        print("\n" + "=" * 80)
        print("整理完成 / Organization Complete")
        print("=" * 80)

        if not result.get("success"):
            print(f"状态: 已取消")
            print(f"原因: {result.get('message', '未知')}")
            return

        print(f"总文件数: {result.get('total', 0)}")
        print(f"成功处理: {result.get('success_count', 0)}")
        print(f"失败数量: {result.get('failed_count', 0)}")

        if result.get("report_path"):
            print(f"报告路径: {result['report_path']}")

        failed_items: List[Dict[str, str]] = result.get("failed_items", [])
        if failed_items:
            print("\n失败项:")
            for item in failed_items:
                print(f"  - {item.get('path', '')}: {item.get('error', '')}")


class ReportCommand:
    """
    report 子命令实现：生成或查看整理报告。
    """

    def __init__(self, show_last: bool = True) -> None:
        """
        初始化报告命令。

        Args:
            show_last: 是否显示上次整理记录
        """
        self.show_last = show_last

    def execute(self) -> Dict[str, any]:
        """
        执行报告命令。

        Returns:
            报告结果字典
        """
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        date_str: str = datetime.now().strftime(REPORT_DATE_FORMAT)
        report_file: str = os.path.join(
            OUTPUT_DIR, f"{REPORT_PREFIX}{date_str}{REPORT_SUFFIX}"
        )

        last_records: List[Dict[str, str]] = load_success_log()

        if last_records:
            report_path: str = write_report(
                records=last_records,
                total_count=len(last_records),
                success_count=len(last_records),
                failed_count=0,
                failed_items=[]
            )

            return {
                "success": True,
                "report_path": report_path,
                "records": last_records,
                "total": len(last_records)
            }

        return {
            "success": False,
            "message": "未找到上次整理记录。",
            "report_path": "",
            "records": [],
            "total": 0
        }

    def display(self, result: Dict[str, any]) -> None:
        """
        显示报告结果。

        Args:
            result: 报告结果字典
        """
        print("\n" + "=" * 80)
        print("整理报告 / Organization Report")
        print("=" * 80)

        if not result.get("success"):
            print(result.get("message", "无法生成报告。"))
            return

        print(f"报告已生成: {result.get('report_path', '')}")
        print(f"记录数量: {result.get('total', 0)}")

        records: List[Dict[str, str]] = result.get("records", [])
        if records:
            print("\n最近整理记录:")
            print("-" * 80)
            for idx, record in enumerate(records[:10], 1):
                old_path: str = record.get("old_path", "")
                new_path: str = record.get("new_path", "")
                print(f"{idx}. {os.path.basename(old_path)} -> {os.path.basename(new_path)}")

            if len(records) > 10:
                print(f"... 还有 {len(records) - 10} 条记录")


def create_preview_command(
    source_dir: str,
    extensions: Optional[List[str]] = None
) -> PreviewCommand:
    """
    创建预览命令实例。

    Args:
        source_dir: 源目录
        extensions: 扩展名列表

    Returns:
        PreviewCommand 实例
    """
    ext_set: Set[str] = validate_extensions(extensions)
    return PreviewCommand(source_dir=source_dir, extensions=ext_set)


def create_run_command(
    source_dir: str,
    extensions: Optional[List[str]] = None,
    move_mode: bool = False,
    dry_run: bool = False,
    auto_confirm: bool = False
) -> RunCommand:
    """
    创建运行命令实例。

    Args:
        source_dir: 源目录
        extensions: 扩展名列表
        move_mode: 是否移动模式
        dry_run: 是否仅预览
        auto_confirm: 是否自动确认

    Returns:
        RunCommand 实例
    """
    ext_set: Set[str] = validate_extensions(extensions)
    return RunCommand(
        source_dir=source_dir,
        extensions=ext_set,
        move_mode=move_mode,
        dry_run=dry_run,
        auto_confirm=auto_confirm
    )


def create_report_command(show_last: bool = True) -> ReportCommand:
    """
    创建报告命令实例。

    Args:
        show_last: 是否显示上次记录

    Returns:
        ReportCommand 实例
    """
    return ReportCommand(show_last=show_last)
