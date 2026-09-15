# Herdr Annotate / Plannotator 導入調査

調査日: 2026-09-15。公式ドキュメント、GitHub のソースと release API を確認した。以下は調査時の導入案。続けて実施した導入と検証は [運用メモ](plannotator.md) を参照。

## 役割と推奨構成

Herdr Annotate Full とブラウザ版 Plannotator を併用するのがよい。前者をターミナルの選択テキスト・Markdown・エージェント回答へのコメントに、後者をコード差分や計画のレビューに使う。Herdr Annotate は内部に `plannotator-tui` を同梱するため、ブラウザ版の `plannotator` とは別の実行ファイルになる。[Herdr Annotate](https://github.com/plannotator/herdr-annotate)、[Plannotator](https://github.com/backnotprop/plannotator)

ユーザーの方針に合わせ、`crit` は外して Claude Code の計画レビューを Plannotator に置き換える。Herdr の手動レビューとブラウザ版の手動レビューを確認してから切り替える。Codex の自動 hook は実験的なため、初期導入は手動レビューにする。

## 確認した版

| 対象                     | 確認値                                             | 出典                                                                                                                                                                                                                                                                       |
| ------------------------ | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plannotator 最新 release | `v0.27.14`、2026-09-11 公開                        | [Release](https://github.com/backnotprop/plannotator/releases/tag/v0.27.14)                                                                                                                                                                                                |
| herdr-annotate main      | `7c8f5a177b8285dc56efc471ef04f7ab44a2b4b6`         | [Commit](https://github.com/plannotator/herdr-annotate/commit/7c8f5a177b8285dc56efc471ef04f7ab44a2b4b6)                                                                                                                                                                    |
| plugin manifest          | ID `annotate`、version `0.4.0`、Herdr 最低 `0.8.0` | [Manifest](https://github.com/plannotator/herdr-annotate/blob/7c8f5a177b8285dc56efc471ef04f7ab44a2b4b6/herdr-plugin.toml)                                                                                                                                                  |
| 同梱 binary の指定       | herdr-annotate `0.1.0`、plannotator-tui `0.8.0`    | [Annotate version](https://github.com/plannotator/herdr-annotate/blob/7c8f5a177b8285dc56efc471ef04f7ab44a2b4b6/herdr-annotate.version)、[TUI version](https://github.com/plannotator/herdr-annotate/blob/7c8f5a177b8285dc56efc471ef04f7ab44a2b4b6/plannotator-tui.version) |

manifest と binary の版番号は別物。導入時にはその時点の release を再確認する。

## Herdr Annotate

### 導入方法

公式 Full install:

```sh
herdr plugin install plannotator/herdr-annotate
herdr config check
herdr server reload-config
```

キーバインドは別途設定が必要。Lite は `plannotator/herdr-annotate/lite` だが、Full と同じ plugin ID なので共存せず置き換えになる。現在の macOS 版はビルド済み binary を取得し SHA-256 を検証する。Bun や Rust toolchain の導入は不要。更新は install コマンドの再実行で行う。[公式 README](https://github.com/plannotator/herdr-annotate#install)

### 登録する action

| action                  | 内容                                     | 公式の推奨キー   |
| ----------------------- | ---------------------------------------- | ---------------- |
| `annotate.capture`      | 選択テキストにコメント                   | `prefix+a`       |
| `annotate.copy-context` | 保存済みコメントをコピー                 | `prefix+shift+a` |
| `annotate.copy-archive` | コピーしてアーカイブ                     | `prefix+ctrl+a`  |
| `annotate.manage`       | コメント一覧                             | `prefix+m`       |
| `annotate.open`         | フォーカス中のフォルダの文書レビュー     | `prefix+o`       |
| `annotate.last`         | フォーカス中のエージェントの回答レビュー | `prefix+shift+o` |

各項目は `[[keys.command]]` の `type = "plugin_action"` として登録する。既存キーとの衝突確認が必要。Full は Markdown の `file://` リンク用 handler も登録する。[Manifest](https://github.com/plannotator/herdr-annotate/blob/7c8f5a177b8285dc56efc471ef04f7ab44a2b4b6/herdr-plugin.toml)

文書レビューは Claude Code と Codex に対応し、Send / `E` でコメントをエージェントの次のメッセージとして送れる。表示先は `~/.config/plannotator-tui/config.toml` の `[herdr] placement` に `overlay`、`split`、`popup` を指定する。Herdr 外でも TUI を起動したい場合だけ、単独版の追加を検討する。[TUI README](https://github.com/plannotator/plannotator-tui#inside-herdr)

### 制限

Neovim 内部の選択はそのまま取得できない。公式の visual mapping は選択内容を一時ファイルに渡して action を起動する方式。まず Herdr 側の選択で試し、必要なら Neovim integration を追加する。[選択の制限と Neovim 設定](https://github.com/plannotator/herdr-annotate#selection-limits)

回答レビューで正確なセッションを選ぶには、Herdr がセッション ID を把握している必要がある。Claude の integration を導入する前から動いていたセッションでは ID がなく、同一フォルダの最新 transcript にフォールバックする場合がある。複数セッションを同じフォルダで動かす場合は、新しいセッションで確認する。[TUI の agent replies](https://github.com/plannotator/plannotator-tui#agent-replies)

## ブラウザ版 Plannotator

### binary と設定を分けて導入する

chezmoi 管理の設定と統合しやすいのは、公式 installer の minimal mode で binary だけを導入し、skills / hooks を別途管理する方法。

```sh
curl -fsSL https://plannotator.ai/install.sh -o /tmp/plannotator-install.sh
# 取得したスクリプトを確認してから実行する
bash /tmp/plannotator-install.sh --minimal --version v0.27.14
~/.local/bin/plannotator --version
~/.local/bin/plannotator --help
```

`--minimal` は skills、hooks、agent 設定、sem sidecar、agent-terminal runtime を追加しない。macOS Arm64/x64 対応で binary の SHA-256 を検証する。追加の attestation 検証は `--verify-attestation`。通常版の install は Git を使い、任意の統合 terminal は Node.js/npm も使う。[Installation](https://docs.plannotator.ai/open-source/start/installation)

保存先は現行 installer で `~/.local/bin/plannotator`。mise の GitHub backend も release asset の直接管理候補にはなるが、この組み合わせの asset 選択・実行名・検証動作は未検証。まず公式 minimal installer を使い、必要になったら mise に集約するのが確実。[Installer source](https://github.com/backnotprop/plannotator/blob/v0.27.14/scripts/install.sh)、[mise GitHub backend](https://mise.jdx.dev/dev-tools/backends/github.html)

### skills と共有ディレクトリ

公式 docs は三つの core skill `plannotator-review`、`plannotator-annotate`、`plannotator-last` を説明している。確認した `v0.27.14` には CLI リファレンス用の `plannotator` skill もある。[Skills docs](https://docs.plannotator.ai/open-source/start/skills)、[v0.27.14 core skills](https://github.com/backnotprop/plannotator/tree/v0.27.14/apps/skills/core)

重要なのは同名 skill に別の実装がある点。Claude 専用版は動的コンテキスト挿入で直接コマンドを実行し、共通 core 版はエージェントに shell 実行を指示する。標準 installer は Claude 版を `~/.claude/skills` に置いた後、core 版を `~/.agents/skills` に置く。二つが symlink で同じ実体を指す環境では、後者が前者を上書きする。共通 core 版のみを共有する方針か、Claude 専用配置を分ける方針かを決める必要がある。[v0.27.14 installer](https://github.com/backnotprop/plannotator/blob/v0.27.14/scripts/install.sh)、[Claude skill](https://github.com/backnotprop/plannotator/blob/v0.27.14/apps/skills/claude/plannotator-review/SKILL.md)、[Core skill](https://github.com/backnotprop/plannotator/blob/v0.27.14/apps/skills/core/plannotator-review/SKILL.md)

### Claude Code

公式 plugin コマンド:

```text
/plugin marketplace add backnotprop/plannotator
/plugin install plannotator@plannotator
```

再起動後、`PermissionRequest` の `ExitPlanMode` を Plannotator でレビューする。手動コマンドは `/plannotator-review`、`/plannotator-annotate`、`/plannotator-last`。plugin と skills / binary は別の更新対象である。[Claude Code guide](https://docs.plannotator.ai/open-source/agents/claude-code)

現行 hook は `EnterPlanMode` の `PreToolUse` でも `plannotator improve-context` を実行する。今回の導入では `crit` の計画レビュー hook を外し、Plannotator に担当させる。[Hook source](https://github.com/backnotprop/plannotator/blob/v0.27.14/apps/hook/hooks/hooks.json)

### Codex

Plannotator の公式 integration は実験的な `Stop` hook を使う。Claude の実装開始前の `ExitPlanMode` と異なり、ターン完了後の計画を読み取り、フィードバックで同じターンの継続を求める。まず `$plannotator-review` / `$plannotator-annotate` / `$plannotator-last`、または CLI の手動利用で試すのがよい。[Codex guide](https://docs.plannotator.ai/open-source/agents/codex)

自動 hook は各 `$CODEX_HOME/config.toml` の `[features] hooks = true` と隣接する `hooks.json` の `Stop` 登録が必要。Desktop は shell の PATH を継承しない場合があるため binary の絶対パスを使う。標準 installer の hook 対象は実行時の `$CODEX_HOME` 一つであり、work seat 全体の設定は別途確認する。[Codex guide](https://docs.plannotator.ai/open-source/agents/codex)

この対応表は Plannotator 側の仕様確認であり、利用中の Codex Desktop / CLI で hook 発火を実証したものではない。

## 保存データとネットワーク

レビュー内容は通常ローカルの `~/.plannotator` に保存される。文書履歴には開いたファイル全文が含まれることがある。通常は loopback の HTTP server を使うが、完全なオフライン動作ではなく GitHub release 確認等がある。URL annotation、Ask AI、共有はそれぞれ外部通信を伴う。仕事での初期導入はローカルファイルから試すのがよい。[Privacy and data flow](https://docs.plannotator.ai/open-source/reference/privacy-and-data-flow)

TUI はブラウザ版と互換の feedback archive を保存する。個人・仕事の履歴を分けたい場合は `PLANNOTATOR_DATA_DIR` の切り替えを検討する。ただし Herdr plugin がどの環境変数を継承するかは導入時の確認事項。[TUI storage](https://github.com/plannotator/plannotator-tui#where-annotations-live)

## この dotfiles での実装案

以下はローカル設定を読んだうえでの提案。設定ファイルの変更や導入コマンドの実行はまだ行っていない。調査時の `herdr --version` は `0.9.0` で最低要件を満たす。`plannotator` と `plannotator-tui` は現在の PATH では見つからなかった。

### 1. Herdr Full を既存の更新フローに追加

[herdr_plugins.py](../dot_config/herdr/scripts/herdr_plugins.py) の `PLUGINS` に `"annotate": "plannotator/herdr-annotate"` を追加する。キーは repo 名ではなく manifest の ID。既存の chezmoi after-script と `mise run update-herdr-plugins` を使えば、他のプラグインと同様に更新前後の commit を記録できる。

`plannotator-tui` skill は同じプラグイン checkout から共有ストアへ更新する案を勧める。既存の `herdr-file-viewer` skill と同じ方式にすると、プラグイン本体と説明の版を揃えられる。既存テスト [test-worktrunk-herdr-plugins.py](../scripts/test-worktrunk-herdr-plugins.py) の固定されたプラグイン一覧と件数も更新対象になる。

[Herdr config](../dot_config/herdr/config.toml.tmpl) の prefix は `Ctrl+F`。`a` と `Shift+A` はエージェント切り替え、`o` はデフォルトの通知先移動に使う。公式例をそのままコピーせず、次の割り当てを候補にする。最終的な衝突は `herdr config check` で確認する。

| キー候補         | action                  |
| ---------------- | ----------------------- |
| `prefix+u`       | `annotate.capture`      |
| `prefix+shift+u` | `annotate.copy-context` |
| `prefix+ctrl+u`  | `annotate.copy-archive` |
| `prefix+m`       | `annotate.manage`       |
| `prefix+i`       | `annotate.open`         |
| `prefix+shift+i` | `annotate.last`         |

キー追加時には repo の `sync-herdr-docs` スキルに従い [docs/herdr.md](herdr.md) も更新する。初期設定は追加の placement 指定をせず、標準の overlay から試せる。

### 2. ブラウザ版と skills を管理

公式 minimal installer を版固定の chezmoi after-script から呼ぶ。自動更新の有無は明示し、少なくとも起動のたびに最新版を取得する処理にはしない。導入先の `~/.local/bin` は [dot_zprofile.tmpl](../dot_zprofile.tmpl) で PATH に追加しているが、GUI 起動と hook の実行環境では別途到達確認が必要。

共通 core skills を `~/.agents/skills` に一度だけ配置する。Claude の hooks は公式 Claude plugin に任せ、手動コマンドは共有 core skills から使う。これで共有 skills のリンクを維持しつつ、標準 installer が異なる内容の同名 skill を重ねて書く処理を避けられる。確認した v0.27.14 の plugin には手動コマンドが含まれず、共有 skills と plugin の同名コマンドは重複しない。

### 3. crit を外し、Claude plugin を切り替える

削除対象は次のとおり。

- [packages.yaml](../.chezmoidata/packages.yaml) の `packages.darwin.brews.base.crit`。
- [Claude settings template](../dot_claude/settings.json.tmpl) の `enabledPlugins` 内 `crit@crit` と `extraKnownMarketplaces` 内 `crit`。
- 個人用・仕事用それぞれの Claude plugin 登録に残る `crit`。
- インストール済みの Homebrew `crit` 本体。

現物の `~/.claude/plugins/cache/crit/crit/1.8.7/hooks/hooks.json` は `PermissionRequest` / `ExitPlanMode` で `crit plan-hook` を呼んでいた。Plannotator と同じ計画承認に入るので、切り替え後の新しい Claude セッションで Plannotator だけが起動することを確認する。

Homebrew 用 [after-script](../.chezmoiscripts/run_onchange_darwin-install-packages.sh.tmpl) はインストール処理のみで、不要パッケージの削除は行っていない。YAML から消すだけで完了とせず、導入時に `crit` のみを明示的にアンインストールする。

Plannotator の marketplace / enabledPlugins をテンプレートに追加し、公式 plugin を各 Claude home に登録する。[claude-accounts.md](claude-accounts.md) のとおり `wclaude` は settings を共有しても plugin 登録・cache は個別。標準 home だけを処理する既存 Worktrunk script の対象範囲をそのまま流用しない。

### 4. Codex は手動で開始

共有 core skills と Herdr の `annotate.last` を使う。自動 Stop hook は導入後の追加候補とする。後で追加する場合、[modify_hooks.json](../dot_codex/modify_hooks.json) の既存 hook を維持し、work1〜3 が hooks を共有して config を個別管理している構成に合わせる。

### 導入完了の確認

- 変更した shell script は ShellCheck、テンプレートはレンダリング確認、Herdr plugin 更新処理は既存テストを実行する。
- Herdr の選択テキスト・文書・回答をそれぞれ開き、コメントが意図したエージェントに戻ることを確認する。
- 個人用 Claude と存在する仕事用 Claude で、計画承認時に Plannotator が一度だけ開くことを確認する。
- Codex は手動レビューでフィードバックが戻ることを確認する。初回確認には機密を含まない小さな文書と差分を使う。
- 2 回目の適用で登録が重複せず、chezmoi 管理ファイルに意図しない差分が残らないことを確認する。
