# Herdr ショートカットチートシート

prefix キーは **`ctrl+f`** に変更済み（デフォルトは `ctrl+b`）。
以下の `prefix+X` は「`ctrl+f` を押してから `X`」の意味。

macOS では prefix モード中に ASCII 入力ソースへ自動切り替えする設定
（`switch_ascii_input_source_in_prefix = true`）を有効化しているため、
日本語 IME が ON でも prefix コマンドはそのまま効く。

## 独自ショートカット（config.toml の `[[keys.command]]`）

### worktrunk / ファイルビューア

| キー | 動作 |
| --- | --- |
| `prefix+shift+g` | worktrunk プラグインの worktree ピッカーを開く（`worktrunk.open`） |
| `prefix+shift+c` | worktrunk プラグインでカレントリポジトリを開く（`worktrunk.open-current`） |
| `prefix+f` | ファイルビューアを開く（`herdr-file-viewer.open-file-viewer`） |

組み込みの worktree 作成（`new_worktree`）は無効化し、worktrunk ピッカーに置き換えている。

### lazygit

| キー | 動作 |
| --- | --- |
| `prefix+shift+l` | lazygit を split で開く（`herdr-lazygit.open`） |
| `prefix+alt+l` | lazygit をタブで開く（`scripts/lazygit-tab.sh`）。タブラベルを "lazygit" に固定。lazygit タブにいる状態でもう一度押すと、直前にいたタブへ戻る |

### hunk diff（`scripts/hunk-diff.sh`）

覚え方: `d` = worktree、`shift+s` = staged、`shift+b` = branch。`alt` を付けると split の代わりにタブで開く。同じキーをもう一度押すとトグルで閉じる。

| キー | diff 対象 | 開き方 |
| --- | --- | --- |
| `prefix+d` | worktree（未ステージ含む作業ツリー） | 右 split |
| `prefix+alt+d` | worktree | タブ |
| `prefix+shift+s` | staged | 右 split |
| `prefix+alt+s` | staged | タブ |
| `prefix+shift+b` | branch（ブランチ全体の diff） | 右 split |
| `prefix+alt+b` | branch | タブ |

## Herdr 本体のショートカット（デフォルトのまま）

### 全般

| キー | 動作 |
| --- | --- |
| `prefix+?` | ヘルプ |
| `prefix+s` | 設定画面 |
| `prefix+q` | デタッチ |
| `prefix+shift+r` | 設定リロード |
| `prefix+o` | 通知元のペインへジャンプ |
| `prefix+g` | goto（ナビゲートモード） |

### ワークスペース

| キー | 動作 |
| --- | --- |
| `prefix+w` | ワークスペースピッカー |
| `prefix+shift+n` | 新規ワークスペース |
| `prefix+shift+w` | ワークスペースのリネーム |
| `prefix+shift+d` | ワークスペースを閉じる |

### タブ

| キー | 動作 |
| --- | --- |
| `prefix+c` | 新規タブ |
| `prefix+shift+t` | タブのリネーム |
| `prefix+p` / `prefix+n` | 前 / 次のタブ |
| `prefix+1..9` | タブ番号で切り替え |
| `prefix+shift+x` | タブを閉じる |

### ペイン

| キー | 動作 |
| --- | --- |
| `prefix+v` | 縦分割 |
| `prefix+minus` | 横分割 |
| `prefix+h/j/k/l` | ペインのフォーカス移動（左/下/上/右） |
| `prefix+tab` / `prefix+shift+tab` | 次 / 前のペインへ循環 |
| `prefix+x` | ペインを閉じる |
| `prefix+z` | ズーム（フルスクリーン） |
| `prefix+r` | リサイズモード |
| `prefix+shift+p` | ペインのリネーム |
| `prefix+e` | スクロールバックをエディタで開く |
| `prefix+b` | サイドバー表示切り替え |

### ナビゲートモード（`prefix+g` 中のローカルキー）

| キー | 動作 |
| --- | --- |
| `up` / `down` | ワークスペース上下移動 |
| `h/j/k/l` | ペイン移動（矢印キー左右も左右ペインに効く） |
