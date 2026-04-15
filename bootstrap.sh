#!/usr/bin/env bash
#
# bootstrap.sh — install this repo's Claude Code config on a new machine.
#
# Symlinks skills, agents, commands, CLAUDE.md, and settings.json into
# $CLAUDE_DIR (default: ~/.claude). Never clobbers existing real files;
# updates existing symlinks; skips anything already present as a real file.
#
# Usage:
#   ./bootstrap.sh               # install, keeping existing files
#   ./bootstrap.sh --force       # replace existing files with symlinks (backs up first)
#   CLAUDE_DIR=/path ./bootstrap.sh   # install to a non-default location

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
FORCE=0

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    -h|--help)
      sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "unknown arg: $arg" >&2; exit 1 ;;
  esac
done

echo "Installing claude-config"
echo "  source: $REPO_DIR"
echo "  target: $CLAUDE_DIR"
echo

mkdir -p "$CLAUDE_DIR/skills" "$CLAUDE_DIR/agents" "$CLAUDE_DIR/commands"

backup_file() {
  local path="$1"
  local backup="${path}.backup-$(date +%Y%m%d-%H%M%S)"
  mv "$path" "$backup"
  echo "    backed up to: $backup"
}

link() {
  local src="$1" dst="$2"

  if [[ -L "$dst" ]]; then
    rm "$dst"
    ln -s "$src" "$dst"
    echo "  updated:  $dst"
    return
  fi

  if [[ -e "$dst" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
      echo "  replacing: $dst"
      backup_file "$dst"
      ln -s "$src" "$dst"
      echo "  linked:    $dst"
    else
      echo "  skipped (real file exists): $dst"
    fi
    return
  fi

  ln -s "$src" "$dst"
  echo "  linked:   $dst"
}

link_dir_contents() {
  local src_dir="$1" dst_dir="$2"
  [[ -d "$src_dir" ]] || return 0
  mkdir -p "$dst_dir"
  for entry in "$src_dir"/*; do
    [[ -e "$entry" ]] || continue
    link "$entry" "$dst_dir/$(basename "$entry")"
  done
}

echo "== skills =="
link_dir_contents "$REPO_DIR/skills" "$CLAUDE_DIR/skills"
echo
echo "== agents =="
link_dir_contents "$REPO_DIR/agents" "$CLAUDE_DIR/agents"
echo
echo "== commands =="
link_dir_contents "$REPO_DIR/commands" "$CLAUDE_DIR/commands"
echo
echo "== scripts =="
link_dir_contents "$REPO_DIR/scripts" "$CLAUDE_DIR/scripts"
echo
echo "== root files =="
link "$REPO_DIR/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"
link "$REPO_DIR/settings.json" "$CLAUDE_DIR/settings.json"

echo
echo "Done."
echo
echo "Next steps:"
echo "  1. If you skipped real files above, diff them against the repo versions and merge manually."
echo "  2. Copy your machine-local files (not tracked by this repo):"
echo "       ~/.claude/settings.local.json      # machine-specific permissions"
echo "       ~/.claude/registry.local.md        # Supabase/EAS/bundle IDs, etc."
echo "  3. Restart Claude Code (or open a new session) to pick up changes."
