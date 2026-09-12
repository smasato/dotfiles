# Claude のアカウント切り替え

Codex と同じく、通常のコマンドを個人用、`w` 付きのコマンドを仕事用にする。

| コマンド  | アカウント | 設定ディレクトリ |
| --------- | ---------- | ---------------- |
| `claude`  | 個人用     | `~/.claude`      |
| `wclaude` | 仕事用     | `~/.claude_work` |

`wclaude` と仕事用 Raycast ウィジェットは `.work = true` の環境にだけ配置する。
仕事用 home は設定・ルール・hooks・agents・skills を共有し、認証とセッションは分離する。
プラグインの登録・キャッシュは個別に管理する。Worktrunk の更新は [wt.md](wt.md#claude-code-連携) を参照。

## 以前の pclaude 構成からの切り替え

以前は `claude` が標準 home、`pclaude` が `~/.claude_personal_home` を使用していた。
今回の変更は alias と管理対象の配置を変える。既存のログイン・履歴・Keychain は移動しない。
適用後も標準 home の既存アカウントはそのままなので、個人用への切り替えが必要になる。

Claude を終了し、`~/.claude`・`~/.claude.json`・`~/.claude_personal_home` をバックアップしてから、
`claude` で個人用、仕事環境では `wclaude` で仕事用アカウントにログインする。
認証は設定ディレクトリに対応する Keychain エントリも使うため、ディレクトリ名の変更だけでは移行できない。
旧 home の履歴を参照する場合は `CLAUDE_CONFIG_DIR="$HOME/.claude_personal_home" claude` で起動できる。
旧 home は削除しない。旧 Raycast の `pclaude-usage.sh` が残っていれば Script Commands から無効化する。

変更を取り消す場合は以前の dotfiles 設定を適用し直す。ログインを切り替えた場合は、
元のアカウントでログインし直す。履歴のバックアップは切り替えを確認するまで保管する。
