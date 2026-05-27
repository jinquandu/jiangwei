#!/usr/bin/env python3
"""
功能:
- 读取一个 *_v1.fea 文件，提取 player_feature 列并展开为带 p0_/p1_ 前缀的真实字段名。

输入:
- --fea: 可选，指定 fea 文件名（默认读取 fea 目录第一个 *_v1.fea）
- --output: 可选，字段名输出文本文件

输出:
- 控制台输出展开后的 player_feature 字段名（以及 game_feature 字段名）
- 可选输出文本文件
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

FEA_DIR = PROJECT_ROOT / "fea"


def pick_one_fea_file(fea_name: str | None = None) -> Path:
    if fea_name:
        candidate = FEA_DIR / fea_name
        if not candidate.exists():
            raise FileNotFoundError(f"fea file not found: {candidate}")
        return candidate

    candidates = sorted(FEA_DIR.glob("*_v1.fea"))
    if not candidates:
        raise FileNotFoundError(f"no *_v1.fea files found in {FEA_DIR}")
    return candidates[0]


def load_one_tick_feature(fea_path: Path):
    with open(fea_path, "rb") as f:
        feature_dict = pickle.load(f)

    for tick_key in feature_dict:
        one_tick_feature = feature_dict[tick_key]
        if "player_feature" in one_tick_feature:
            return tick_key, one_tick_feature

    raise ValueError(f"no player_feature found in {fea_path}")


def expand_player_feature_columns(player_df) -> list[str]:
    """
    把 player_feature 的列名展开成:
    p0_xxx, p0_yyy, ..., p1_xxx, p1_yyy, ...
    """
    expanded_columns: list[str] = []
    player_df = player_df.reset_index(drop=True)

    for player_idx in range(len(player_df)):
        for col_name in player_df.columns:
            expanded_columns.append(f"p{player_idx}_{col_name}")

    return expanded_columns


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect one v1 fea file and expand player_feature column names with p0_/p1_ prefixes."
    )
    parser.add_argument(
        "--fea",
        default="",
        help="Specific *_v1.fea file name under fea/. If omitted, the first one is used.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional output txt file path relative to project root.",
    )
    args = parser.parse_args()

    fea_path = pick_one_fea_file(args.fea or None)
    tick_key, one_tick_feature = load_one_tick_feature(fea_path)

    player_df = one_tick_feature["player_feature"]
    game_df = one_tick_feature.get("game_feature")

    expanded_player_columns = expand_player_feature_columns(player_df)
    game_columns = list(game_df.columns) if game_df is not None else []

    lines: list[str] = []
    # lines.append(f"fea_file: {fea_path}")
    # lines.append(f"tick_key: {tick_key}")
    # lines.append(f"player_feature_shape: {player_df.shape}")
    # lines.append(f"game_feature_shape: {None if game_df is None else game_df.shape}")
    # lines.append("")
    # lines.append("expanded_player_feature_columns:")
    lines.extend(expanded_player_columns)
    # lines.append("")
    # lines.append("game_feature_columns:")
    lines.extend(game_columns)

    output_text = "\n".join(lines)
    print(output_text)

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = PROJECT_ROOT / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")
        print(f"\nsaved to: {output_path}")


if __name__ == "__main__":
    main()