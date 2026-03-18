"""Constants and configuration for the image organizer tool."""

import os

SOURCE_DIR: str = "./source_data/"
OUTPUT_DIR: str = "./output_build/"
ORGANIZED_DIR: str = os.path.join(SOURCE_DIR, "organized")

DEFAULT_IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

SCREENSHOT_KEYWORDS: list[str] = ["截图", "screenshot", "Snip", "snip"]

CATEGORIES: list[str] = ["Screenshots", "Memes", "Downloads", "Other"]

DATE_FORMAT: str = "%Y-%m"

REPORT_DATE_FORMAT: str = "%Y%m%d"
