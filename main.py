"""Main entry point for the image organizer CLI tool."""

import argparse
import sys

from cli_commands import cmd_preview, cmd_run, cmd_report


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog='image_organizer',
        description='Desktop screenshot and image auto-organizer tool'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    preview_parser = subparsers.add_parser(
        'preview',
        help='Preview organization plan without making changes'
    )
    preview_parser.add_argument(
        '--ext',
        type=str,
        help='Comma-separated list of extensions (e.g., png,jpg,webp)'
    )
    preview_parser.set_defaults(func=cmd_preview)
    
    run_parser = subparsers.add_parser(
        'run',
        help='Execute organization operation'
    )
    run_parser.add_argument(
        '--yes',
        action='store_true',
        help='Skip confirmation prompt'
    )
    run_parser.add_argument(
        '--move',
        action='store_true',
        help='Move files instead of copying (default: copy)'
    )
    run_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show preview only, do not execute'
    )
    run_parser.add_argument(
        '--ext',
        type=str,
        help='Comma-separated list of extensions (e.g., png,jpg,webp)'
    )
    run_parser.set_defaults(func=cmd_run)
    
    report_parser = subparsers.add_parser(
        'report',
        help='Show last organization report'
    )
    report_parser.set_defaults(func=cmd_report)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    if hasattr(args, 'func'):
        return args.func(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
