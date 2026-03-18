"""Engine for file traversal, copy/move operations, and preview generation."""

import os
import shutil
from typing import Dict, List, Tuple, Any

from core_organizer import generate_organization_plan
from utils.helpers import (
    get_file_size,
    format_file_size,
    ensure_directory,
    is_protected_path
)
from utils.config import SOURCE_DIR


class OperationResult:
    """Stores results of file operations."""
    
    def __init__(self):
        self.success: List[Tuple[str, str]] = []
        self.failed: List[Tuple[str, str, str]] = []
        self.total_files: int = 0
    
    def add_success(self, src: str, dst: str) -> None:
        """Add a successful operation."""
        self.success.append((src, dst))
    
    def add_failure(self, src: str, dst: str, error: str) -> None:
        """Add a failed operation."""
        self.failed.append((src, dst, error))


def scan_directory(source_dir: str, extensions: set[str]) -> List[str]:
    """Scan directory for image files matching extensions."""
    image_files = []
    try:
        for root, dirs, files in os.walk(source_dir):
            organized_path = os.path.join(source_dir, "organized")
            if os.path.abspath(root).startswith(os.path.abspath(organized_path)):
                continue
            for filename in files:
                filepath = os.path.join(root, filename)
                if is_protected_path(filepath, source_dir):
                    continue
                ext = os.path.splitext(filename)[1].lower()
                if ext in extensions:
                    image_files.append(filepath)
    except OSError:
        pass
    return image_files


def generate_preview(plan: List[Tuple[str, str]], source_dir: str) -> Dict[str, Any]:
    """Generate preview information for organization plan."""
    preview = []
    for src, dst in plan:
        try:
            size = get_file_size(src)
            preview.append({
                "source": src,
                "target": dst,
                "size": size,
                "size_formatted": format_file_size(size)
            })
        except Exception:
            continue
    return {
        "files": preview,
        "total": len(plan)
    }


def copy_file(src: str, dst: str) -> Tuple[bool, str]:
    """Copy a file from source to destination."""
    try:
        dst_dir = os.path.dirname(dst)
        if not ensure_directory(dst_dir):
            return False, "Failed to create target directory"
        shutil.copy2(src, dst)
        return True, ""
    except OSError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def move_file(src: str, dst: str) -> Tuple[bool, str]:
    """Move a file from source to destination."""
    try:
        dst_dir = os.path.dirname(dst)
        if not ensure_directory(dst_dir):
            return False, "Failed to create target directory"
        shutil.move(src, dst)
        return True, ""
    except OSError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def execute_organization(
    plan: List[Tuple[str, str]],
    source_dir: str,
    move: bool = False
) -> OperationResult:
    """Execute the organization plan."""
    result = OperationResult()
    result.total_files = len(plan)
    
    for src, dst in plan:
        if is_protected_path(src, source_dir):
            result.add_failure(src, dst, "Protected file")
            continue
        
        if move:
            success, error = move_file(src, dst)
        else:
            success, error = copy_file(src, dst)
        
        if success:
            result.add_success(src, dst)
        else:
            result.add_failure(src, dst, error)
    
    return result
