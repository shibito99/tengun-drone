# Claude Code 許可リスト 移植キット

別のPCに移して実行すれば、このPCと同じ「許可リスト改造」（`settings.json` の
permissions 設定）を適用します。**「実行してもいいですか?」の確認を9割削減。**

## 中身

| ファイル | 役割 |
|---|---|
| `install.sh` | 実行の入口（これを叩くだけ） |
| `apply_permissions.py` | 本体。`~/.claude/settings.json` に permissions を注入 |
| `permissions.json` | 適用する内容の正本（allow 59 / deny 10 / defaultMode）。編集可 |
| `仕様_許可リスト設計.md` | 設計の考え方・根拠（読み物） |

## 使い方（移植先PCで）

1. このフォルダ（ZIPなら展開）を移植先PCの任意の場所に置く
2. ターミナルでフォルダに入り、次を実行：

```bash
bash install.sh
```

3. Claude Code を**再起動**（次回セッションから有効）
4. 新セッションで `/permissions` を開き、allow/deny/mode が入っていれば成功

> 対象OS: macOS / Linux（`bash` と `python3` が必要。Macは標準で両方あり）

## 何をするか（安全設計）

- **`settings.json` は上書きしません**。`permissions` キーだけを注入し、
  既存の `model` / `hooks` / `mcpServers` / APIトークン等はそのまま保持。
- 実行前に **自動バックアップ**（`settings.json.bak.<日時>`）。
- **冪等**：何度実行しても同じ結果。
- `settings.local.json` は**触りません**（既定）。移植先の既存ルールを勝手に消さない。

## オプション

```bash
bash install.sh --dry-run      # 変更せず、何が起きるか表示だけ
bash install.sh --slim-local   # settings.local.json の肥大化したallowも減量
                               #   （WebFetchドメイン＋Skillのみ残す。バックアップは取る）
```

> 補足：`settings.local.json` が肥大していても改造は効きます（deny は全スコープで最優先、
> allow はマージされるため）。`--slim-local` は掃除したい場合の任意オプションです。

## ロールバック

```bash
# 直前のバックアップに戻す（日時は生成されたファイル名に合わせる）
cp ~/.claude/settings.json.bak.<日時> ~/.claude/settings.json
```

## 中身のカスタマイズ

`permissions.json` の `allow` にコマンドのプレフィックスを追記すれば、
そのコマンドは確認なしで実行されます（構文はスペース+`*`：例 `Bash(npm run *)`）。
秘密ファイルは `deny` に `Read(...)` を追加して守ります（`deny` が最優先）。
編集後に再度 `bash install.sh` を実行すれば反映されます。
