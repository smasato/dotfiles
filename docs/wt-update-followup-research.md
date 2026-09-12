# Worktrunk 改善候補の再調査

実施状況: 2026-09-12 に、優先順リストの **1 / 2 / 4 / 5 / 6 / 7 / 10** を実施した。
PR の upstream・リポジトリ・HEAD 照合、共通検証の `config show`、hook ログの復旧手順、
CLI による各 home の plugin 確認、Codex plugin の導入、監査の MARKER 列、Herdr popup を追加した。
現在の仕様は [運用メモ](wt.md) を参照。以下の調査本文は実装前の記録。

先行7項目の検証は共通テスト57件・ShellCheckが成功。標準 Claude / Codex は実際の CLI で installed / enabled を確認した。
Codex の実 hook を一時 Git リポジトリで実行し、作業中・入力待ち・終了時の marker 消去を確認した。
仕事用 home は現環境に存在せず、各 home の導入・確認と無効化の保持はスタブで検証した。
Herdr は popup 80% × 70% の設定読み込みとピッカー起動を確認し、確認用プロセスを終了した。
Computer Use が Ghostty へのアクセスを許可しなかったため、画面の見た目は未確認。
監査スクリプト・popup 設定・Codex 設定は配置済みで、Codex 導入スクリプトも対象を限定して適用した。

残りの **3 / 8 / 9** も議論で合意した範囲を実装した。

- 3: グローバルの `pre-start.sync` を削除し、明示した起点を保持する。既存リモートは `wt switch origin/foo` で選ぶ。
- 8: `pre-start.copy` に `wt step copy-ignored --require-include` を追加。primary の `.worktreeinclude` に一致する ignored ファイルを新規作成時だけコピーし、既存ファイルは保持する。今回は共通機構と記述例までで、個別リポジトリへの include 追加は対象外。
- 9: `prefix+alt+x` に確認付き削除 popup を追加。ブランチ名とパスを示し、既定 No の確認後に `wt remove --foreground` を実行する。merge キーは今回の対象外。

追加後の共通テストは68件成功し、ShellCheck・Prettier・Pkl 検証も成功した。
一時リポジトリで起点の保持、コピーの対象・新規作成限定・失敗時の起動中止、
dirty worktree の削除拒否と未統合ブランチの保持を確認した。削除 popup の確認・キャンセル・
対象変更・失敗表示はスタブで検証し、実画面からの操作は未確認。
対象4ファイルは `chezmoi apply --exclude=scripts` で配置し、配置後の差分はゼロ。
Herdr の `server reload-config` は diagnostics なしの `applied` を返した。

現在の設定と復旧手順は [運用メモ](wt.md)、キー一覧は [Herdr チートシート](herdr.md) を参照。

調査日: 2026-09-12。対象 HEAD: `62fd5f3`。前回の [調査記録](wt-update-research.md) と、Worktrunk / herdr-worktrunk の公式リリース、タグ付き文書、ソースを再確認した。設定変更、プラグインの導入・更新、`chezmoi apply`、削除、コミットは行っていない。

前回の主要修正は完了している。次に優先したいのは、共通検証への `config show` 追加と、監査の PR 照合の修正。Codex marker・Herdr 操作キー・依存コピーは未導入の選択肢として残る。

## 前回の改善候補との照合

前回の優先項目と追加レビューの修正は反映されている。ただし、設定検証の自動化には下記の不足がある。「候補として未導入」と「不具合修正が未完了」は分けて扱う。

| 前回の項目                                                | 現状                                              | 確認先                                                                                                    |
| --------------------------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| detached HEAD の hook 修正・引数境界                      | 実装済み                                          | [config.toml](../dot_config/worktrunk/config.toml)、[hook テスト](../scripts/test-worktrunk-hooks.py)     |
| Claude plugin 更新                                        | 実施済み。標準 home は毎回 apply 時に更新         | [更新スクリプト](../.chezmoiscripts/run_after_04-claude-worktrunk.sh.tmpl)。実キャッシュは `b611d86e8eff` |
| remote 操作・schema 2・for-each / eval の説明             | 反映済み                                          | [運用メモ](wt.md)、[操作スキル](../dot_agents/skills/wt-worktree-ops/SKILL.md)                            |
| prune の監査列・snapshot 共通化・取得失敗の保留・Herdr 列 | 実装済み                                          | [監査スクリプト](../dot_agents/skills/poteto-mode/scripts/executable_worktree-audit.sh)                   |
| Herdr の排他・途中再開・ID を照合する遅延 close           | 実装済み。手動復旧コマンドも追加済み              | [worktree.py](../dot_config/herdr/scripts/worktree.py)、[運用メモ](wt.md)                                 |
| 共通検証・Herdr plugin 更新の検証と記録                   | 実装済み。ただし `config show` の自動実行は未実装 | [check-worktrunk.py](../scripts/check-worktrunk.py)、[更新タスク](../scripts/update-herdr-plugins.py)     |
| Codex activity marker                                     | 未導入                                            | 管理元の４つの config と現環境の `~/.codex/config.toml` に登録なし                                        |
| Herdr remove / merge キー                                 | 未導入。任意の操作追加                            | [キー設定](../dot_config/herdr/config.toml.tmpl) は `worktrunk.open` / `open-current` のみ                |
| copy-ignored                                              | 未導入。プロジェクトごとの採用候補                | [Worktrunk 設定](../dot_config/worktrunk/config.toml) にコピー hook なし                                  |
| 同名 remote への sync の範囲縮小                          | 挙動は維持。回避方法の文書化まで完了              | 明示 `--base` でも同期を試みる。現状は呼び出しごとに `--config-set 'pre-start.sync=""'`                   |

前回後の `e80b3d6` では `herdr-worktrees status/resume/retry-close` と検証付き plugin 更新、`62fd5f3` では `wt-prune` エイリアスも追加されている。この２つを新しい未実装候補として挙げる必要はない。

Codex の work1 / work2 / work3 と Claude の work 用 plugin directory は調査環境に存在しない。複数 home の導入実動作は未確認。標準 Claude の更新完了を work 用 home の導入完了とは扱わない。仕事用 home の plugin 管理が別である点は、既に [アカウント運用](claude-accounts.md) に記載されている。

## 優先する追加改善

### 1. 共通検証に config show を加える

[check-worktrunk.py](../scripts/check-worktrunk.py) は ShellCheck と unittest を実行するが、`wt config show` は呼んでいない。[hook テスト](../scripts/test-worktrunk-hooks.py) が呼ぶのは `wt hook ... --dry-run`。そのため、前回提案した設定診断は手動手順に留まっている。

管理設定の一時コピーに次を加え、実際の v0.77.0 で確認した。

```toml
[list]
columns = ["not-a-real-column"]
```

| 実行                                                             | 終了コード            |
| ---------------------------------------------------------------- | --------------------- |
| `wt --config <一時設定> config show`                             | 1。未知のカラムを検出 |
| `wt --config <一時設定> hook pre-switch --dry-run --branch=main` | 0。検出しない         |

共通検証の最初に管理元を明示した `config show` を加える。配置後の通常 `wt config show` は別の確認として残す。未知キーが警告だけになるケースは引き続き診断出力を確認する必要がある。[v0.77.0 の設定診断修正](https://github.com/max-sixty/worktrunk/pull/3999)

これは現行設定のエラーではなく、今後の設定変更を検出する仕組みの不足。現行の管理元・配置済み設定は両方とも `config show` が成功し、ファイル内容も一致した。

### 2. 監査の PR を upstream とリポジトリも使って照合する

[監査スクリプト](../dot_agents/skills/poteto-mode/scripts/executable_worktree-audit.sh) は `number,state,headRefName` だけを取得し、ローカル `.branch` と `headRefName` の一致で PR を選ぶ。REMOTE 列は正しい upstream を表示するが、PR 列の照合には使っていない。

実装中の jq 式をそのまま抽出し、合成 JSON で次を再現した。

| 入力                                                                   | 現在の結果  | 問題                                 |
| ---------------------------------------------------------------------- | ----------- | ------------------------------------ |
| ローカル `topic`、別 fork の `topic` に OPEN PR                        | `#7/OPEN`   | 他のブランチをこの作業の PR と扱う   |
| 作り直した `topic`、古い同名 PR が MERGED                              | `#3/MERGED` | 現在のコミットが統合済みか分からない |
| ローカル `local-topic`、upstream は `origin/topic`、PR head は `topic` | `-`         | 実際の OPEN PR を見落とす            |

特に別名ローカルブランチでは `hold-open-pr` を付けられなくなる。監査自体は削除せず、playbook に手動確認もあるので、直接削除する不具合ではない。

取得項目に `headRepository` / `headRepositoryOwner` / `headRefOid` などを追加し、upstream の remote URL・ブランチ名と照合する。古い MERGED PR は現在の HEAD との関係も確認し、一意に対応を証明できない場合は `unknown` に保留する。単純な SHA 不一致は、ローカルの未 push コミットでも起きるため「PR なし」の根拠にしない。これらの JSON 項目は [GitHub CLI の公式仕様](https://cli.github.com/manual/gh_pr_list) で提供されている。

## 公開版と未リリースの区別

GitHub API でも最新リリースと日時を確認した。Worktrunk 本体をさらに更新する必要は、現時点ではない。

| 対象            | 最新公開リリース                                   | main                                                                |
| --------------- | -------------------------------------------------- | ------------------------------------------------------------------- |
| Worktrunk       | `v0.77.0`、2026-09-08 22:12:09 UTC、`0683ad85c753` | `b611d86e8eff`、2026-09-11 17:16:22 UTC。公開タグから 21 コミット先 |
| herdr-worktrunk | `v0.7.0`、2026-08-27 19:18:13 UTC                  | `4be9bbbaab1d`、2026-09-08 05:52:52 UTC。公開タグから 1 コミット先  |

一次情報: [Worktrunk release API](https://api.github.com/repos/max-sixty/worktrunk/releases/latest)、[Worktrunk の差分](https://github.com/max-sixty/worktrunk/compare/v0.77.0...b611d86e8eff1372467393c8a88308bff6f4dcfc)、[herdr-worktrunk release API](https://api.github.com/repos/devashish2203/herdr-worktrunk/releases)、[herdr-worktrunk の差分](https://github.com/devashish2203/herdr-worktrunk/compare/v0.7.0...4be9bbbaab1dfbecc81b298d30624052d0c432d1)。日時と差分数は調査時点の値。

Claude plugin のキャッシュが `b611d86e8eff` でも、本体 `wt v0.77.0` に main の Rust 実装修正が入るわけではない。次の修正は未リリースとして扱う。

- `wt merge` が worktree を削除した場合、その場所に紐付く `post-commit` を起動しない修正。v0.77.0 は注意点を文書化しているが、動作修正はタグより後。現在のユーザー設定に `post-commit` はないため、これだけを理由に開発版を導入する必要はない。別リポジトリの project hook を追加する際には関係する。[PR #4049](https://github.com/max-sixty/worktrunk/pull/4049)、[v0.77.0 hook 文書](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/hook.md)
- plugin の存在確認を設定ファイルの推測から各 CLI の JSON 出力へ変える修正。uninstall が失敗したのに成功と扱う問題や、`wt config show` の Claude plugin 存在判定が対象。v0.77.0 の `config show` だけで plugin の導入状態を確定せず、`claude plugin list --json` など実際の管理 CLI の結果も確認する。[PR #4048](https://github.com/max-sixty/worktrunk/pull/4048)、[PR #4054](https://github.com/max-sixty/worktrunk/pull/4054)

herdr-worktrunk の main にだけある変更は tab mode のシェル別コマンド生成。workspace mode を使う現在の構成を理由に追加変更する必要はない。[PR #31](https://github.com/devashish2203/herdr-worktrunk/pull/31)

## 前回の未採用候補を再確認

### Codex activity marker

導入候補として残る。v0.77.0 の installer は marketplace の登録と plugin の導入まで行う。利用する各 `CODEX_HOME` で登録・有効化を確認する必要があるという前回の判断は変わらない。[v0.77.0 installer](https://github.com/max-sixty/worktrunk/blob/v0.77.0/src/commands/config/codex.rs)

追加で、監査が既に取得する `wt list` schema 2 の `marker` を補足表示に使える。Claude plugin 導入済みなら Codex 導入前でも有用。`symbols` から絵文字を切り出す必要はない。[v0.77.0 リリース](https://github.com/max-sixty/worktrunk/releases/tag/v0.77.0)

ただし marker はプロセスの生存証明ではない。ブランチ単位の保存値で、plugin はイベントごとに set / clear する。同じブランチで複数セッションを使う場合は別セッションの終了で消える可能性があり、空欄を削除許可に使わない。この限界は保存形式と hook の動作からの推論。[marker の保存仕様](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/config.md#wt-config-state-marker)、[Claude hook 定義](https://github.com/max-sixty/worktrunk/blob/v0.77.0/plugins/worktrunk/hooks/hooks.json)

### Herdr の remove / merge キー

追加可能な操作として残るが、利用方針を決めてからでよい。特に `merge-no-squash` はコミットを潰さない指定であり、rebase や未コミット変更の commit まで無効にする指定ではない。プラグインは `wt merge --no-remove` 成功後に `wt remove --foreground` を呼ぶ。GitHub の PR merge を代替するものではない。[固定コミットの merge 実装](https://github.com/devashish2203/herdr-worktrunk/blob/4be9bbbaab1dfbecc81b298d30624052d0c432d1/merge.sh)

### copy-ignored

`.worktreeinclude` を置いたプロジェクトだけに適用する候補として残る。標準的な導入は `wt step copy-ignored --require-include`。既存ファイルは上書きせず、コピー対象は ignored と include の両方に一致するものに限られる。プロジェクトのビルドに直ちに必要なら、ユーザー `pre-start` に置くのが分かりやすい。[v0.77.0 copy-ignored 仕様](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/step.md#wt-step-copy-ignored)

順序には追加の注意がある。user と project の `post-*` は別々のバックグラウンド pipeline なので、user `post-start` のコピー完了を project `post-start` のビルドは待たない。`[[post-start]]` に変えても source をまたぐ順序は作れない。依存する操作を同じ source の pipeline にまとめるか、コピーを `pre-start` で完了させる。[v0.77.0 hook の実行順序](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/hook.md#project-vs-user-hooks)

## 前回以外の小さな改善候補

### Worktrunk hook のログを復旧手順から辿れるようにする

`herdr-worktrees status` と pueue のログだけでは、Worktrunk が起動した shell の出力を追えない。運用メモに Worktrunk 側のログ一覧を加えると、Python 実装が状態を保存する前のエラーも調べやすい。

```sh
wt config state logs
wt config state logs --format=json
```

JSON の `hook_output` には `path`、`branch`、`source`、`hook_type`、`name` がある。`post-switch` / `post-remove` の `herdr` 出力を絞り込める。コマンド履歴の background hook の `exit` は `null` なので成功判定には使わない。同じ hook の再実行で出力は上書きされ、branch 削除時にログ subtree も消えるため、永続的な監査記録の代わりにはならない。[v0.77.0 ログ仕様](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/config.md#wt-config-state-logs)

### Herdr picker を popup にする

これは不具合修正ではなく操作上の好み。現在の split / 複数タブのレイアウトを一時的に縮めたくない場合、plugin 設定に `picker_placement = "popup"` を指定できる。`popup_width` と `popup_height` も調整可能。herdr-worktrunk v0.7.0 で公開済みだが、Herdr 本体は 0.7.4 以上が必要。採用時に表示サイズを実機で確認する。[v0.7.0 の picker 設定](https://github.com/devashish2203/herdr-worktrunk/blob/v0.7.0/README.md#picker-presentation)

## sync の適用範囲は既存の判断事項

明示的な `--base` にも同名 remote への同期が適用される点は、前回から残る方針の選択。hook で `base` は参照できるが、ユーザーが `--base` を明示したかを示す変数は公式の公開変数表にない。`base == default_branch` だけの判定では、既定の main と明示的な `--base main` は区別できない。[v0.77.0 変数表](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/hook.md#template-variables)

現在の呼び出しごとの `--config-set 'pre-start.sync=""'` を残すか、グローバルの同期を外して対象リポジトリの `[projects]` へ移す方式が候補。`[projects]` の hook はグローバル hook に追加されるため、プロジェクト側へ空の hook を足すだけでは無効化できない。この点は scalar の上書き規則と異なる。[v0.77.0 projects 設定と優先順位](https://github.com/max-sixty/worktrunk/blob/v0.77.0/docs/public/config.md#user-project-specific-settings)

## 今回の検証範囲

- 対象 HEAD は `62fd5f3c75ad4629ef261049f03294381baf6515`。調査開始時の作業ツリーは clean。
- `mise run check-worktrunk` は 40 件すべて成功。実際の wt のテンプレート展開と、スタブを使う Herdr・Claude plugin・監査テストを含む。実タブ操作の確認ではない。
- 管理元を明示した `wt config show` と、配置済み設定に対する通常の `wt config show` はともに終了コード 0。
- 不正カラムの検出差と PR の誤照合は一時ファイル・合成データで確認。管理設定の変更、実 worktree の作成・削除、plugin 更新、`chezmoi apply` は行っていない。
- この再調査で変更するのは調査文書のみ。上の改善案は未実装。
