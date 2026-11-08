#!/usr/bin/env bash
# Claude Code 許可リスト移植キット — ワンショット・インストーラ
# 使い方: このフォルダで  bash install.sh   （減量も行うなら  bash install.sh --slim-local）
set -euo pipefail
cd "$(dirname "$0")"

echo "=============================================="
echo " Claude Code 許可リスト 改造インストーラ"
echo "=============================================="

# python3 の存在確認
if ! command -v python3 >/dev/null 2>&1; then
  echo "✗ python3 が見つかりません。python3 を入れてから再実行してください。" >&2
  exit 1
fi

# 本体を実行（引数はそのまま渡す: --slim-local / --dry-run など）
python3 apply_permissions.py "$@"

echo
echo "→ 済んだら Claude Code を再起動して /permissions で確認してください。"
