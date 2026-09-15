# Plannotator

Herdr Annotate Full はターミナルの選択テキスト・文書・回答へのコメントに、
ブラウザー版 Plannotator は計画・コード差分のレビューに使う。
Claude の計画承認は crit から Plannotator に置き換える。

## 使い方

| 場所              | 操作                                                                |
| ----------------- | ------------------------------------------------------------------- |
| Herdr             | `Ctrl+F` → `u` で選択テキストにコメント                             |
| Herdr             | `Ctrl+F` → `i` で文書、`Ctrl+F` → `Shift+I` で回答をレビュー        |
| Claude            | `/plannotator-review`、`/plannotator-annotate`、`/plannotator-last` |
| Claude 計画モード | 計画承認時にブラウザーが開く                                        |
| Codex             | `$plannotator-review`、`$plannotator-annotate`、`$plannotator-last` |
| シェル            | `plannotator review`、`plannotator annotate README.md`              |

Claude と Codex は設定・skills の追加後に新しいセッションで使う。
Codex の自動 Stop hook は追加していない。
Herdr の全キーは [チートシート](herdr.md#annotate) を参照。

## 管理と更新

[plannotator.yaml](../.chezmoidata/plannotator.yaml) の version でブラウザー版 binary、
core skills、Claude marketplace のタグを揃える。
[after-script](../.chezmoiscripts/run_onchange_after_07-plannotator.sh.tmpl) が公式 minimal installer を実行する。
binary は `~/.local/bin/plannotator`、core skills は `~/.agents/skills` に配置する。
Claude の公式 plugin は hooks、共有 core skills は手動レビューの指示を提供する。
標準 installer による skills の二重配置は行わない。

更新時は version を変更し、chezmoi の差分を確認して適用する。
Claude marketplace の自動更新は無効。個人用と `.work` 環境の仕事用 home をそれぞれ処理する。
settings の symlink は維持する。認証とプラグインの cache は各 home に置く。

Herdr Annotate は既存の `mise run update-herdr-plugins` で更新する。
プラグイン ID は `annotate`。同梱の TUI とその checkout の skill を使うため、
単独の `plannotator-tui` はインストールしない。
`~/.local/bin/plannotator-tui` はインストール済みプラグインの場所を調べ、同梱 binary を起動する。

crit の Homebrew 定義、Claude の enabledPlugins / marketplace 定義を削除した。
after-script は各 Claude home の crit 登録と Homebrew 本体も削除する。
crit のプラグイン保存データは `--keep-data` で残す。

## 保存先

既定ではレビュー履歴を `~/.plannotator` に保存する。
Claude / Codex の認証 home を分けても、Plannotator の履歴は自動では分離されない。
ローカルファイルのレビューから始め、URL annotation、Ask AI、共有を使う場合は
その操作に伴う外部通信を考慮する。

公式仕様と導入時の判断は [調査メモ](plannotator-research.md) を参照。

## 導入時の検証

2026-09-15、macOS / Herdr 0.9.0 で確認。

- `plannotator 0.27.14`、Claude plugin 0.27.14、Herdr Annotate 0.4.0、同梱 TUI 0.8.0。
- 個人用・仕事用 Claude の Plannotator が有効で、crit の登録と Homebrew 本体がない。
- Herdr config check とリロードは成功。公式 TUI のテスト文書を Herdr ペインで開閉できる。
- ブラウザーでテスト文書にコメントし、CLI に `decision: annotated` とコメントが戻る。
- 模擬 ExitPlanMode 入力をブラウザーで承認すると `PermissionRequest` の `allow` が戻る。
- 一時 Git repo の差分をブラウザーで表示・承認し、CLI に `decision: approved` が戻る。
- ShellCheck、Prettier、既存の関連テスト 70 件が成功。総合テストは一時ディレクトリの古い hk.json の影響を避けるため `HK=0 mise run check-worktrunk` で実行した。
- 導入 script の再実行は成功し、確認対象の chezmoi 差分は空。

新しい Claude / Codex セッションでの自然言語からの skill 起動、計画 hook の自動発火、
Herdr の回答選択から実エージェントへの返送は未検証。導入済み plugin / skill と
模擬入力の検証を、実エージェントとの往復確認とは区別している。
