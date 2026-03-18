"""Core organization rules engine for image classification and path generation."""

import os
from typing import Dict, List, Tuple

from utils.config import SCREENSHOT_KEYWORDS, CATEGORIES, ORGANIZED_DIR
from utils.helpers import get_file_modified_date


def classify_file(filename: str) -> str:
    """Classify file based on filename keywords."""
    filename_lower = filename.lower()
    for keyword in SCREENSHOT_KEYWORDS:
        if keyword.lower() in filename_lower:
            return "Screenshots"
    return "Other"


def generate_target_path(filepath: str, source_dir: str) -> str:
    """Generate the target path for a file based on organization rules."""
    filename = os.path.basename(filepath)
    file_date = get_file_modified_date(filepath)
    category = classify_file(filename)
    
    date_dir = file_date
    category_dir = category
    
    target_dir = os.path.join(ORGANIZED_DIR, date_dir, category_dir)
    target_path = os.path.join(target_dir, filename)
    
    return target_path


def resolve_conflict(target_path: str) -> str:
    """Resolve filename conflicts by adding numeric suffix."""
    if not os.path.exists(target_path):
        return target_path
    
    base, ext = os.path.splitext(target_path)
    counter = 1
    while True:
        new_path = f"{base}_{counter}{ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def generate_organization_plan(
    files: List[str],
    source_dir: str
) -> List[Tuple[str, str]]:
    """Generate complete organization plan for all files."""
    plan = []
    for filepath in files:
        try:
            target_path = generate_target_path(filepath, source_dir)
            final_target = resolve_conflict(target_path)
            plan.append((filepath, final_target))
        except Exception:
            continue
    return plan
