#!/usr/bin/env bash
# 把工作区的每个 skills/<name> 软链到目标 agent CLI 的 skills 目录，使其全局可发现。
# skill 源码（SKILL.md + YAML frontmatter name/description）在 Claude Code 与 Codex
# 两边格式通用，仅安装目录不同——一次开发、两边复用。
#
# 用法：
#   bash scripts/link-skills.sh             # 默认：Claude Code（~/.claude/skills）
#   bash scripts/link-skills.sh codex       # Codex（~/.codex/skills）
#   bash scripts/link-skills.sh all         # 两者都链
#   bash scripts/link-skills.sh /custom/dir # 自定义目标目录直接装
#   DEST_DIR=/custom/dir bash scripts/link-skills.sh codex  # 覆盖某平台的默认目录
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/skills"
PLATFORM="${1:-claude}"

link_to() {
  local dest="$1"
  mkdir -p "$dest"
  for skill_dir in "$SRC_DIR"/*/; do
    [ -d "$skill_dir" ] || continue
    local name
    name=$(basename "$skill_dir")
    ln -sfn "$skill_dir" "$dest/$name"
    echo "linked: $name"
  done
}

case "$PLATFORM" in
  claude)
    link_to "${DEST_DIR:-$HOME/.claude/skills}" ;;
  codex)
    link_to "${DEST_DIR:-$HOME/.codex/skills}" ;;
  all)
    link_to "$HOME/.claude/skills"
    echo "---"
    link_to "$HOME/.codex/skills" ;;
  *)
    # 任意其它参数当作自定义目标目录
    link_to "$PLATFORM" ;;
esac
