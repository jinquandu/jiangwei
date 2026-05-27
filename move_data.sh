#!/bin/zsh

set -e

TARGET_ROOT="../jiangwei_data"

move_if_exists() {
	local source_path="$1"
	local target_path="$2"

	if [[ ! -e "$source_path" ]]; then
		echo "[SKIP] source not found: $source_path"
		return 0
	fi

	mkdir -p "$(dirname "$target_path")"
	mv "$source_path" "$target_path"
	echo "[OK] moved: $source_path -> $target_path"
}

move_if_exists "./csv" "$TARGET_ROOT/csv"
move_if_exists "./match" "$TARGET_ROOT/match"
move_if_exists "./dota_replay" "$TARGET_ROOT/dota_replay"
move_if_exists "./decompress" "$TARGET_ROOT/decompress"
move_if_exists "./train_data.csv" "$TARGET_ROOT/train_data.csv"
move_if_exists "./fea" "$TARGET_ROOT/fea"