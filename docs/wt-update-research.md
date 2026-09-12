# Worktrunk 最近の更新と dotfiles 改善候補

実施状況: 2026-09-12 に優先項目１〜３を実施。detached HEAD の hook 修正、Claude plugin の `d44d68797a25` → `b611d86e8eff` 更新、リモートブランチの運用・設定コメント・操作スキルの整理を行った。項目４も実施し、監査の PRUNE 列と for-each / eval の操作ガイドを追加した。以下は実施前の調査記録。現行の操作は [運用メモ](wt.md) を参照。

追加レビューの改善１〜４も実施。hook の引数境界を修正し、共通の検証コマンドを追加した後、Herdr レイアウトの排他制御・再開、削除前の ID に固定した遅延 close、監査の snapshot 共通化・取得失敗の保留・Herdr 列を導入した。検証と現在の制約は [運用メモ](wt.md) に記載。

調査日: 2026-09-12。対象 HEAD: `085d28f399efe8d4aa25d093044532aebe039266`。
インストール済み CLI は `wt v0.77.0`。GitHub の最新公開版も v0.77.0、公開日時は 2026-09-08 22:12 UTC。v0.69.0 から v0.77.0 までの公開リリースと v0.77.0 タグのソースを比較した。以下は公開済みの機能で、main の未リリース機能は含めない。[v0.77.0 リリース](https://github.com/max-sixty/worktrunk/releases/tag/v0.77.0)

本体の更新より、既存 hook の互換性確認、プラグイン更新、運用文書への新しいコマンドの反映が中心になる。調査では設定の変更、インストール、`chezmoi apply`、削除、コミットを行っていない。

## 最優先: detached HEAD で hook が展開できない

v0.77.0 は detached worktree の `branch` を文字列 `HEAD` から未定義へ変更した。この dotfiles の `pre-switch.fetch`、`pre-start.sync`、`post-switch.herdr` は、いずれも未保護の `{{ branch }}` を含む。
[変更点](https://github.com/max-sixty/worktrunk/releases/tag/v0.77.0)、
[修正 PR #4010](https://github.com/max-sixty/worktrunk/pull/4010)。

一時 Git リポジトリを detached HEAD にして、管理元の設定を直接指定し、各 hook を `--dry-run` で確認した。上記３つは終了コード 1、`undefined value` で失敗し、`post-remove` は成功した。実際の hook、fetch、Herdr 操作は実行していない。

`pre-switch` 冒頭だけの `default('')` や、シェルの `case`、`|| true` では残りのテンプレート展開を防げない。`wt config show` は現行設定で成功するため、設定の読み込み検査だけでも見つからない。

修正案は次のとおり。

- `pre-switch.fetch` と `pre-start.sync` の文字列全体を `{% if branch %} ... {% endif %}` で囲み、detached 時はブランチ同期を省く。
- `post-switch.herdr` のラベル引数を `{{ branch | default(short_commit) }}` にして、detached 時は短縮 SHA を使う。

提案を一時設定ファイルにだけ反映し、通常の `main` と detached HEAD の両方で３つの dry-run が成功することを確認した。通常ブランチの展開結果も維持できた。Herdr の実動作確認は実装時に必要。
対象は [Worktrunk 設定](../dot_config/worktrunk/config.toml) の 15、25、34 行。

## リモートブランチの開き方を整理する

v0.76.0 から、作成するブランチと起点のリモートブランチが同名のときだけ upstream を設定することが明確になった。`branch.autoSetupMerge` にも左右されない。
[リリース](https://github.com/max-sixty/worktrunk/releases/tag/v0.76.0)、
[現行コマンド仕様](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/switch.md)。

| 意図                                   | コマンド                                                        |
| -------------------------------------- | --------------------------------------------------------------- |
| 既存のリモートブランチを開く           | `wt switch origin/foo`                                          |
| 同じ名前で起点と upstream を明示する   | `wt switch --create foo --base origin/foo`                      |
| リモートを起点に別の新規ブランチを作る | `wt switch --create bar --base origin/foo`。upstream は付かない |

インストール済み Herdr プラグインの `helpers.sh` と `picker.sh` を読むと、`origin/foo` は既存 remote-tracking ref と判定され、そのまま `wt switch origin/foo` に渡される。`show_remote_branches = true` はすでに設定済みなので、一覧の `origin/foo` を選ぶ運用がよい。

一方、ローカル `foo` がなく `origin/foo` だけある状態で、単に `foo` と入力すると、プラグインは `--create foo` を選び得る。Claude プラグインの `WorktreeCreate` も引き続き `--create` を使う。したがって、v0.76.0 だけを理由に `pre-start.sync` を削除してはいけない。
[公式 Claude hook](https://github.com/max-sixty/worktrunk/blob/v0.77.0/plugins/worktrunk/hooks/hooks.json)。

まず [運用メモ](wt.md) と設定コメントの「Herdr はローカルにないと常に --create」という説明を直し、既存 remote を開く経路を整理する。その後、`sync` の適用範囲を狭める。現行の同名 remote への自動同期は、意図して指定した別の `--base` の内容にも fast-forward を試みるため、全リポジトリ共通の方針として残すかを分けて判断したい。

なお v0.76.0 は PR 経由の `pre-switch` にも解決後の実ブランチ名を渡す。`pr:*` / `mr:*` の文字列判定だけで PR 操作をスキップできる、というコメントも再確認が必要。

## Herdr 連携で追加できる操作

Worktrunk 本体とは別の更新だが、関連する [herdr-worktrunk の PR #27](https://github.com/devashish2203/herdr-worktrunk/pull/27) は 2026-08-27 に merge 操作を追加した。インストール済み manifest にも `worktrunk.remove`、`worktrunk.merge`、`worktrunk.merge-no-squash` が存在する。

この dotfiles では switch/create の２つだけをキーに割り当てている。作成後の片付けまで Herdr から行いたいなら、まず remove、必要なら merge-no-squash を追加する候補になる。ローカル merge が運用に合うリポジトリで使う。GitHub の PR merge を代替するものではない。

プラグインの merge は `wt merge --no-remove` の後に `wt remove --foreground` を実行し、削除完了後にワークスペースを閉じる。既存の通常 CLI 操作では pueue 経由の `post-remove` が必要なので、この追加を理由に pueue を削除しない。キーを追加する際は `docs/herdr.md` も追従させる。

## 設定検証を更新手順に追加する

v0.77.0 の `wt config show` は、設定ファイルの読み込み・構文エラー、不正な `[list] columns`、不正な `approvals.toml` で終了コード 1 を返すようになった。以前は常に 0 だったため、設定変更時の確認に使いやすくなった。ただし未知のキーや非推奨キーは警告だけで終了コード 0。hook の全実行条件を検証するものでもない。[変更 PR #3999](https://github.com/max-sixty/worktrunk/pull/3999)

この repo では管理元の `dot_config/worktrunk/config.toml` を明示して検証し、反映後には通常の `wt config show` で実際に読まれる設定も確認する。hook を編集した場合は、通常ブランチと detached HEAD の両方で `wt hook <hook名> --dry-run` を併用する。

```sh
wt --config "$PWD/dot_config/worktrunk/config.toml" config show
wt config show
```

v0.77.0 の移行プレビューは `wt config update --output=-`。旧 `--print` は廃止された。chezmoi 管理ファイルを直接書き換える前に差分を確認できる。現在の設定には `[select]` や旧 `commit-generation` などの移行対象は見当たらず、今すぐ移行を実行する理由はない。[変更 PR #4021](https://github.com/max-sixty/worktrunk/pull/4021)、[管理設定](../dot_config/worktrunk/config.toml)

## cleanup の候補判定に stable になった prune を使う

`wt step prune`、`for-each`、`eval` は v0.76.0 で experimental 扱いを終了した。新設コマンドではなく、既存機能が安定扱いになった変更である。[v0.76.0 リリース](https://github.com/max-sixty/worktrunk/releases/tag/v0.76.0)

現在の [worktree-audit.sh](../dot_agents/skills/poteto-mode/scripts/executable_worktree-audit.sh) は `git merge-base --is-ancestor` で統合済みかを判定し、squash merge は PR 状態から補っている。ここに次の読み取り専用プレビューを加えると、Worktrunk 自身の content integration 判定も候補選定に使える。

```sh
wt step prune --dry-run --min-age=2d --format=json
```

`prune` は既定で 1 日以内の worktree / branch を除外し、main と locked worktree を除外する。実行時は branch の削除も対象で、各 worktree の pre-remove / post-remove hook が動く。既存の Herdr close hook を利用できる。[v0.77.0 の prune 文書](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/step.md#wt-step-prune)

ただし [cleanup playbook](../dot_agents/skills/poteto-mode/playbooks/worktree-cleanup.md) は進行中・ピン留め中のチャット、ignored files、未送信の作業も確認する。`prune` はこの判定を代替しない。最初の導入範囲は dry-run 結果を audit に添えるところまでとし、確認済み対象だけを現在と同じ `wt remove <path>` で処理するのが合う。

JSON を取り込む場合は `wt list` と別形式である点に注意する。prune は候補オブジェクトの JSON 配列を出力し、dry-run は予測の `branch_deleted`、実行は結果の `branch_outcome` を返す。v0.72.0 の変更ログだけから「すべて branch_outcome に統一された」と解釈せず、v0.77.0 のコマンド仕様に合わせる。[v0.77.0 の JSON 仕様](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/step.md#wt-step-prune)

v0.70–0.76 には prune の並列処理と削除競合の修正もある。ただしこの dotfiles は removal hook を持つので、upstream のベンチマーク値をそのまま高速化の見込みとして使わない。[v0.70.0](https://github.com/max-sixty/worktrunk/releases/tag/v0.70.0)、[v0.72.0](https://github.com/max-sixty/worktrunk/releases/tag/v0.72.0)

## for-each と eval をスキルのコマンド表に追加する

[wt-worktree-ops](../dot_agents/skills/wt-worktree-ops/SKILL.md) は create / switch / list / merge / remove を扱うが、まとめて状態を確認するコマンドがない。`wt step for-each -- git status --short` と `wt step eval '{{ primary_worktree_path }}'` を追加すれば、worktree ごとのループやパス推測を減らせる。for-each は逐次実行で、個別コマンドの失敗後も続行し、集計を出す。テンプレート展開エラーでは全体が停止する。`--` の後は shell 文字列ではなく argv なので、pipe が必要なら明示的に `sh -c` を使う。[v0.77.0 の for-each / eval 文書](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/step.md#wt-step-for-each)

## 開発プロジェクトの初回準備に copy-ignored を検討する

現在は依存・キャッシュを複製する hook がない。Node / Rust などの作業先では、次の opt-in 設定が候補になる。`.worktreeinclude` がある repo だけコピーするため、dotfiles 自身に重い初期化を増やさずに導入できる。

```toml
[post-start]
copy = "wt step copy-ignored --require-include"
```

コピー機能や `--require-include` 自体は今回の新機能ではない。v0.74.0 はコピー途中に消えた source file の扱いを修正し、v0.77.0 は reflink / full copy の区別と JSON の `reflinked` / `written` を追加した。macOS の APFS では reflink により変更されるまでディスクブロックを共有する。対象は `.worktreeinclude` で `node_modules/` や `target/` などに絞る。[v0.74.0 リリース](https://github.com/max-sixty/worktrunk/releases/tag/v0.74.0)、[v0.77.0 の copy-ignored 文書](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/step.md#wt-step-copy-ignored)、[変更 PR #4025](https://github.com/max-sixty/worktrunk/pull/4025)

`post-start` はバックグラウンドなので、Herdr が開いてもコピー完了を保証しない。起動する agent や次の hook が直ちに依存を必要とするプロジェクトでは `pre-start` に置く。まず対象プロジェクトで `wt step copy-ignored --require-include --dry-run` の内容と実際の待ち時間を確認してから採用する。

## Claude plugin を本体とは別に更新する

調査環境の Claude plugin cache `worktrunk/worktrunk/d44d68797a25/hooks/hooks.json` には、activity marker のコマンドに `-C "$CLAUDE_PROJECT_DIR"` がなかった。v0.76.0 はこの指定を追加し、セッション中に `cd` しても起動元の worktree に marker を付けるよう修正している。本体が最新でも plugin cache に修正が入っているとは限らない。[v0.76.0 リリース](https://github.com/max-sixty/worktrunk/releases/tag/v0.76.0)、[v0.77.0 の hook 定義](https://github.com/max-sixty/worktrunk/blob/v0.77.0/plugins/worktrunk/hooks/hooks.json)

同じキャッシュと v0.77.0 を比較すると、`WorktreeCreate` の `pipefail`、`WorktreeRemove` の対象 worktree を `-C` に渡す処理にも差がある。既存の marketplace / enabledPlugins 設定を利用し、Claude の Worktrunk plugin を更新して hook の内容を確認する候補を優先したい。`pclaude` の設定共有と、実際に読み込む plugin cache の両方を確認する。キャッシュファイルの手編集は更新手順にしない。

## Codex の activity marker を追加する

この repo は Claude Code の Worktrunk plugin を有効化している一方、Codex の [config defaults](../dot_codex/modify_private_config.toml) に Worktrunk の登録はない。調査環境の `~/.codex/config.toml` にも `worktrunk` の記述はなかった。v0.77.0 の `wt config plugins codex install` は marketplace 登録に加えて plugin 本体もインストールする。内部では `codex plugin marketplace add max-sixty/worktrunk` と `codex plugin add worktrunk@worktrunk` を実行する。[v0.77.0 の installer 実装](https://github.com/max-sixty/worktrunk/blob/v0.77.0/src/commands/config/codex.rs)

導入すると `wt list` に作業中・入力待ちの marker が出る。v0.71.0 では SessionEnd で marker を消す修正も入り、終了済みセッションの表示が残りにくくなった。[v0.71.0 リリース](https://github.com/max-sixty/worktrunk/releases/tag/v0.71.0)

work1 / work2 / work3 は plugins directory を共有するが `config.toml` は別々。この構成ではキャッシュ共有だけで各 home の有効化まで完了したと判断しない。導入時は利用する home を `CODEX_HOME="$HOME/.codex_work1"` のように明示し、各 home で登録・有効化を確認する。Worktrunk の実装も `CODEX_HOME` を認識する。work 用 home は現在の調査環境には存在せず、複数 home でのインストール実動作までは検証していない。[installer 実装](https://github.com/max-sixty/worktrunk/blob/v0.77.0/src/commands/config/codex.rs)、[work1 の plugin symlink](../dot_codex_work1/symlink_plugins)、[work1 の独立 config](../dot_codex_work1/modify_private_config.toml)

導入コマンドはユーザー環境へ書き込むため、この調査では実行していない。後から導入する場合も、本体の mise 更新と plugin の更新を別の手順として文書化する。

## 維持する設定と導入順

- `[list] json-schema = 2` は維持してよい。v0.77.0 で既定値も 2 になったため、「将来切り替わる」というコメントだけを更新する。audit はすでに `.items` / `.repo` を読み、インストール済み Herdr plugin も envelope を処理できる。[schema 変更 PR #4038](https://github.com/max-sixty/worktrunk/pull/4038)
- zsh / bash は起動時に `wt config shell init` を評価する現在の構成でよい。非対話の調査プロセスで出た `Shell integration not active` は、管理された rc 設定が欠けている証拠ではない。
- `wt switch --execute` を今後使う場合は、v0.76.0 からプログラムと argv を直接渡す仕様になった点を反映する。この repo の `wcodex1` などの alias や `codex()` 関数は、そのまま `-x` から呼べない。現在の設定には移行対象の `-x` 呼び出しは見つからなかった。[v0.76.0 リリース](https://github.com/max-sixty/worktrunk/releases/tag/v0.76.0)

実装するなら、detached hook の修正、Claude plugin 更新、remote 運用と説明の整理を先に行う。次に prune の読み取り専用プレビュー、for-each / eval、Codex marker を追加する。Herdr の remove / merge キーと依存コピーは、使うプロジェクトを選んで採用する。今回の変更はこの調査メモだけで、設定への提案は未適用。
