# Worktrunk (wt) の仕組み

Worktrunk（`wt` CLI）による git worktree 管理の構成メモ。
インストールからライフサイクル hook、Herdr / Claude Code 連携までこのリポジトリで管理している。

## 構成要素

| ファイル                                                   | 役割                                                      |
| ---------------------------------------------------------- | --------------------------------------------------------- |
| `dot_config/mise/config.toml`                              | mise で `worktrunk = "latest"` をインストール             |
| `dot_zshrc.tmpl`                                           | シェル統合（`wt config shell init zsh` を eval）          |
| `dot_config/worktrunk/config.toml`                         | ユーザー設定。ライフサイクル hook を定義                  |
| `dot_config/herdr/scripts/executable_worktree-open.sh`     | post-switch hook から呼ばれ、worktree を Herdr で開く     |
| `dot_config/herdr/scripts/executable_worktree-close.sh`    | post-remove hook から呼ばれ、Herdr ワークスペースを閉じる |
| `.chezmoiscripts/run_onchange_after_herdr-plugins.sh.tmpl` | Herdr の `herdr-worktrunk` プラグインをインストール       |
| `dot_claude/settings.json.tmpl`                            | Claude Code の worktrunk プラグイン有効化と worktree 権限 |

## インストールとシェル統合

- 本体は mise 管理（`dot_config/mise/config.toml` の `worktrunk = "latest"`）。
- `.zshrc` で `wt` が存在すれば `eval "$(command wt config shell init zsh)"` を実行。
  これで `wt switch` 後にシェルの cwd が worktree へ移動する（シェル統合なしでは cd できない）。

## ライフサイクル hook（`~/.config/worktrunk/config.toml`）

worktree の作成〜削除に合わせて 4 つの hook を定義している。

| Hook          | 名前    | やること                                                                                                                                              |
| ------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pre-switch`  | `fetch` | ローカルに存在しないブランチへ切り替えるとき先に `git fetch origin --prune`。remote-tracking ref からトラッキングブランチを作れるようにする           |
| `pre-start`   | `sync`  | `origin/<branch>` があれば upstream 設定 + `git merge --ff-only` で fast-forward。`wt switch --create` はベースから分岐するため、origin に同名ブランチがある場合に内容を揃える |
| `post-switch` | `herdr` | `worktree-open.sh` で switch 先 worktree を Herdr に開き、ワークスペースを自動レイアウト（primary worktree はスキップ）                              |
| `post-remove` | `herdr` | `worktree-close.sh` で対応する Herdr ワークスペースを閉じる                                                                                           |

### pre-switch: `fetch`

ショートカット（`^` `@` `-` `pr:` `mr:`）とローカルに既にあるブランチはスキップ。
オフライン等で fetch が失敗しても `|| true` で switch 自体は止めない。

### pre-start: `sync`

`wt switch --create <branch>`（Claude Code の WorktreeCreate hook や、ローカルに
branch がないと必ず `--create` を選ぶ herdr worktrunk ピッカー経由を含む）は
`origin/<branch>` が既に存在してもベースから分岐する。wt が upstream を設定して
いれば fast-forward。wt は upstream を設定しないことがあるので、その場合は
`origin/<branch>` が存在すれば upstream に設定してから fast-forward し、
どちらでもリモートの内容で開く。
diverge している・同名リモート branch がない場合はベースの内容のまま（`|| true`）。

### post-switch / post-remove: Herdr 連携

どちらも Herdr サーバーが動いていないときは失敗を無視する（`|| true`）。

## Herdr 連携の詳細

### worktree-open.sh（post-switch）

`herdr worktree open` でワークスペースを作成・フォーカスし、ワークスペースがまだ素の状態
（ペイン 1 つだけ）のときのみ以下をレイアウトする（レイアウト済みワークスペースへの
再実行ではペイン・タブを積み増さない）。post-start ではなく post-switch なのは、
herdr の worktrunk ピッカーで既存 worktree を開いたときにも発火させるため。
ガードが `already_open` ではなくペイン数なのは、ピッカーが `wt switch` の直後に自分で
ワークスペースを登録するため、hook 実行時には「登録済みだが未レイアウト」の状態が普通にあるから:

1. タブ 1: シェル（左）+ ファイルビューア（右）の split
2. タブ 2: lazygit（タブラベル `lazygit`）
3. タブ 3: hunk diff（左: working tree、右: PR base / デフォルトブランチとの merge-base からの branch diff）

### worktree-close.sh（post-remove）

削除された worktree のパスに一致するワークスペースを探して閉じる。
pueue 経由で 5 秒遅延実行するのがポイント: ワークスペースを閉じるとペインの
プロセスグループが kill されるため、`wt remove` を実行したペインで直接閉じると
wt 自身の trash 掃除（`.git/wt/trash` の rm）まで巻き添えになる。

ワークスペースを閉じると、閉じたのがフォーカス中でなくても herdr のフォーカスが
隣のワークスペースへ移ってしまうため、閉じる前にフォーカス中のワークスペースを
記録しておき、各クローズ直後に復元する（閉じた対象自身がフォーカス中だった場合は復元しない）。

### herdr-worktrunk プラグイン

`.chezmoiscripts/run_onchange_after_herdr-plugins.sh.tmpl` で
`devashish2203/herdr-worktrunk` をインストール。キーバインドは `docs/herdr.md` 参照:

- `prefix+shift+g` — worktree ピッカー（`worktrunk.open`）
- `prefix+shift+c` — カレントリポジトリを開く（`worktrunk.open-current`）

Herdr 組み込みの worktree 作成（`new_worktree`）は無効化し、このピッカーに置き換えている。

## Claude Code 連携

`dot_claude/settings.json.tmpl` で設定:

- `worktrunk@worktrunk` プラグインを有効化（marketplace: `max-sixty/worktrunk`）。
  worktrunk スキル（設定・hook のリファレンス）と `wt-switch-create` スキルが使える
- `permissions.allow` に `EnterWorktree` / `ExitWorktree` を追加。
  Claude Code の worktree 分離（`isolation: "worktree"`）が確認なしで動く

## 注意点

- hook は `~/.config/worktrunk/config.toml`（ユーザー設定）のみ。
  プロジェクト設定 `.config/wt.toml` はこのリポジトリでは使っていない
- プロジェクト設定の hook は初回実行時に承認が必要（`wt config approvals add`）。
  ユーザー設定の hook に承認は不要
