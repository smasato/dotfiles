# Worktrunk (wt) の仕組み

Worktrunk（`wt` CLI）による git worktree 管理の構成メモ。
インストールからライフサイクル hook、Herdr / Claude Code 連携までこのリポジトリで管理している。

## 構成要素

| ファイル                                                   | 役割                                                                 |
| ---------------------------------------------------------- | -------------------------------------------------------------------- |
| `dot_config/mise/config.toml`                              | mise で `worktrunk = "latest"` をインストール                        |
| `dot_zshrc.tmpl`                                           | シェル統合（`wt config shell init zsh` を eval）                     |
| `dot_config/worktrunk/config.toml`                         | ユーザー設定。ライフサイクル hook を定義                             |
| `dot_config/herdr/scripts/executable_worktree-open.sh`     | post-switch hook から呼ばれ、worktree を Herdr で開く                |
| `dot_config/herdr/scripts/executable_worktree-close.sh`    | pre/post-remove hook から呼ばれ、削除前の ID を保存して close を予約 |
| `dot_config/herdr/scripts/worktree.py`                     | レイアウトの再開・排他制御と削除前後の ID 照合を共通実装             |
| `.chezmoiscripts/run_onchange_after_herdr-plugins.sh.tmpl` | Herdr の `herdr-worktrunk` プラグインをインストール                  |
| `.chezmoiscripts/run_after_04-claude-worktrunk.sh.tmpl`    | 毎回の apply 後に Claude の Worktrunk プラグインを更新               |
| `dot_claude/settings.json.tmpl`                            | Claude Code の worktrunk プラグイン有効化と worktree 権限            |

## インストールとシェル統合

- 本体は mise 管理（`dot_config/mise/config.toml` の `worktrunk = "latest"`）。
- `.zshrc` で `wt` が存在すれば `eval "$(command wt config shell init zsh)"` を実行。
  これで `wt switch` 後にシェルの cwd が worktree へ移動する（シェル統合なしでは cd できない）。

## ライフサイクル hook（`~/.config/worktrunk/config.toml`）

worktree の作成〜削除に合わせて 5 つの hook を定義している。

| Hook          | 名前    | やること                                                                                                                                                                       |
| ------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `pre-switch`  | `fetch` | ローカルに存在しないブランチへ切り替えるとき先に `git fetch origin --prune`。remote-tracking ref からトラッキングブランチを作れるようにする                                    |
| `pre-start`   | `sync`  | `origin/<branch>` があれば upstream 設定 + `git merge --ff-only` で fast-forward。`wt switch --create` はベースから分岐するため、origin に同名ブランチがある場合に内容を揃える |
| `post-switch` | `herdr` | `worktree-open.sh` で switch 先 worktree を Herdr に開き、ワークスペースを自動レイアウト（primary worktree はスキップ）                                                        |
| `pre-remove`  | `herdr` | 削除前のワークスペース ID・端末 ID・ソケット情報を保存する                                                                                                                     |
| `post-remove` | `herdr` | 保存した対象の close を pueue に予約する                                                                                                                                       |

### pre-switch: `fetch`

detached HEAD とローカルに既にあるブランチはスキップ。
未解決のショートカットもスキップするが、v0.76 以降の PR/MR 経由の switch は
実ブランチ名が渡るため、ローカルブランチがなければ fetch が動く。
オフライン等で fetch が失敗しても `|| true` で switch 自体は止めない。

### pre-start: `sync`

既存のリモートブランチを開くときは `wt switch origin/foo` を使う。
Herdr ピッカーでも一覧の `origin/foo` を選べば同じコマンドに渡される。
remote-tracking ref がまだなければ先に `git fetch origin --prune` する。

| 意図                                   | コマンド                                   | upstream            |
| -------------------------------------- | ------------------------------------------ | ------------------- |
| 既存リモートを開く                     | `wt switch origin/foo`                     | `origin/foo`        |
| 同名ブランチをリモートから明示的に作る | `wt switch --create foo --base origin/foo` | `origin/foo`        |
| 別名の新規ブランチをリモートから作る   | `wt switch --create bar --base origin/foo` | wt 本体は設定しない |

この追跡ルールは v0.76 以降、`branch.autoSetupMerge` の値によらない。
`--create foo` だけでは同名リモートが存在してもデフォルトブランチから分岐する。
Claude Code の WorktreeCreate hook と、Herdr でローカルにない短い名前 `foo` を
入力した場合にはこの経路が残るため、補助同期 hook は維持する。

hook は upstream があれば fast-forward し、なければ同名の `origin/<branch>` を
upstream に設定して fast-forward を試みる。diverge 時は内容を変更せず、設定した
upstream は残る。同名リモートがない場合と detached HEAD は同期しない。

この補助同期は明示的な `--base` にも適用される。指定した起点をそのまま保ちたいときは
当該呼び出しだけ同期 hook を空にする。Herdr など他の hook は引き続き動く。

```sh
wt --config-set 'pre-start.sync=""' switch --create bar --base origin/foo
```

### post-switch / pre-remove / post-remove: Herdr 連携

いずれも Herdr サーバーが動いていないときは失敗を無視する（`|| true`）。
detached HEAD では `branch` が未定義になるため、Herdr のラベルには短縮 SHA を使う。
`pre-switch` と `pre-start` はテンプレートの `{% if branch %}` で処理全体を囲み、
未定義変数の展開を防ぐ。シェル側の `|| true` ではテンプレート展開エラーは防げない。

Worktrunk はテンプレート変数をシェル用に自動エスケープするので、`{{ worktree_path }}` などを
さらに引用符で囲まない。ブランチから ref を組み立てる部分は、一度シェル変数に代入してから
`"refs/heads/$branch"` として扱う。pueue への登録は `--escape` を付け、再実行時も引数境界を保つ。

## Herdr 連携の詳細

### worktree-open.sh（post-switch）

`worktree-open.sh` は共通実装の `worktree.py` を呼ぶ。
ソケットと worktree パスごとにロックし、`herdr worktree open --no-focus` で開く。
初回はペイン１つのワークスペースだけを対象に、次のレイアウトを作る。
ピッカーが先に登録したワークスペースでも、素の状態なら対象になる。

1. タブ 1: シェル（左）+ ファイルビューア（右）の split
2. タブ 2: lazygit（タブラベル `lazygit`）
3. タブ 3: シェル（左）+ yazi（右）の split（タブラベル `yazi`）

hunk diff タブは自動では作らず、必要なときに `scripts/hunk-diff.sh` のキーバインドで開く。

進捗は `${XDG_STATE_HOME:-~/.local/state}/herdr/worktrunk/` に保存する。
作成結果は API が返すペイン ID・端末 ID で記録する。タブ名変更などの途中失敗は次の switch で再開する。
作成応答を失った場合は `creation-unconfirmed` に保留し、後から増えたペインを自動採用しない。
復旧時には保存済みの各ペインが同じ端末・タブに属することも再確認する。
完了後の再実行ではペインを増やさず、ユーザーが閉じたタブも再作成しない。
既に独自レイアウトがある場合や、最初のシェルが置き換えられた場合も変更しない。
yazi 起動の応答を失った場合も `yazi-unconfirmed` に保留し、端末入力を自動再送しない。
接続先の識別と API 呼び出しは `herdr_common.py` を共用し、lazygit の戻り先も同じソケット識別で分離する。

### worktree-close.sh（pre-remove / post-remove）

pre-remove の `capture` でワークスペース ID、端末 ID、worktree 情報、ソケットの識別情報を保存する。
post-remove の `queue-close` は保存した対象を pueue に渡し、5 秒後に共通実装の `close` を実行する。
実行時に同じソケット・ワークスペース・端末が残り、元の checkout パスが存在しないことを再確認する。
同じパスの再作成、サーバー再起動、端末の追加・置換があれば閉じない。
プラグイン側で既に閉じたワークスペースはスキップする。親グループを閉じる `--group` は使わない。

pueue に分離する理由: ワークスペースを閉じるとペインの
プロセスグループが kill されるため、`wt remove` を実行したペインで直接閉じると
wt 自身の trash 掃除（`.git/wt/trash` の rm）まで巻き添えになる。

### 状態確認と復旧

`herdr-worktrees` は `~/.local/bin` に配置する。`status` は保存した記録だけを読み、Herdr 停止中でも使える。
表示は最後の記録であり、稼働中のペインや pueue の現在状態を自動取得するものではない。
`--json` ではペイン ID・端末 ID・接続先・pueue タスク ID・最後のエラーも確認できる。

```sh
herdr-worktrees status
herdr-worktrees status /path/to/worktree --json
```

復旧コマンドは対象の Herdr セッション内で実行する。対象パス、ソケット、ワークスペース、
保存済み端末を照合し、別セッションや再作成された端末には適用しない。

| 状態                                | 確認後の操作                                                                                   |
| ----------------------------------- | ---------------------------------------------------------------------------------------------- |
| 通常の途中失敗                      | `herdr-worktrees resume /path/to/worktree`                                                     |
| 作成されたペインが分かる            | `herdr-worktrees resume /path/to/worktree --adopt-pane w1:p3`                                  |
| 作成されなかったことを確認した      | `herdr-worktrees resume /path/to/worktree --retry-pending`。ペイン集合が変わっていれば拒否する |
| yazi が既に動いている               | `herdr-worktrees resume /path/to/worktree --yazi-running`。入力を送らず完了として記録する      |
| yazi が起動せず、対象がシェルのまま | `herdr-worktrees resume /path/to/worktree --retry-yazi`                                        |
| close の予約・実行失敗              | `herdr-worktrees retry-close /path/to/removed-worktree`。pueue 経由で再試行する                |

`--adopt-pane` は確認済みの作成結果を明示的に採用する操作。失敗後に手動で追加した別のペインを指定しない。
予約済み・予約結果不明の close は重複投入を拒否する。`pueue status` / `pueue log <task-id>` で
旧タスクが停止済みか存在しないことを確認した場合だけ、`retry-close` に `--confirm-task-stopped` を付ける。
close の記録は `captured` → `queued` → `closed` または `skipped` に進み、失敗は `queue-failed` / `close-failed`、
予約応答が不明なら `queue-unconfirmed` として残る。後から始まった削除の記録を古いタスクで上書きしない。

### herdr-worktrunk プラグイン

`.chezmoiscripts/run_onchange_after_herdr-plugins.sh.tmpl` で
`devashish2203/herdr-worktrunk` をインストール。実処理は `scripts/update-plugins.sh` と
`herdr_plugins.py` に集約し、file viewer・lazygit の更新と対応するエージェントスキルの同期も行う。
本体バージョンやインストーラーの変更がない場合でも、dotfiles リポジトリで次を実行すれば更新できる。

```sh
mise run update-herdr-plugins
```

手動タスクは `check-worktrunk` を更新前後に実行する。事前検証が失敗すれば更新を始めない。
更新後は必要なプラグインの登録・有効状態・警告を確認し、スキルを同期する。
更新前後のバージョンとコミット、途中失敗、検証結果は
`${XDG_STATE_HOME:-~/.local/state}/herdr/plugin-updates/` の JSON に保存する。
chezmoi apply からの実行でも同じ更新記録を残す。前後のテスト実行は手動タスク側で行う。
更新が途中で失敗した場合は部分更新を記録して終了する。自動ロールバックは行わない。
テストにはスタブを使い、実際のタブ切り替えやペイン起動までは自動確認しない。

キーバインドは `docs/herdr.md` 参照:

- `prefix+shift+g` — worktree ピッカー（`worktrunk.open`）
- `prefix+shift+c` — カレントリポジトリを開く（`worktrunk.open-current`）

Herdr 組み込みの worktree 作成（`new_worktree`）は無効化し、このピッカーに置き換えている。
ピッカーは `show_remote_branches = true` で remote-tracking ブランチ（`origin/foo`）も出す。

## Claude Code 連携

`dot_claude/settings.json.tmpl` で設定:

- `worktrunk@worktrunk` プラグインを有効化（marketplace: `max-sixty/worktrunk`）。
  worktrunk スキル（設定・hook のリファレンス）と `wt-switch-create` スキルが使える
- `permissions.allow` に `EnterWorktree` / `ExitWorktree` を追加。
  Claude Code の worktree 分離（`isolation: "worktree"`）が確認なしで動く

`chezmoi apply` は `run_after_04-claude-worktrunk.sh.tmpl` を毎回実行し、
標準の `~/.claude` にある Worktrunk marketplace とプラグインを更新する。
未導入なら登録・インストールする。mise の本体インストール後に実行し、
`CLAUDE_CONFIG_DIR` が継承されても更新先は標準 home に固定する。
ネットワークや CLI のエラーは apply の失敗として通知され、次回の apply で再試行する。
このスクリプトは毎回実行されるが、通常の `chezmoi diff` では非表示になる。
表示の切り替えと既存環境への設定反映は [chezmoi diff の運用](../README.md#chezmoi-diff) を参照。

手動で更新する場合:

```sh
claude plugin marketplace update worktrunk
claude plugin update worktrunk@worktrunk --scope user
```

更新後は Claude Code を再起動する。v0.76 以降の activity marker hook は
`-C "$CLAUDE_PROJECT_DIR"` を指定し、セッション中に `cd` しても起動元の worktree を示す。
`pclaude` は設定ファイルを共有するが、別の `CLAUDE_CONFIG_DIR` を使うため、プラグインの
登録とキャッシュも確認する。独立して導入している場合は、その環境変数を指定して更新する。
今回の自動更新スクリプトは、この別 home や他の Claude プラグインを更新しない。

## 状態確認と片付け候補

```sh
wt step for-each -- git status --short
wt step eval '{{ primary_worktree_path }}'
wt step prune --dry-run --min-age=2d --format=json
```

`for-each` は各 worktree で逐次実行し、`eval` は Worktrunk のテンプレート変数を返す。
prune のプレビューは候補オブジェクトの JSON 配列で、`wt list` の `.items` 形式とは異なる。

`~/.agents/skills/poteto-mode/scripts/worktree-audit.sh` は、このプレビューを一度取得し、
監査表の `PRUNE` 列に `candidate`、`-`、`unknown` を表示する。
`candidate` は作成から２日以上の削除候補、`-` は今回の候補外、`unknown` は取得失敗を示す。
対応はパスで判定し、worktree を持たない branch-only 候補は表に含めない。

HEAD・コミット日時・ブランチ・upstream は、一度取得した schema 2 の `wt list` を使う。
`REMOTE` は実際の upstream と差分数を表示する（例: `mirror/topic:+2/-3`）。
追跡先なしは `no-upstream`、detached HEAD は `detached`。`MERGED` は祖先関係の判定であり、
prune の内容統合判定とは区別する。Git や PR 取得の失敗は `unknown` とし、`hold-unknown` に保留する。
PR は著者を限定せず取得する。取得上限 1,000 件に達して該当 PR が見つからない場合も `unknown`。

Herdr 内から実行した場合は `herdr api snapshot` を一度取得し、正規化したパスで照合する。
`HERDR` 列にはワークスペース ID、現在のセッションに未登録なら `-`、取得できない場合や
Herdr 外からの実行なら `unknown` を表示する。他の Herdr セッションまでは調べない。
この列と `PRUNE` は使用状況の補足で、削除の許可には使わない。

会話履歴、作業中の変更、ignored ファイル、PR の状態を確認したうえで、
確認済みの対象だけを `wt remove <path>` で削除する。監査スクリプト自体は削除しない。
会話の日付取得には macOS 標準の `date` / `stat` を使い、GNU coreutils の PATH に影響されない。

共通の検証入口は `mise run check-worktrunk`。関連ファイルの変更時は `hk check` からも実行する。
実際の wt による hook 展開、Claude プラグインの導入・更新・失敗、Herdr の並行実行・再開・遅延 close、
監査の取得失敗・upstream・Herdr パス照合を検証する。外部操作はスタブに置き換え、
稼働中のワークスペースや実際の worktree は作成・削除しない。シェルスクリプトは ShellCheck も通す。

## 設定変更時の確認

`wt config show` で管理元を検証し、通常ブランチと detached HEAD で変更した hook の
`wt hook <hook名> --dry-run` を確認する。展開結果だけを検証し、fetch や Herdr 操作は実行しない。

```sh
wt --config "$PWD/dot_config/worktrunk/config.toml" config show
```

## 注意点

- hook は `~/.config/worktrunk/config.toml`（ユーザー設定）のみ。
  プロジェクト設定 `.config/wt.toml` はこのリポジトリでは使っていない
- プロジェクト設定の hook は初回実行時に承認が必要（`wt config approvals add`）。
  ユーザー設定の hook に承認は不要
