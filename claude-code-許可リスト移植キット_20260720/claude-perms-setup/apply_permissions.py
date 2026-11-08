#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code 許可リスト移植インストーラ
  同フォルダの permissions.json を、このPCの ~/.claude/settings.json の
  "permissions" キーに注入（マージ）する。既存の model/hooks/mcpServers/token 等は保持。

使い方:
  python3 apply_permissions.py            # permissions を注入（安全・推奨）
  python3 apply_permissions.py --slim-local
        # 上記に加え settings.local.json を減量（WebFetchドメイン＋Skillのみ残し
        #  肥大化した allow を削除）。実行前に必ずバックアップを取る。
  python3 apply_permissions.py --dry-run  # 変更せず、何が起きるかだけ表示

特徴: 実行前に自動バックアップ / JSON検証 / 何度実行しても同じ結果（冪等）
"""
import json, sys, shutil, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLAUDE_DIR = Path.home() / ".claude"
SETTINGS = CLAUDE_DIR / "settings.json"
LOCAL = CLAUDE_DIR / "settings.local.json"
STAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

DRY = "--dry-run" in sys.argv
SLIM = "--slim-local" in sys.argv


def load(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.exit(f"✗ {path} が壊れたJSONです: {e}")


def backup(path):
    if path.exists():
        bak = path.with_name(path.name + f".bak.{STAMP}")
        if not DRY:
            shutil.copy2(path, bak)
        print(f"  backup: {bak}")


def write(path, obj):
    if DRY:
        return
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    if not (HERE / "permissions.json").exists():
        sys.exit("✗ permissions.json が同フォルダに見つかりません")
    perm = json.loads((HERE / "permissions.json").read_text(encoding="utf-8"))
    print(f"■ 適用する権限: allow={len(perm['allow'])} deny={len(perm['deny'])} "
          f"defaultMode={perm['defaultMode']}")
    if DRY:
        print("  (--dry-run: 実際の書き込みは行いません)")

    CLAUDE_DIR.mkdir(exist_ok=True)

    # 1) settings.json に permissions を注入（他キーは保持）
    s = load(SETTINGS)
    before = s.get("permissions")
    backup(SETTINGS)
    s["permissions"] = perm
    write(SETTINGS, s)
    kept = [k for k in s if k != "permissions"]
    print(f"✓ settings.json: permissions を{'更新' if before else '新規追加'}"
          f"（保持した既存キー: {', '.join(kept) or 'なし'}）")

    # 2) settings.local.json の減量（任意）
    if SLIM:
        l = load(LOCAL)
        old = l.get("permissions", {}).get("allow", [])
        keep = sorted({a for a in old
                       if a.startswith("WebFetch(") or a.startswith("Skill(")})
        if old:
            backup(LOCAL)
            l["permissions"] = {"allow": keep}
            write(LOCAL, l)
            print(f"✓ settings.local.json: allow {len(old)}件 → {len(keep)}件"
                  f"（WebFetchドメイン＋Skillのみ保持）")
        else:
            print("  settings.local.json: 減量対象なし（スキップ）")
    else:
        print("  settings.local.json: 変更せず（減量するには --slim-local）")

    # 3) 検証
    if not DRY:
        json.loads(SETTINGS.read_text(encoding="utf-8"))
        if LOCAL.exists():
            json.loads(LOCAL.read_text(encoding="utf-8"))
        print("✓ JSON妥当性チェック 合格")

    print("\n完了。次回 Claude Code 起動時から有効です。")
    print("確認: 新セッションで /permissions（allow/deny/mode）／ロールバックは .bak を戻す")


if __name__ == "__main__":
    main()
