# Herdr ショートカットチートシート

prefix キーは **`ctrl+f`** に変更済み（デフォルトは `ctrl+b`）。
以下の `prefix+X` は「`ctrl+f` を押してから `X`」の意味。

macOS では prefix モード中に ASCII 入力ソースへ自動切り替えする設定
（`switch_ascii_input_source_in_prefix = true`）を有効化しているため、
日本語 IME が ON でも prefix コマンドはそのまま効く。

## v0.9.0 での運用

サイドバーは `agent_panel_sort = "priority"` で確認待ちのエージェントを優先表示する。
通知が来たら `prefix+o` で通知元へ移動し、`prefix+space` で直前のペインへ戻る。
順に確認するときは `prefix+a` / `prefix+shift+a`、番号が分かる場合は `prefix+alt+1..9` を使う。

Claude のアカウント表示は **Team が青、Max が紫**。SessionStart hook が報告した値を色分けする。
Codex は ChatGPT のプラン（**Business が青、Pro 20x / Pro 5x が紫、Plus が緑**）と
work seat（`w1` / `w2` / `w3`、個人の `~/.codex` は無印）を `~/.codex/herdr-codex-account.sh`
が報告し、同じ行に表示する。起動直後は zsh の `codex` ラッパー関数（`wcodexN` alias も経由）が、
resume / restore 後は Codex の SessionStart hook（最初のプロンプト送信時に発火）が同じスクリプトを呼ぶ。
新しい hook は各 CODEX_HOME で一度 `/hooks` から trust する必要がある。
Claude/Codex/Grok の独自行にも `machine` を含め、複数マシン接続時に実行先を確認できるようにしている。

### 明示コピー

`copy_on_select = false` に設定している。マウスでドラッグ・ダブルクリックしても
クリップボードは上書きせず、選択後に `Cmd+C` でコピーする。
ペインの出力が続いていても選択は保持される。

### エージェントへの依頼と待機

Herdr 経由でエージェントへ依頼するときは `agent prompt --wait` を使う。
インストール済みの Herdr スキルもこの手順を標準としている。
対象マシンの Herdr ペイン内で `herdr agent list` を実行し、対象の名前またはペイン ID と状態を確認する。
以下の `AGENT_TARGET` は、依頼を受け付けられる `idle` / `done` の対象に置き換える。

```sh
herdr agent prompt AGENT_TARGET "現在の差分をレビューして、修正が必要な点を報告してください。" --wait --timeout 60000
herdr agent read AGENT_TARGET --source recent-unwrapped --lines 120
```

`--timeout` の単位はミリ秒。`--wait` は作業開始を観測してから、
`idle` / `done` / `blocked` のいずれかで戻る。`blocked` は承認・質問待ちなので、
待機が終わっただけで作業完了とは判断せず、出力を確認する。
作業中の対象への送信は、その時点の作業終了で待機が終わる場合があるため、完了待ちには次を使う。

```sh
herdr agent wait AGENT_TARGET --timeout 60000
```

タイムアウトはエージェントの作業を停止しない。
`timeout` / `agent_prompt_stalled` が返ったら `agent get` と `agent read` で確認し、
送信済みの依頼を重複送信しない。まだ作業中なら `agent wait` で待機を続ける。
worker の対象を操作するときは worker 内で実行する。UI のマシン切り替えだけでは CLI の接続先は変わらない。

### worker マシンを同じウィンドウにまとめる

接続先の SSH 設定を確認したうえで、対話シェルから一度登録する。
以下の `SSH_HOST` は実際の SSH ホスト名に置き換える。

```sh
herdr machine add SSH_HOST --label worker
herdr machine list
```

既定では接続先の default セッションを使う。名前付きセッションを使っている場合は
登録時に `--remote-session SESSION_NAME` を指定する。
登録したマシンは開いているローカルクライアントにも反映され、エージェント一覧と通知が統合される。
マシンやワークスペースの切り替えはサイドバーで行う。

表示テーマとキーバインドはローカルクライアントの設定を使うため、worker 側の Frappé 設定だけでは
統合ウィンドウの色は切り替わらない。実行先はサイドバーのマシン名とタブ右端の hostname で確認する。
worktrunk、hunk、lazygit などのコマンドとプラグインは実行先にもインストールしておく。
UI でマシンを切り替えても、既存ペイン内の `herdr` CLI の接続先は変わらない。

同じサーバーに複数クライアントを接続して、別々のタブを表示できる。
操作用と監視用に分ける場合は別タブを開く。同じタブを表示すると、最後に操作したクライアントがサイズを決める。

### 設定反映と終了

設定を適用したら `prefix+shift+r` でリロードする。v0.9.0 の UI リロードは、
ローカルの表示設定と選択中サーバーの設定を両方読み直す。
`herdr status` でクライアントとサーバーの互換性を確認できる。
離席・ウィンドウを閉じる際は `prefix+q` でデタッチするとペイン内の処理が継続する。

子 worktree が開いている親ワークスペースを CLI で閉じるには明示的な `--group` が必要になった。
通常の `wt remove` 後の hook は該当する子だけを閉じるため、`--group` は付けない。

仕様の参照先: [v0.9.0 リリース](https://github.com/herdrdev/herdr/releases/tag/v0.9.0)、
[マシン接続](https://github.com/herdrdev/herdr/blob/v0.9.0/docs/next/website/src/content/docs/connecting-machines.mdx)、
[表示設定・リロード](https://github.com/herdrdev/herdr/blob/v0.9.0/docs/next/website/src/content/docs/configuration.mdx)。

## 独自ショートカット（config.toml の `[keys]` 上書きと `[[keys.command]]`）

`[[keys.command]]` には `description` を付けているので、`prefix+?` のヘルプでも同じラベルが出る。

### エージェント切り替え（`[keys]`）

herdr デフォルトでは未割り当てのアクションに独自キーを割り当てている。

| キー              | 動作                                                                       |
| ----------------- | -------------------------------------------------------------------------- |
| `prefix+a`        | 次のエージェントペインへ（サイドバー順 = priority 設定なら注意が必要な順） |
| `prefix+shift+a`  | 前のエージェントペインへ                                                   |
| `prefix+alt+1..9` | サイドバーの n 番目のエージェントへ直行                                    |

### ワークスペース / タブ / ペイン操作（`[keys]`）

herdr デフォルトでは未割り当てのアクションに独自キーを割り当てている。

| キー                | 動作                                               |
| ------------------- | -------------------------------------------------- |
| `prefix+shift+1..9` | ワークスペース番号で直接切り替え                   |
| `prefix+alt+p`      | アクティブなタブを前へ移動（先頭から末尾へ循環）   |
| `prefix+alt+n`      | アクティブなタブを後ろへ移動（末尾から先頭へ循環） |
| `prefix+space`      | 直前にフォーカスしていたペインと往復（全体）       |

### ペインリサイズ（`[keys]`）

リサイズモード（`prefix+r`）に入らず直接リサイズする。prefix 不要の直接バインドなので連打できる。

| キー                   | 動作                     |
| ---------------------- | ------------------------ |
| `ctrl+shift+alt+left`  | ペインを左方向へリサイズ |
| `ctrl+shift+alt+down`  | ペインを下方向へリサイズ |
| `ctrl+shift+alt+up`    | ペインを上方向へリサイズ |
| `ctrl+shift+alt+right` | ペインを右方向へリサイズ |

### scratch シェル

| キー       | 動作                                                                                                                    |
| ---------- | ----------------------------------------------------------------------------------------------------------------------- |
| `prefix+t` | scratch シェル（`zsh -l`）を popup で開く。タブレイアウトを変えないセッションモーダル、幅・高さ 80%。シェル終了で閉じる |

### worktrunk / ファイルビューア

| キー             | 動作                                                                       |
| ---------------- | -------------------------------------------------------------------------- |
| `prefix+shift+g` | worktrunk プラグインの worktree ピッカーを開く（`worktrunk.open`）         |
| `prefix+shift+c` | worktrunk プラグインでカレントリポジトリを開く（`worktrunk.open-current`） |
| `prefix+f`       | ファイルビューアを開く（`herdr-file-viewer.open-file-viewer`）             |

組み込みの worktree 作成（`new_worktree`）は無効化し、worktrunk ピッカーに置き換えている。

キーバインドではないが、`wt` で worktree へ switch すると post-switch hook（`scripts/worktree-open.sh`）が
その worktree を Herdr で開き、ワークスペースが素の状態ならレイアウトする:
タブ 1 = 「左: シェル / 右: ファイルビューア」の split、タブ 2 = lazygit、
タブ 3 = 「左: シェル / 右: yazi」の split（タブラベル "yazi"）。
hunk diff タブは自動では作らず、必要なときに `scripts/hunk-diff.sh` のキーバインドで開く。
hook はフォーカスを動かさない。ピッカー（`prefix+shift+g` / `prefix+shift+c`）から開いたときは
ピッカー側がフォーカスする。
`wt remove` 時は post-remove hook が pueue 経由で `scripts/worktree-close.sh` を遅延実行し、
その worktree のワークスペースを閉じる（pueued のセッションで走るため、close が
`wt remove` 自身のバックグラウンド掃除を巻き添えにしない）。

### lazygit

| キー             | 動作                                                                                                                                          |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `prefix+shift+l` | lazygit を split で開く（`herdr-lazygit.open`）                                                                                               |
| `prefix+alt+l`   | lazygit をタブで開く（`scripts/lazygit-tab.sh`）。タブラベルを "lazygit" に固定。lazygit タブにいる状態でもう一度押すと、直前にいたタブへ戻る |

`scripts/lazygit-tab.sh` と `scripts/hunk-diff.sh` はキーを押した時点のペイン、タブ、cwd を使うため、
コマンド起動前に別のペインへ移動しても対象は変わらない。

### hunk diff（`scripts/hunk-diff.sh`）

覚え方: `d` = worktree、`shift+s` = staged、`shift+b` = branch。`alt` を付けると split の代わりにタブで開く。同じキーをもう一度押すとトグルで閉じる。

| キー             | diff 対象                                                         | 開き方   |
| ---------------- | ----------------------------------------------------------------- | -------- |
| `prefix+d`       | worktree（未ステージ含む作業ツリー）                              | 右 split |
| `prefix+alt+d`   | worktree                                                          | タブ     |
| `prefix+shift+s` | staged                                                            | 右 split |
| `prefix+alt+s`   | staged                                                            | タブ     |
| `prefix+shift+b` | branch（PR base / デフォルトブランチとの merge-base からの diff） | 右 split |
| `prefix+alt+b`   | branch                                                            | タブ     |

## Herdr 本体のショートカット（デフォルトのまま）

### 全般

| キー             | 動作                     |
| ---------------- | ------------------------ |
| `prefix+?`       | ヘルプ                   |
| `prefix+s`       | 設定画面                 |
| `prefix+q`       | デタッチ                 |
| `prefix+shift+r` | 設定リロード             |
| `prefix+o`       | 通知元のペインへジャンプ |
| `prefix+g`       | goto（ナビゲートモード） |

### ワークスペース

| キー             | 動作                     |
| ---------------- | ------------------------ |
| `prefix+w`       | ワークスペースピッカー   |
| `prefix+shift+n` | 新規ワークスペース       |
| `prefix+shift+w` | ワークスペースのリネーム |
| `prefix+shift+d` | ワークスペースを閉じる   |

### タブ

| キー                    | 動作               |
| ----------------------- | ------------------ |
| `prefix+c`              | 新規タブ           |
| `prefix+shift+t`        | タブのリネーム     |
| `prefix+p` / `prefix+n` | 前 / 次のタブ      |
| `prefix+1..9`           | タブ番号で切り替え |
| `prefix+shift+x`        | タブを閉じる       |

### ペイン

| キー                              | 動作                                  |
| --------------------------------- | ------------------------------------- |
| `prefix+v`                        | 縦分割                                |
| `prefix+minus`                    | 横分割                                |
| `prefix+h/j/k/l`                  | ペインのフォーカス移動（左/下/上/右） |
| `prefix+tab` / `prefix+shift+tab` | 次 / 前のペインへ循環                 |
| `prefix+x`                        | ペインを閉じる                        |
| `prefix+z`                        | ズーム（フルスクリーン）              |
| `prefix+r`                        | リサイズモード                        |
| `prefix+shift+p`                  | ペインのリネーム                      |
| `prefix+e`                        | スクロールバックをエディタで開く      |
| `prefix+b`                        | サイドバー表示切り替え                |

### ナビゲートモード（`prefix+g` 中のローカルキー）

| キー          | 動作                                         |
| ------------- | -------------------------------------------- |
| `up` / `down` | ワークスペース上下移動                       |
| `h/j/k/l`     | ペイン移動（矢印キー左右も左右ペインに効く） |
