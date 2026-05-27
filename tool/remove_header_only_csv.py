#!/usr/bin/env python3
"""
功能:
- 删除仅包含表头、没有有效数据行的 CSV 文件。

输入:
- dir: 目标目录（默认 url_dir）
- --recursive: 是否递归扫描子目录
- --dry-run: 仅预览将删除的文件，不执行删除

输出:
- 控制台输出扫描结果与删除统计
- 非 dry-run 模式下实际删除匹配文件
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def is_non_empty_row(row: list[str]) -> bool:
    return any(cell.strip() for cell in row)


def is_header_only_csv(file_path: Path) -> bool:
    """Return True if CSV has exactly one non-empty row (the header)."""
    try:
        with file_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)

            # Find first non-empty row as header.
            for row in reader:
                if is_non_empty_row(row):
                    break
            else:
                # Empty file: not treated as header-only.
                return False

            # If any subsequent non-empty row exists, it has data.
            for row in reader:
                if is_non_empty_row(row):
                    return False

            return True
    except Exception as exc:
        print(f"[SKIP] {file_path} (read error: {exc})")
        return False


def collect_csv_files(root: Path, recursive: bool) -> list[Path]:
    pattern = "**/*.csv" if recursive else "*.csv"
    return sorted(p for p in root.glob(pattern) if p.is_file())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete CSV files that contain only a header row.",
    )
    parser.add_argument(
        "dir",
        nargs="?",
        default="url_dir",
        help="Target directory (default: url_dir)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan CSV files recursively.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview files that would be deleted without deleting.",
    )
    args = parser.parse_args()

    root = Path(args.dir)
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Directory does not exist or is not a folder: {root}")

    csv_files = collect_csv_files(root, args.recursive)
    if not csv_files:
        print("No CSV files found.")
        return

    to_delete = [p for p in csv_files if is_header_only_csv(p)]

    if not to_delete:
        print("No header-only CSV files found.")
        return

    mode = "DRY-RUN" if args.dry_run else "DELETE"
    print(f"[{mode}] Found {len(to_delete)} header-only CSV file(s):")

    deleted = 0
    for p in to_delete:
        print(f" - {p}")
        if not args.dry_run:
            try:
                p.unlink()
                deleted += 1
            except Exception as exc:
                print(f"   [FAILED] {exc}")

    if args.dry_run:
        print("Dry run complete. No files were deleted.")
    else:
        print(f"Deleted {deleted}/{len(to_delete)} file(s).")


if __name__ == "__main__":
    main()
