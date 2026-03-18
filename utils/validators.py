"""Input validation utilities for the image organizer tool."""

import os
import re
import sys
from typing import Optional

from .config import DEFAULT_IMAGE_EXTENSIONS


def validate_source_dir(path: str) -> bool:
    """Validate that the source directory exists and is accessible."""
    if not os.path.exists(path):
        print(f"Error: Source directory '{path}' does not exist.", file=sys.stderr)
        return False
    if not os.path.isdir(path):
        print(f"Error: '{path}' is not a directory.", file=sys.stderr)
        return False
    return True


def validate_output_dir(path: str) -> bool:
    """Validate or create the output directory."""
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as e:
            print(f"Error: Cannot create output directory '{path}': {e}", file=sys.stderr)
            return False
    if not os.path.isdir(path):
        print(f"Error: '{path}' is not a directory.", file=sys.stderr)
        return False
    return True


def validate_extensions(ext_string: Optional[str]) -> set[str]:
    """Validate and parse extension string, return set of valid extensions."""
    if ext_string is None:
        return DEFAULT_IMAGE_EXTENSIONS.copy()
    
    exts = set()
    for ext in ext_string.split(','):
        ext = ext.strip().lower()
        if not ext.startswith('.'):
            ext = '.' + ext
        if re.match(r'^\.[a-z0-9]+$', ext):
            exts.add(ext)
        else:
            print(f"Warning: Invalid extension '{ext}' ignored.", file=sys.stderr)
    
    if not exts:
        print("Warning: No valid extensions provided, using defaults.", file=sys.stderr)
        return DEFAULT_IMAGE_EXTENSIONS.copy()
    
    return exts


def confirm_action() -> bool:
    """Prompt user for confirmation before executing actions."""
    try:
        response = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
        return response in ('yes', 'y')
    except (EOFError, KeyboardInterrupt):
        return False
