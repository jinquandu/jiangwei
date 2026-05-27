#!/usr/bin/env python3
"""
功能:
- 对比 match 目录中的 .mad 文件与 fea 目录中的 .fea 文件，统计缺失和多余项。

输入:
- --match-dir: .mad 文件目录（默认 match）
- --fea-dir: .fea 文件目录（默认 fea）
- --output: 可选，缺失 .mad 清单输出文件

输出:
- 控制台统计信息（match_count/fea_count/common_count/missing_count/extra_count）
- 可选输出文件（每行一个缺失的 .mad 文件名）
"""

from __future__ import annotations

import argparse
from pathlib import Path


def collect_match_stems(match_dir: Path) -> set[str]:
    return {path.stem for path in match_dir.glob("*.mad") if path.is_file()}


def collect_fea_stems(fea_dir: Path) -> set[str]:
    stems: set[str] = set()
    for path in fea_dir.glob("*.fea"):
        if not path.is_file():
            continue
        stem = path.stem
        if stem.endswith("_v1"):
            stem = stem[:-3]
        stems.add(stem)
    return stems


def build_report(match_dir: Path, fea_dir: Path) -> tuple[list[str], list[str], list[str]]:
    match_stems = collect_match_stems(match_dir)
    fea_stems = collect_fea_stems(fea_dir)
    missing = sorted(match_stems - fea_stems)
    extra = sorted(fea_stems - match_stems)
    common = sorted(match_stems & fea_stems)
    return missing, extra, common


def main() -> None:
    parser = argparse.ArgumentParser(description="Check which match files are missing fea outputs.")
    parser.add_argument("--match-dir", default="match", help="Directory containing .mad files")
    parser.add_argument("--fea-dir", default="fea", help="Directory containing .fea files")
    parser.add_argument(
        "--output",
        default="",
        help="Optional output file to save the missing match list (one stem per line)",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    match_dir = (base_dir / args.match_dir).resolve()
    fea_dir = (base_dir / args.fea_dir).resolve()

    if not match_dir.exists() or not match_dir.is_dir():
        raise SystemExit(f"match_dir not found or not a directory: {match_dir}")
    if not fea_dir.exists() or not fea_dir.is_dir():
        raise SystemExit(f"fea_dir not found or not a directory: {fea_dir}")

    missing, extra, common = build_report(match_dir, fea_dir)

    print(f"match_count={len(list(match_dir.glob('*.mad')))}")
    print(f"fea_count={len(list(fea_dir.glob('*.fea')))}")
    print(f"common_count={len(common)}")
    print(f"missing_count={len(missing)}")
    print(f"extra_count={len(extra)}")

    if missing:
        print("missing_match_files:")
        for stem in missing:
            print(f"- {stem}.mad")

    if extra:
        print("extra_fea_files:")
        for stem in extra:
            print(f"- {stem}.fea")

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = base_dir / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for stem in missing:
                f.write(f"{stem}.mad\n")
        print(f"Saved missing list to {output_path}")


if __name__ == "__main__":
    main()
