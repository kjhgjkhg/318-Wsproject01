"""
图片自动整理工具 - 命令行入口。

这是一个模块化的、可维护的Python桌面截图与图片自动整理工具（CLI版）。
用于扫描指定目录中的图片/截图文件，自动按规则整理，并生成整理报告。

使用方法:
    python main.py organize preview [--ext png,jpg]
    python main.py organize run --yes [--move] [--ext png,jpg]
    python main.py organize report [--show]

作者: AI Assistant
版本: 1.0.0
"""

import sys
import argparse
from typing import Optional, List

from utils.config import (
    get_source_path,
    get_output_path,
    get_all_extensions_list,
)
from cli_commands import execute_command, cmd_preview, cmd_run, cmd_report


# =============================================================================
# 版本信息
# =============================================================================

__version__ = "1.0.0"
__author__ = "AI Assistant"


# =============================================================================
# ArgumentParser 设置
# =============================================================================

def create_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器。
    
    Returns:
        配置好的ArgumentParser实例
    """
    parser = argparse.ArgumentParser(
        prog="img-organizer",
        description="""
图片自动整理工具 - 扫描、分类、整理您的图片文件。

此工具会扫描 ./source_data/ 目录中的图片文件，
按照日期和类型自动整理到 ./source_data/organized/ 目录下，
并生成详细的整理报告保存到 ./output_build/。
        """.strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 预览整理计划
  python main.py organize preview
  
  # 预览特定类型的文件
  python main.py organize preview --ext png,jpg
  
  # 执行整理（复制模式，默认）
  python main.py organize run --yes
  
  # 执行整理（移动模式）
  python main.py organize run --yes --move
  
  # 查看报告
  python main.py organize report --show

更多信息: https://github.com/kjhgjkhg/318-Wsproject01
        """.strip()
    )
    
    # 版本信息
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    # 子命令
    subparsers = parser.add_subparsers(
        dest="command",
        help="可用命令",
        metavar="COMMAND"
    )
    
    # -------------------------------------------------------------------------
    # organize 子命令
    # -------------------------------------------------------------------------
    organize_parser = subparsers.add_parser(
        "organize",
        help="整理图片文件",
        description="整理图片文件到结构化目录"
    )
    
    organize_subparsers = organize_parser.add_subparsers(
        dest="organize_command",
        help="整理子命令",
        metavar="ACTION"
    )
    
    # ----- preview 子命令 -----
    preview_parser = organize_subparsers.add_parser(
        "preview",
        help="预览整理计划（不实际执行）",
        description="预览整理计划，显示每个文件将被整理到哪里"
    )
    
    preview_parser.add_argument(
        "--ext",
        type=str,
        default=None,
        metavar="EXTENSIONS",
        help=f"指定文件扩展名，逗号分隔。默认: {', '.join(get_all_extensions_list())}"
    )
    
    preview_parser.add_argument(
        "--max-preview",
        type=int,
        default=20,
        metavar="N",
        help="控制台预览最多显示的文件数量（默认: 20）"
    )
    
    preview_parser.set_defaults(func=cmd_preview)
    
    # ----- run 子命令 -----
    run_parser = organize_subparsers.add_parser(
        "run",
        help="执行整理操作",
        description="执行实际的整理操作。默认复制文件，源文件保留。"
    )
    
    run_parser.add_argument(
        "--yes",
        action="store_true",
        default=False,
        help="确认执行操作（必须指定，否则拒绝执行）"
    )
    
    run_parser.add_argument(
        "--move",
        action="store_true",
        default=False,
        help="移动文件而非复制（源文件将被删除）"
    )
    
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="试运行模式（显示操作但不实际执行）"
    )
    
    run_parser.add_argument(
        "--ext",
        type=str,
        default=None,
        metavar="EXTENSIONS",
        help=f"指定文件扩展名，逗号分隔。默认: {', '.join(get_all_extensions_list())}"
    )
    
    run_parser.set_defaults(func=cmd_run)
    
    # ----- report 子命令 -----
    report_parser = organize_subparsers.add_parser(
        "report",
        help="查看整理报告",
        description="查看或导出上次整理的详细报告"
    )
    
    report_parser.add_argument(
        "--show",
        action="store_true",
        default=False,
        help="显示最新报告的详细内容"
    )
    
    report_parser.add_argument(
        "--output",
        type=str,
        default=None,
        metavar="PATH",
        help="导出报告到指定路径"
    )
    
    report_parser.set_defaults(func=cmd_report)
    
    return parser


# =============================================================================
# 主函数
# =============================================================================

def main(argv: Optional[List[str]] = None) -> int:
    """
    主入口函数。
    
    Args:
        argv: 命令行参数列表，None则使用sys.argv
        
    Returns:
        退出码（0成功，非0失败）
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        return 0
    
    # 处理 organize 命令
    if args.command == "organize":
        if not args.organize_command:
            print("Error: organize command requires an action (preview/run/report)")
            print("Use 'organize --help' for more information")
            return 1
        
        # 执行对应的子命令函数
        if hasattr(args, 'func'):
            return args.func(args)
        else:
            print(f"Error: Unknown organize action: {args.organize_command}")
            return 1
    
    # 未知命令
    print(f"Error: Unknown command: {args.command}")
    return 1


# =============================================================================
# 程序入口
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
