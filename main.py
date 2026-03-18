"""
main.py - CLI工具入口模块

命令行参数解析与子命令调度。
支持 preview / run / report 三个子命令。
"""
import argparse
import sys
from typing import List, Optional

from cli_commands import (
    PreviewCommand,
    RunCommand,
    ReportCommand,
    create_preview_command,
    create_run_command,
    create_report_command
)
from utils.config import DEFAULT_EXTENSIONS, SOURCE_DIR
from utils.validators import validate_extensions


def create_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器。

    Returns:
        配置好的 ArgumentParser 实例
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="organize",
        description="桌面截图与图片自动整理工具 - Desktop Screenshot & Image Organizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py organize preview              预览整理计划
  python main.py organize run --yes            执行整理（复制模式，自动确认）
  python main.py organize run --move --yes     执行整理（移动模式，自动确认）
  python main.py organize run --dry-run        预览模式（不实际操作）
  python main.py organize report               生成整理报告
        """
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 1.0.0"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="可用命令",
        description="支持的子命令",
        help="子命令帮助"
    )

    organize_parser = subparsers.add_parser(
        "organize",
        help="图片整理相关命令"
    )

    organize_subparsers = organize_parser.add_subparsers(
        dest="subcommand",
        title="整理子命令",
        description="整理操作类型",
        help="子命令帮助"
    )

    preview_parser = organize_subparsers.add_parser(
        "preview",
        help="预览整理计划（不执行实际操作）"
    )
    preview_parser.add_argument(
        "--source", "-s",
        type=str,
        default=SOURCE_DIR,
        help=f"源扫描目录 (默认: {SOURCE_DIR})"
    )
    preview_parser.add_argument(
        "--ext", "-e",
        type=str,
        default=None,
        help=f"指定扩展名，逗号分隔 (默认: {', '.join(sorted(DEFAULT_EXTENSIONS))})"
    )

    run_parser = organize_subparsers.add_parser(
        "run",
        help="执行整理操作"
    )
    run_parser.add_argument(
        "--source", "-s",
        type=str,
        default=SOURCE_DIR,
        help=f"源扫描目录 (默认: {SOURCE_DIR})"
    )
    run_parser.add_argument(
        "--ext", "-e",
        type=str,
        default=None,
        help=f"指定扩展名，逗号分隔 (默认: {', '.join(sorted(DEFAULT_EXTENSIONS))})"
    )
    run_parser.add_argument(
        "--move", "-m",
        action="store_true",
        help="移动模式（源文件将被移动），默认为复制模式"
    )
    run_parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="预览模式，只显示将执行的操作，不实际操作文件"
    )
    run_parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="自动确认，跳过交互确认"
    )

    report_parser = organize_subparsers.add_parser(
        "report",
        help="生成或查看整理报告"
    )
    report_parser.add_argument(
        "--last", "-l",
        action="store_true",
        help="显示上次整理记录"
    )

    return parser


def parse_extensions(ext_str: Optional[str]) -> Optional[List[str]]:
    """
    解析扩展名字符串。

    Args:
        ext_str: 逗号分隔的扩展名字符串

    Returns:
        扩展名列表，None 表示使用默认值
    """
    if ext_str is None:
        return None

    extensions: List[str] = []
    for ext in ext_str.split(","):
        clean: str = ext.strip().lower().lstrip(".")
        if clean:
            extensions.append(clean)

    return extensions if extensions else None


def handle_preview(args: argparse.Namespace) -> int:
    """
    处理 preview 子命令。

    Args:
        args: 解析后的参数

    Returns:
        退出码
    """
    extensions: Optional[List[str]] = parse_extensions(args.ext)

    try:
        cmd: PreviewCommand = create_preview_command(
            source_dir=args.source,
            extensions=extensions
        )
        result = cmd.execute()
        cmd.display(result)
        return 0
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return 1
    except PermissionError as e:
        print(f"权限错误: {e}")
        return 1
    except Exception as e:
        print(f"未知错误: {e}")
        return 1


def handle_run(args: argparse.Namespace) -> int:
    """
    处理 run 子命令。

    Args:
        args: 解析后的参数

    Returns:
        退出码
    """
    extensions: Optional[List[str]] = parse_extensions(args.ext)

    try:
        cmd: RunCommand = create_run_command(
            source_dir=args.source,
            extensions=extensions,
            move_mode=args.move,
            dry_run=args.dry_run,
            auto_confirm=args.yes
        )
        result = cmd.execute()
        cmd.display(result)

        if result.get("success"):
            return 0
        return 1
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return 1
    except PermissionError as e:
        print(f"权限错误: {e}")
        return 1
    except Exception as e:
        print(f"未知错误: {e}")
        return 1


def handle_report(args: argparse.Namespace) -> int:
    """
    处理 report 子命令。

    Args:
        args: 解析后的参数

    Returns:
        退出码
    """
    try:
        cmd: ReportCommand = create_report_command(show_last=args.last)
        result = cmd.execute()
        cmd.display(result)

        if result.get("success"):
            return 0
        return 1
    except Exception as e:
        print(f"错误: {e}")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """
    主入口函数。

    Args:
        argv: 命令行参数列表，None 时使用 sys.argv

    Returns:
        退出码
    """
    parser: argparse.ArgumentParser = create_parser()
    args: argparse.Namespace = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "organize":
        if args.subcommand is None:
            parser.parse_args(["organize", "--help"])
            return 0

        if args.subcommand == "preview":
            return handle_preview(args)
        elif args.subcommand == "run":
            return handle_run(args)
        elif args.subcommand == "report":
            return handle_report(args)
        else:
            print(f"未知子命令: {args.subcommand}")
            return 1

    print(f"未知命令: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
