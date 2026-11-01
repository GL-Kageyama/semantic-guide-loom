#!/usr/bin/env bash
#
# semantic-guide-loom installer
#
# このリポジトリの Skill（説明の映像を焼く手順）を、Claude Code の検出場所へ入れる。
#
# Usage:
#   ./install.sh            # Global: ~/.claude/skills/（どのプロジェクトからも呼べる）
#   ./install.sh --local    # Project: .claude/skills/（このリポジトリのみ）
#   ./install.sh --uninstall
#
# 入れるのは symlink：正本は ./skills/ のまま。リポジトリへの編集が即反映される。
#
# ⚠️ 呼び出し名には名前空間が付く——`/semantic-guide-loom:semantic-guide-loom`。

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$REPO_DIR/skills"

#: 入れる Skill の名。**`skills/` の下のディレクトリ名と一致する。**
SKILLS=(semantic-guide-loom)

MODE="global"
ACTION="install"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --local)     MODE="local" ;;
    --global)    MODE="global" ;;
    --uninstall) ACTION="uninstall" ;;
    -h|--help)
      echo "Usage: ./install.sh [--local|--global] [--uninstall]"
      echo ""
      echo "  --local      .claude/skills/ へ入れる（このリポジトリだけ）"
      echo "  --global     ~/.claude/skills/ へ入れる（既定。どこからでも呼べる）"
      echo "  --uninstall  入れた Skill を消す（既定の行き先から）"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

if [[ "$MODE" == "local" ]]; then
  TARGET_DIR="$REPO_DIR/.claude/skills"
else
  TARGET_DIR="$HOME/.claude/skills"
fi

if [[ "$ACTION" == "uninstall" ]]; then
  echo "==> Uninstalling from: $TARGET_DIR"
  for name in "${SKILLS[@]}"; do
    target="$TARGET_DIR/$name"
    if [[ -L "$target" || -e "$target" ]]; then
      rm -rf "$target"
      echo "    ✓ removed $name"
    else
      echo "    (not installed) $name"
    fi
  done
  exit 0
fi

# ⚠️ **先に全部を確かめてから張る。** 途中で欠けていると、
#    **入ったように見えて Skill が揃っていない**という壊れ方をする。
for name in "${SKILLS[@]}"; do
  if [[ ! -f "$SKILLS_DIR/$name/SKILL.md" ]]; then
    echo "    ✗ missing: skills/$name/SKILL.md" >&2
    exit 1
  fi
done

echo "==> Installing ${#SKILLS[@]} skill(s) to: $TARGET_DIR"
mkdir -p "$TARGET_DIR"
for name in "${SKILLS[@]}"; do
  target="$TARGET_DIR/$name"
  rm -rf "$target"              # 前回のインストール（symlink かファイル）を除去
  if [[ "$MODE" == "local" ]]; then
    # ⚠️ **リポジトリの中は相対で張る。** 絶対で張ると、clone した人の環境では
    #    リンクが他人のホームを指す——コミットされるのはこの形だからである。
    ln -s "../../skills/$name" "$target"
  else
    # ⚠️ **ホームの側は絶対で張る。**
    ln -s "$SKILLS_DIR/$name" "$target"
  fi
  echo "    ✓ $name"
done

echo ""
echo "==> Done. Callable as:"
for name in "${SKILLS[@]}"; do
  echo "      /semantic-guide-loom:$name"
done
echo ""
echo "    Note: restart Claude Code or run /skills once to reload the listing."
