#!/usr/bin/env bash
# 把工作区的每个 skills/<name> 软链到 ~/.claude/skills/<name>，使其全局可发现
set -euo pipefail
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/skills"
DEST_DIR="$HOME/.claude/skills"
mkdir -p "$DEST_DIR"
for skill_dir in "$SRC_DIR"/*/; do
  [ -d "$skill_dir" ] || continue
  name=$(basename "$skill_dir")
  ln -sfn "$skill_dir" "$DEST_DIR/$name"
  echo "linked: $name"
done
