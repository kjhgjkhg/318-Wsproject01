"""Helper functions for file operations and report generation."""

import os
import datetime
from typing import Dict, List, Tuple, Optional

from .config import DATE_FORMAT, REPORT_DATE_FORMAT


def get_file_modified_date(filepath: str) -> str:
    """Get the modified date of a file in YYYY-MM format."""
    try:
        mtime = os.path.getmtime(filepath)
        dt = datetime.datetime.fromtimestamp(mtime)
        return dt.strftime(DATE_FORMAT)
    except OSError:
        return datetime.datetime.now().strftime(DATE_FORMAT)


def get_file_size(filepath: str) -> int:
    """Get file size in bytes, return 0 on error."""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0


def format_file_size(size: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def format_table_row(items: List[str], widths: List[int]) -> str:
    """Format a row for report table."""
    return " | ".join(f"{item:<{w}}" for item, w in zip(items, widths))


def get_report_filename() -> str:
    """Generate report filename with current date."""
    today = datetime.datetime.now().strftime(REPORT_DATE_FORMAT)
    return f"organize_report_{today}.txt"


def ensure_directory(path: str) -> bool:
    """Ensure directory exists, create if not."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False


def is_protected_path(filepath: str, source_dir: str) -> bool:
    """Check if path is protected (should not be modified)."""
    filename = os.path.basename(filepath)
    if filename == '.do_not_touch.cfg':
        return True
    if os.path.abspath(filepath) == os.path.abspath(source_dir):
        return True
    return False
