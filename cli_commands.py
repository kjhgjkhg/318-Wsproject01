"""CLI command implementations for organize subcommands."""

import os
import datetime
from typing import Any

from organize_engine import (
    scan_directory,
    generate_preview,
    execute_organization
)
from core_organizer import generate_organization_plan
from utils.validators import (
    validate_source_dir,
    validate_output_dir,
    validate_extensions,
    confirm_action
)
from utils.helpers import (
    format_file_size,
    get_file_size,
    get_report_filename,
    ensure_directory
)
from utils.config import (
    SOURCE_DIR,
    OUTPUT_DIR,
    REPORT_DATE_FORMAT
)

_last_report: Any = None


def save_report(result: Any) -> str:
    """Save operation result to report file."""
    global _last_report
    _last_report = result
    
    ensure_directory(OUTPUT_DIR)
    report_filename = get_report_filename()
    report_path = os.path.join(OUTPUT_DIR, report_filename)
    
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("IMAGE ORGANIZATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Files Processed: {result.total_files}\n")
            f.write(f"Successful: {len(result.success)}\n")
            f.write(f"Failed: {len(result.failed)}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("SUCCESSFUL OPERATIONS\n")
            f.write("-" * 80 + "\n\n")
            for src, dst in result.success:
                size = format_file_size(get_file_size(dst))
                f.write(f"From: {src}\n")
                f.write(f"To:   {dst}\n")
                f.write(f"Size: {size}\n\n")
            
            if result.failed:
                f.write("-" * 80 + "\n")
                f.write("FAILED OPERATIONS\n")
                f.write("-" * 80 + "\n\n")
                for src, dst, error in result.failed:
                    f.write(f"From: {src}\n")
                    f.write(f"To:   {dst}\n")
                    f.write(f"Error: {error}\n\n")
            
            f.write("=" * 80 + "\n")
        return report_path
    except OSError:
        return ""


def cmd_preview(args: Any) -> int:
    """Preview organization plan command."""
    extensions = validate_extensions(getattr(args, 'ext', None))
    
    if not validate_source_dir(SOURCE_DIR):
        return 1
    
    files = scan_directory(SOURCE_DIR, extensions)
    
    if not files:
        print("No image files found.")
        return 0
    
    plan = generate_organization_plan(files, SOURCE_DIR)
    preview = generate_preview(plan, SOURCE_DIR)
    
    print(f"\nFound {preview['total']} image files:\n")
    print("-" * 80)
    
    for item in preview['files']:
        print(f"Source: {item['source']}")
        print(f"Target: {item['target']}")
        print(f"Size:   {item['size_formatted']}")
        print()
    
    print("-" * 80)
    print(f"Total: {preview['total']} files")
    
    return 0


def cmd_run(args: Any) -> int:
    """Execute organization command."""
    extensions = validate_extensions(getattr(args, 'ext', None))
    dry_run = getattr(args, 'dry_run', False)
    move = getattr(args, 'move', False)
    confirmed = getattr(args, 'yes', False)
    
    if not validate_source_dir(SOURCE_DIR):
        return 1
    
    if not validate_output_dir(OUTPUT_DIR):
        return 1
    
    files = scan_directory(SOURCE_DIR, extensions)
    
    if not files:
        print("No image files found.")
        return 0
    
    plan = generate_organization_plan(files, SOURCE_DIR)
    
    if dry_run:
        print("DRY RUN MODE - Showing preview only:\n")
        cmd_preview(args)
        return 0
    
    if not confirmed:
        print(f"\nThis will {'move' if move else 'copy'} {len(files)} files.")
        if not confirm_action():
            print("Operation cancelled.")
            return 0
    
    result = execute_organization(plan, SOURCE_DIR, move=move)
    report_path = save_report(result)
    
    print(f"\nOperation complete:")
    print(f"  Total files:   {result.total_files}")
    print(f"  Successful:    {len(result.success)}")
    print(f"  Failed:        {len(result.failed)}")
    
    if report_path:
        print(f"\nReport saved to: {report_path}")
    
    if result.failed:
        print(f"\nFailed operations:")
        for src, dst, error in result.failed[:5]:
            print(f"  {src}: {error}")
        if len(result.failed) > 5:
            print(f"  ... and {len(result.failed) - 5} more")
    
    return 0


def cmd_report(args: Any) -> int:
    """Show last organization report command."""
    global _last_report
    
    if _last_report is None:
        print("No recent report available.")
        print("Looking for saved reports...")
        
        ensure_directory(OUTPUT_DIR)
        reports = []
        try:
            for f in os.listdir(OUTPUT_DIR):
                if f.startswith('organize_report_') and f.endswith('.txt'):
                    reports.append(f)
        except OSError:
            pass
        
        if not reports:
            print("No saved reports found.")
            return 1
        
        reports.sort(reverse=True)
        latest = os.path.join(OUTPUT_DIR, reports[0])
        try:
            with open(latest, 'r', encoding='utf-8') as f:
                print(f.read())
            return 0
        except OSError as e:
            print(f"Error reading report: {e}")
            return 1
    
    print(f"Total Files: {_last_report.total_files}")
    print(f"Successful:  {len(_last_report.success)}")
    print(f"Failed:      {len(_last_report.failed)}")
    
    if _last_report.success:
        print("\nSuccessful operations:")
        for src, dst in _last_report.success[:10]:
            print(f"  {src} -> {dst}")
    
    return 0
