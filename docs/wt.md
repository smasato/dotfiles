# Worktrunk (wt) の仕組み

Worktrunk（`wt` CLI）による git worktree 管理の構成メモ。
インストールからライフサイクル hook、Herdr / Claude Code 連携までこのリポジトリで管理している。

## 構成要素

| ファイル                                                        | 役割                                                                 |
| --------------------------------------------------------------- | -------------------------------------------------------------------- |
| `dot_config/mise/config.toml`                                   | mise で `worktrunk = "latest"` をインストール                        |
| `dot_zshrc.tmpl`                                                | シェル統合（`wt config shell init zsh` を eval）                     |
| `dot_config/worktrunk/config.toml`                              | ユーザー設定。ライフサイクル hook を定義                             |
| `dot_config/herdr/scripts/executable_worktree-open.sh`          | post-switch hook から呼ばれ、worktree を Herdr で開く                |
| `dot_config/herdr/scripts/executable_worktree-close.sh`         | pre/post-remove hook から呼ばれ、削除前の ID を保存して close を予約 |
| `dot_config/herdr/scripts/worktree.py`                          | レイアウトの再開・排他制御と削除前後の ID 照合を共通実装             |
| `.chezmoiscripts/run_onchange_after_herdr-plugins.sh.tmpl`      | Herdr の `herdr-worktrunk` プラグインをインストール                  |
| `.chezmoiscripts/run_after_04-claude-worktrunk.sh.tmpl`         | 毎回の apply 後に Claude の Worktrunk プラグインを更新               |
| `.chezmoiscripts/run_onchange_after_05-codex-worktrunk.sh.tmpl` | Codex の各 home に Worktrunk plugin を導入し、CLI で有効化を確認     |
| `dot_claude/settings.json.tmpl`                                 | Claude Code の worktrunk プラグイン有効化と worktree 権限            |

## インストールとシェル統合

- 本体は mise 管理（`dot_config/mise/config.toml` の `worktrunk = "latest"`）。
- `.zshrc` で `wt` が存在すれば `eval "$(command wt config shell init zsh)"` を実行。
  これで `wt switch` 後にシェルの cwd が worktree へ移動する（シェル統合なしでは cd できない）。

## ライフサイクル hook（`~/.config/worktrunk/config.toml`）

worktree の作成〜削除に合わせて 5 つの hook を定義している。

| Hook          | 名前    | やること                                                                                                                                    |
| ------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `pre-switch`  | `fetch` | ローカルに存在しないブランチへ切り替えるとき先に `git fetch origin --prune`。remote-tracking ref からトラッキングブランチを作れるようにする |
| `pre-start`   | `copy`  | primary worktree の `.worktreeinclude` に一致する ignored ファイルを、新規 worktree へコピーする                                            |
| `post-switch` | `herdr` | `worktree-open.sh` で switch 先 worktree を Herdr に開き、ワークスペースを自動レイアウト（primary worktree はスキップ）                     |
| `pre-remove`  | `herdr` | 削除前のワークスペース ID・端末 ID・ソケット情報を保存する                                                                                  |
| `post-remove` | `herdr` | 保存した対象の close を pueue に予約する                                                                                                    |

### pre-switch: `fetch`

detached HEAD とローカルに既にあるブランチはスキップ。
未解決のショートカットもスキップするが、v0.76 以降の PR/MR 経由の switch は
実ブランチ名が渡るため、ローカルブランチがなければ fetch が動く。
オフライン等で fetch が失敗しても `|| true` で switch 自体は止めない。

### ブランチの起点とリモートの選択

既存のリモートブランチを開くときは `wt switch origin/foo` を使う。
Herdr ピッカーでも一覧の `origin/foo` を選べば同じコマンドに渡される。
remote-tracking ref がまだなければ先に `git fetch origin --prune` する。

| 意図                                   | コマンド                                   | upstream     |
| -------------------------------------- | ------------------------------------------ | ------------ |
| 既存リモートを開く                     | `wt switch origin/foo`                     | `origin/foo` |
| 同名ブランチをリモートから明示的に作る | `wt switch --create foo --base origin/foo` | `origin/foo` |
| 別名の新規ブランチをリモートから作る   | `wt switch --create bar --base origin/foo` | 設定しない   |

この追跡ルールは v0.76 以降、`branch.autoSetupMerge` の値によらない。
`--create foo` だけでは同名リモートが存在してもデフォルトブランチから分岐する。
同名リモートへ自動で追従する `pre-start.sync` は削除したため、明示した `--base` を保つ。
Claude Code の WorktreeCreate hook と、Herdr で新しい短い名前を入力する場合も同じ。

### pre-start: `copy`

`wt step copy-ignored --require-include` を新規 worktree の作成時に同期実行する。
コピー元は常に primary worktree、コピー先は新規 worktree。
コピー元の `.worktreeinclude` が存在するリポジトリだけが対象になり、ファイルは
Git の ignore と include の両方に一致する必要がある。たとえば primary に次の内容の
`.worktreeinclude` を置けば、Git で ignore されている `.env.local` を引き継げる。

```gitignore
.env.local
```

今回は共通 hook と記述例だけを用意した。個別リポジトリの `.worktreeinclude` は追加していない。
include がない場合と対象がない場合は何もせず成功する。tracked ファイルと
コピー先の既存ファイルは上書きしない。既存 worktree への switch ではコピーせず、
作成後の設定変更も同期しない。別の worktree から作成してもコピー元は primary になる。

コピーが I/O エラーで失敗すると、後続の起動 hook を中止する。
作成済み worktree と途中までコピーしたファイルは残る。
原因を修正してから新規 worktree 内で次を実行する。既存ファイルは保持し、不足分をコピーする。

```sh
wt step copy-ignored --require-include --dry-run
wt step copy-ignored --require-include
```

コピー完了後は必要な起動 hook を明示的に再実行する。既存 worktree への
`wt switch <branch>` は `post-switch` を再実行するが、`pre-start` / `post-start` は再実行しない。

### post-switch / pre-remove / post-remove: Herdr 連携

いずれも Herdr サーバーが動いていないときは失敗を無視する（`|| true`）。
detached HEAD では `branch` が未定義になるため、Herdr のラベルには短縮 SHA を使う。
`pre-switch` はテンプレートの `{% if branch %}` で処理全体を囲み、
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

Worktrunk が起動した hook の出力は、対象リポジトリで次を実行して探す。
Python が状態を保存する前の起動エラーは、こちらのログに残ることがある。

```sh
wt config state logs
wt config state logs --format=json |
  jq '.hook_output[] | select(.source == "user" and (.hook_type == "post-switch" or .hook_type == "post-remove") and .name == "herdr") | {branch, hook_type, path}'
```

表示された `path` を `tail` などで読む。close の予約後は `pueue log <task-id>` も確認する。
バックグラウンド hook の command log にある `exit: null` は成功を意味しない。
同じ hook の出力は再実行で上書きされ、ブランチ削除時に消えることもある。
長期保存する監査ログとしては使わない。[ログ仕様](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/config.md#wt-config-state-logs)

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
- `prefix+shift+c` — 現在のブランチを起点に作成・切り替え（`worktrunk.open-current`）
- `prefix+alt+x` — 削除候補を popup で選び、確認後に削除（`worktree-remove.sh`）

Herdr 組み込みの worktree 作成（`new_worktree`）は無効化し、このピッカーに置き換えている。
ピッカーは `show_remote_branches = true` で remote-tracking ブランチ（`origin/foo`）も出す。
`picker_placement = "popup"`、幅 80%・高さ 70% で表示し、既存のタブ・split の大きさを保つ。
plugin 設定は起動ごとに読まれるため、設定反映後の次のピッカーから有効になる。

削除 popup は primary と detached を除く worktree を一覧に出す。現在開いている
worktree も選べる。ブランチ名・パスを表示し、`Remove? [y/N]` に肯定した場合だけ
`wt remove --foreground` を実行する。確認中にブランチ・パス・HEAD が変わった場合は中止する。
未コミット変更があれば通常の wt 判定で削除を拒否する。ignored ファイルは削除対象に含まれる。
統合済みブランチは削除し、未統合ブランチは保持する。失敗時はエラーを表示して Enter を待つ。
成功後の Herdr close は既存の pre-remove / post-remove hook と pueue に任せる。
merge キーは追加していない。

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
更新後は `claude plugin list --json` でも user scope の登録と `enabled: true` を確認する。
コマンドが成功しても一覧で有効化を確認できなければ、apply を失敗として通知する。
表示の切り替えと既存環境への設定反映は [chezmoi diff の運用](../README.md#chezmoi-diff) を参照。

手動で更新する場合:

```sh
claude plugin marketplace update worktrunk
claude plugin update worktrunk@worktrunk --scope user
```

更新後は Claude Code を再起動する。v0.76 以降の activity marker hook は
`-C "$CLAUDE_PROJECT_DIR"` を指定し、セッション中に `cd` しても起動元の worktree を示す。
`wclaude` は設定ファイルを共有するが、別の `CLAUDE_CONFIG_DIR` を使うため、プラグインの
登録とキャッシュも確認する。独立して導入している場合は、その環境変数を指定して更新する。
今回の自動更新スクリプトは、この別 home や他の Claude プラグインを更新しない。

## Codex 連携と plugin の確認

４つの Codex config の既定値に Worktrunk marketplace と plugin の有効化を登録している。
既存の per-home 設定を優先するため、明示した `enabled = false` は保持する。
初回適用と導入スクリプト変更時に `run_onchange_after_05-codex-worktrunk.sh.tmpl` が動き、
標準 home、仕事環境では work1 / work2 / work3 に不足する plugin を導入する。
`CODEX_HOME` を１つずつ指定し、共有キャッシュの存在だけで完了とは判断しない。
明示的に無効化した home は導入を省き、その旨を表示する。

手動で導入する場合は対象 home を指定する。

```sh
CODEX_HOME="$HOME/.codex" wt config plugins codex install --yes
CODEX_HOME="$HOME/.codex" codex plugin list --marketplace worktrunk --json
```

確認する値は `.installed[]` の `pluginId == "worktrunk@worktrunk"`、`installed: true`、`enabled: true`。
marker を動かすには `features.hooks = true` も必要で、既定値は有効。導入後は Codex を再起動する。
開始時に作業中、Stop / PermissionRequest 時に入力待ち、SessionEnd 時に marker を消す。
本体の mise 更新と plugin の更新は別。更新するときは対象 home を指定して
`codex plugin marketplace upgrade worktrunk` を実行し、一覧で状態を再確認する。
[設定仕様](https://developers.openai.com/codex/config-reference/)、
[Worktrunk の Codex hook](https://github.com/max-sixty/worktrunk/blob/v0.77.0/plugins/worktrunk/.codex-plugin/plugin.json)

存在する Claude / Codex home をまとめて確認する読み取り専用タスクも用意している。

```sh
mise run check-worktrunk-plugins
```

標準・仕事用 home それぞれで管理 CLI の JSON 一覧を読み、登録・有効状態を検証する。
存在しない home は `absent (not checked)` と表示して作成しない。
不足・無効・取得失敗は終了コード 1。意図して無効化している home もこの確認では報告対象になる。
v0.77.0 の `wt config show` は plugin 存在判定に限界があるため、設定診断とこの確認を使い分ける。

## 状態確認と片付け候補

`wt-prune` は `wt step prune --foreground` の Zsh エイリアス。
デフォルトブランチへ統合済みのワークツリーとローカルブランチをまとめて削除する。
`git delete-squashed-branches` がワークツリー付きブランチの削除で失敗する場合も使える。
squash merge のほか、通常の merge や rebase で統合されたブランチも対象になる。
判定基準は wt のデフォルトブランチで、任意の比較先ブランチを指定する機能はない。

```sh
wt-prune --dry-run       # 削除候補を確認
wt-prune                 # 作成から1日以上の統合済み候補を削除
wt-prune --min-age=0s     # 作成から1日未満の候補も対象にする
```

未コミットの変更があるワークツリー、ロックされたワークツリー、メインワークツリーは残る。
削除時は通常の pre/post-remove hook が動く。現在のワークツリーも対象なら最後に削除し、
wt のシェル統合がメインワークツリーへ移動する。リモートの最新状態を判定に使う場合は、
先に `git fetch --prune` する。

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
PR は著者を限定せず取得し、`worktree-prs.py` が upstream の remote URL・ブランチ名と
PR の head repository・ブランチを照合する。ローカルだけ別名でも upstream 側で照合する。
同名の別 fork は除外し、複数の OPEN PR、削除済み fork、追跡先なし、detached HEAD、
remote の取得失敗・別ホスト・解決できない SSH alias は `unknown` として保留する。
PR の HEAD と現在のローカル HEAD が一致する場合だけ状態を表示する。
未 push コミットや同名ブランチの再利用などで不一致なら、古い MERGED PR に結び付けず保留する。
取得上限 1,000 件に達して該当 PR が見つからない場合も `unknown`。
`-` は取得先リポジトリの今回の PR 一覧に対応がないことを示し、別リポジトリへの PR までは調べない。

Herdr 内から実行した場合は `herdr api snapshot` を一度取得し、正規化したパスで照合する。
`HERDR` 列にはワークスペース ID、現在のセッションに未登録なら `-`、取得できない場合や
Herdr 外からの実行なら `unknown` を表示する。他の Herdr セッションまでは調べない。
この列と `PRUNE` は使用状況の補足で、削除の許可には使わない。

`MARKER` は同じ `wt list` snapshot の保存済み activity marker を表示する。
空欄・未設定は `-`。複数セッションが同じブランチを使うと、一方の終了で消えることもある。
プロセスの生存確認ではないので、marker の有無は BUCKET や削除の許可を変えない。

会話履歴、作業中の変更、ignored ファイル、PR の状態を確認したうえで、
確認済みの対象だけを `wt remove <path>` で削除する。監査スクリプト自体は削除しない。
会話の日付取得には macOS 標準の `date` / `stat` を使い、GNU coreutils の PATH に影響されない。

共通の検証入口は `mise run check-worktrunk`。関連ファイルの変更時は `hk check` からも実行する。
`dot_config/herdr/plugins/config/worktrunk/config.toml` 単独の変更も対象に含む。
picker 設定は TOML の構文、管理するキー、真偽値、配置方法、サイズを検証する。
配置は `split` / `popup`、サイズは正のセル数または `1%`〜`100%` を受け付ける。
管理元への `wt config show`、実際の wt による hook 展開、Claude / Codex plugin の導入・確認失敗、
Herdr の並行実行・再開・遅延 close、削除の確認・キャンセル・失敗、監査の PR 対応・marker・取得失敗・Herdr パス照合を検証する。
コピーとブランチの起点は一時リポジトリに実際の worktree を作って確認する。
Herdr・forge・削除 popup の外部操作はスタブに置き換え、利用中の worktree は変更しない。
シェルスクリプトは ShellCheck も通す。

## 設定変更時の確認

`wt config show` で管理元を検証し、通常ブランチと detached HEAD で変更した hook の
`wt hook <hook名> --dry-run` を確認する。展開結果だけを検証し、fetch や Herdr 操作は実行しない。

```sh
wt --config "$PWD/dot_config/worktrunk/config.toml" config show
wt config show
```

## 注意点

- hook は `~/.config/worktrunk/config.toml`（ユーザー設定）のみ。
  プロジェクト設定 `.config/wt.toml` はこのリポジトリでは使っていない
- プロジェクト設定の hook は初回実行時に承認が必要（`wt config approvals add`）。
  ユーザー設定の hook に承認は不要
