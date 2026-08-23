---
name: parallel-deps-update
description: >
  リポジトリの依存パッケージを複数並行で更新し、パッケージごとに個別の PR を作成する。
  /parallel-deps-update <pkg...> で起動するほか、「X と Y をアップデートして」
  「依存を更新して PR 作って」「パッケージ更新して」と依頼したとき、対象が 1 つでも必ず使う。
  wt worktree を切ってサブエージェントを並列配置し、バージョン解決から PR 作成まで完遂する。
---

# parallel-deps-update

依存パッケージ更新を「worktree 分離 + サブエージェント並列 + 個別 PR」で定型実行する。
引数はパッケージ名のスペース区切りリスト（例: `fallow chrome-devtools-mcp oxfmt`）。
`@aws-sdk/*` のようなワイルドカードの場合は、ワイルドカードを展開する。
`(ai @ai-sdk/*)` のような形で依頼された場合は、これらを1つのPRでまとめて更新する。

## Step 0: origin をフェッチする

**最初に必ずやる。** worktree の基点にはローカルブランチでなく、fetch 直後の
`origin/<デフォルトブランチ>` を使う（Step 4 の `--base`）。基点が古いと worktree
全部が古い基点で切られ、CI は通るのにローカル lockfile が実態とズレる。
ローカルのデフォルトブランチ自体は更新不要 — `git pull --ff-only` と違い、
ローカルが dirty / 分岐していても失敗しない。

```sh
git fetch origin
```

## Step 1: バージョン解決（メインセッションで実施）

サブエージェントに任せず、ここで対象バージョンを確定させる。エージェントごとに判断が
ぶれると報告と PR タイトルがずれるため。

1. 現行バージョンと pin スタイルを取得:
   ```sh
   git grep -n '"<pkg>"' -- package.json '**/package.json' pnpm-workspace.yaml
   ```
   pathspec の `**/` はルート直下の package.json に一致しないため、`package.json` を
   単体でも必ず指定する（`**/package.json` だけだとルート宣言の依存が 0 件に見える）。
   `^` 付きか exact pin かを記録する。**pin スタイルは必ず維持**。
   バージョンが `catalog:` の場合は pnpm catalog 管理。実バージョンは
   `pnpm-workspace.yaml` の catalog エントリにあり、**更新対象も pnpm-workspace.yaml**
   （利用側 package.json は `catalog:` のまま触らない）。
2. **宣言箇所は package.json だけとは限らない。** 現行バージョン文字列でリポジトリ全体を
   grep して全件洗う:
   ```sh
   grep -rn "<現行バージョン>" --exclude-dir=node_modules --exclude=pnpm-lock.yaml .
   ```
   `engines` / `packageManager`、バージョンマネージャ設定（mise.toml / mise.lock 等）、
   Dockerfile、CI 設定にも同じバージョンが宣言されていることがある。見積もりで始めず
   grep の全件で確定する。
3. `pnpm-workspace.yaml` に `minimumReleaseAge` があれば、カットオフを
   満たす最新バージョンと、**カットオフ直近の境界バージョン**を機械的に算出する
   （設定が無ければ最新安定版をそのまま対象にする）:
   ```sh
   curl -fsSL "https://registry.npmjs.org/<pkg>" | jq -r --argjson age <minimumReleaseAge値> '
     .time
     | (now - $age*60) as $cutoff
     | to_entries
     | map(select(.key | test("^[0-9]+\\.[0-9]+\\.[0-9]+$")))
     | map(.ts = (.value | sub("\\.[0-9]+Z$"; "Z") | fromdateiso8601))
     | sort_by(.key | split(".") | map(tonumber))
     | "target: \(map(select(.ts <= $cutoff)) | (last.key // "none"))",
       "boundary(<12h): \(map(select(.ts > $cutoff and .ts < ($cutoff + 43200))) | if length == 0 then "none" else map(.key) | join(", ") end)",
       "excluded: \(map(select(.ts > $cutoff)) | if length == 0 then "none" else map(.key) | join(", ") end)"'
   ```
   スコープ付きパッケージ（`@scope/pkg`）は URL の `/` を `%2F` にエンコードする
   （例: `https://registry.npmjs.org/@aws-sdk%2Fclient-s3`）。
   多頻度リリースでも「時系列の末尾 N 件」に頼らずこれで確定できる。
   除外バージョンは PR の Notes に理由として書く。
4. `boundary(<12h)` に出たバージョンは、エージェントの作業中にカットオフを満たして
   pnpm が解決してしまう。テンプレートの境界バージョン注意（Step 5 手順 4）を必ず埋める。
5. **`pnpm-workspace.yaml` の `minimumReleaseAgeExclude` を確認する。** 対象パッケージが
   登録されていればカットオフは適用されない。
   - exclude は本来セキュリティ修正を待たせないための一時措置。
     **非セキュリティの更新に流用するかは確認する**
   - エントリの `Drop when:` 条件を満たしているものがあれば、削除 PR を別途提案する
   - exclude を維持したままバージョンを上げるなら、
     **根拠コメントと Drop when を新しいバージョンの実態に書き換える**。
     旧バージョンのセキュリティ修正を根拠にした文面が残ると次回の判断を誤らせる
6. **override キーの追従が要るパッケージを洗い出す。** `pnpm-workspace.yaml` の
   `overrides` に `<pkg>@<version>>...` 形式のキーがあれば、その pkg の更新と同じ PR で
   キーを書き換える。キーの LHS が古いバージョンのままだと override は**静かに無効化**
   され、脆弱な transitive 依存が復活する。更新後に `grep <脆弱版> pnpm-lock.yaml` で
   実パッケージとして復活していないことを検証させる
7. 現行と対象が同じなら、そのパッケージは「更新不要」と報告してスキップする。
8. **対象が GitHub Actions の場合**は npm registry でなく GitHub API で解決する。
   リポジトリに Actions 更新用のスキルがあればそれに従う。
   `gh api repos/<owner>/<repo>/git/ref/tags/<tag>` でタグ SHA を解決し、
   現行 pin は**旧 SHA でリポジトリ全体を grep** して洗う（`.github/` だけでなく
   composite action にも pin があり得る）。

## Step 2: 過去 PR の収集

パッケージごとにスタイル参照用の過去 PR を探す:

```sh
gh pr list --state merged --search "<pkg> in:title" --limit 5 --json number,title,author
```

bot 製 PR（Renovate / Dependabot 等。`author` が `app/...`）はスタイル参照に不適なので
除外し、手動の `chore(deps):` PR を優先する。
`in:title` 検索が別パッケージを拾うことがある（`next` で `next-intl` の PR が出る等）。
その場合は `gh pr list --state merged --limit 40 --json number,title,author --jq '.[] | select(.title | test("<pkg> を"))'`
で絞る。同一パッケージの手動 PR が見つからない場合は直近の手動 `chore(deps):` PR を
代わりに渡す。

## Step 3: 波分け

**同時オープンは 3〜4 本まで。** 全 PR が `pnpm-lock.yaml` 等を触るため、それ以上並べると
マージのたびに残り全部が衝突して rebase 連鎖になる。5 本以上あるときは波に分け、
**前の波が staging に入りきってから次の波の worktree を切る**（次の波が最新 lockfile
ベースになり、衝突が波の中に閉じる）。

波の中では衝突面積が小さいものを先にマージする順で並べる。
同じファイルの隣接行を触る組は片方に必ず衝突が出る前提で最後に置く。

## Step 4: worktree 作成

`wt-worktree-ops` スキルに従い、**逐次**（git lock 競合回避）で作成する:

```sh
wt switch --create chore/update-<pkg> --base "$(git symbolic-ref --short refs/remotes/origin/HEAD)"
```

`--base` は remote-tracking ref をそのまま受け、その tip からブランチを切る（wt v0.74.0 で検証済み）。
`origin/HEAD` はデフォルトブランチ名を動的に解決する。
`fatal: ... not a symbolic ref` で落ちたら `git remote set-head origin -a` で作る
（`git rev-parse --abbrev-ref` は未設定時にリテラル `origin/HEAD` を返して静かに壊れるため使わない）。

worktree は `<repo>.chore-update-<pkg>` に作られる。post-start hook が
copy / install を走らせるため、作成コマンドの完了を待ってから次へ進む。
Step 0 の `git fetch origin` を飛ばしていないか、ここで再確認する。
時間が経っている場合や次の波に移る場合は fetch を再実行してから切る。

## Step 5: サブエージェント並列投入

パッケージごとに `general-purpose-sonnet` を 1 体、**同一メッセージで全体を一括起動**する。
プロンプトは次のテンプレートを使い、`{...}` を Step 1–4 の結果で埋める:

```text
作業ディレクトリ: {worktree絶対パス}（ブランチ {branch}、作成済み。すべての作業を
このディレクトリ内で行う。メインリポジトリ {repo絶対パス} は触らない）

タスク: 依存パッケージ {pkg} を {現行} から {対象バージョン} へ更新し、PR を作成する。
ユーザー確認は不要、PR 作成まで完遂する。

手順:
0. 長時間コマンド（pnpm install 等、2 分以上見込み）は pueue に投入し、
   `pueue wait <id>` で**同期待ち**する。
   「install 完了待ちです」と報告して停止するのは**失敗扱い**。PR 作成まで
   一気に完遂する
1. Skill ツールで `dependency-update` スキルを読み、ルールに従う
2. worktree の post-start hook (pnpm install) 完了を確認（node_modules 存在確認）。
   無ければ `pnpm install` を実行
3. {package.json / pnpm-workspace.yaml の catalog} の {pkg} を {対象バージョン} へ更新
   （pin スタイルは {^/exact/catalog} を維持）し、`pnpm install` で lockfile 更新。
   {Step 1 手順 2 の grep で見つかった他の宣言箇所も同じ PR で揃える}
4. lockfile の解決バージョンが {対象バージョン} と一致するか必ず確認。
   {境界バージョン} が作業中に minimumReleaseAge を満たして解決された場合は
   `pnpm update {pkg}@{対象バージョン}` で固定し直す（境界バージョンが無い場合は
   一致確認のみ）
5. {override キー追従が要る場合の手順。キーの LHS を新バージョンに書き換え、
   install 後に脆弱版が lockfile に実パッケージとして残っていないことを grep で検証}
6. changelog / リリースノートで {現行}→{対象} の破壊的変更を確認。
   monorepo 配下のパッケージは npm wrapper の CHANGELOG でなく実体側を見る
   （例: oxfmt は oxc-project/oxc の apps/oxfmt/CHANGELOG.md。npm/oxfmt 側は
   ほぼ空で、それだけ見ると「変更なし」と誤認する）
7. 動作確認: {パッケージ固有の検証コマンド}。formatter / linter の更新なら
   リポジトリ全体へ実行し、出た差分は同じコミットに含め、件数を PR 本文に明記する
8. 過去のマージ済み PR {参照PR番号} を `gh pr view` で参照し、タイトル・本文の
   スタイルを踏襲する
9. Skill ツールで `pr-description` と `pr-metadata` スキルを読み、従う
10. Skill ツールで `pre-push-check` スキルを読み、push 前のローカル検証を実施。
    既知の落とし穴: {リポジトリ既知の pre-push / build 落とし穴（必須環境変数など）。
    無ければ「特になし」}
11. PR 本文は **worktree 内の一時ファイル**（例: {worktree絶対パス}/PULL_REQUEST.md）に
    書く。scratchpad はセッション内の全エージェントで共有されるため、そこに置くと
    並列エージェント間で上書き競合し別パッケージの本文で PR が作られる。
    PULL_REQUEST.md はコミットに含めず、PR 作成後に削除する
12. コミット（`chore(deps): {pkg} を {対象バージョン} に更新`。--no-verify は絶対に
    使わない。ローカルの git hook は hk）、push、`gh pr create` で base={デフォルトブランチ} の
    PR を作成

最後に PR URL、変更内容の要約、changelog 上の注意点を報告して。
```

パッケージ固有の検証コマンドの例:

- fallow — `pnpm exec fallow audit`
- oxfmt — `pnpm exec oxfmt --check .`（差分が出たら全体再フォーマットして同コミットへ）
- oxlint — 更新前後で全体 lint を実行して warning / error 件数を比較。加えて
  **type-aware ルールが実際に動くことを実検出で確認させる**（違反する一時ファイルを
  作って検出されるか見る）。
- renovate — `pnpm exec renovate-config-validator --strict`
- pnpm 本体 — `pnpm --version` と `mise exec -- pnpm --version` の一致、バイナリ実体の存在確認
- 上記以外 — そのパッケージを使う mise task 等があれば実行する

エージェントが手順 0 に反して「install 完了待ちです」で停止して完了通知を返すことが
ある。その場合は SendMessage で「停止せず PR 作成まで完遂して」と送って再開させる。

エージェントが pre-push / build の新しい落とし穴（必須環境変数の不足等）を報告したら、
メインセッションが SendMessage で作業中の他エージェントへ回避方法を共有し、
以降の波のプロンプト（手順 10 の既知の落とし穴枠）にも先渡しする。
各エージェントに独立再発見させると時間の二重払いになる。

## Step 6: CI 監視とマージ

ユーザーが自動マージまで許可している場合に実施する。許可が無ければ PR URL の報告までで止める。

1. 各 PR の CI をバックグラウンドで監視する:
   ```sh
   gh pr checks <n> --watch --fail-fast --interval 30
   ```
   `run_in_background: true` で投げれば完了時に通知が来る。複数 PR を同時に監視できる。
2. 状態の確認は集計して読む:
   ```sh
   gh pr checks <n> --json name,state,bucket --jq '[.[] | select(.bucket != "skipping")] | group_by(.state) | map("\(.[0].state): \(length)") | join(", ")'
   gh pr view <n> --json mergeable,mergeStateStatus --jq '"\(.mergeable) \(.mergeStateStatus)"'
   ```
   `mergeStateStatus: BLOCKED` はレビュー未承認によるもので衝突ではない。判断は
   `mergeable` の `MERGEABLE` / `CONFLICTING` で行う。マージ直後は GitHub が再計算中で
   `UNKNOWN` を返すので、その時は少し待って再取得する。
3. `MERGEABLE` なら自動マージを有効にする（全チェック成功後に GitHub が自動でマージする）。
   branch protection のレビュー必須設定などは考慮せず、自動マージを有効にする。
   ```sh
   gh pr merge <n> --squash --auto
   ```

### 衝突が出たとき

`CONFLICTING` になった PR は **rebase でなく merge + lockfile 再生成**で解決する。
衝突マーカーを手で直さない:

```sh
git fetch origin {デフォルトブランチ} && git merge origin/{デフォルトブランチ}
# package.json 等の宣言ファイルは手で解決（両方の変更を残す）
git checkout origin/{デフォルトブランチ} -- pnpm-lock.yaml && pnpm install
```

再生成後に **両方のパッケージが期待バージョンで入っていること**を grep で検証してから
コミットする（片方が巻き戻っていたら失敗）。yaml のコメントブロックが衝突した場合は、
残す側の文面が実態と合っているかも確認する。

## Step 7: 結果収集と後片付け

エージェント完了通知が届くたびに、PR URL と注意点をユーザーへ即時報告する
（全員待ちにしない）。全員完了したら一覧でまとめる。

- 報告に含める: PR URL、バージョン範囲、破壊的変更の有無、minimumReleaseAge で
  除外したバージョン
- worktree はマージまで残す。マージ後は `wt remove chore/update-<pkg> --force`

## Step 8: pnpm dedupe（複数本を連続更新したとき）

3 本以上を続けて更新した後は、同一パッケージの複数バージョンが lockfile に併存しうる。
最後に `pnpm dedupe` の PR を 1 本足す。pnpm 本体も更新する場合は、
**pnpm 更新 PR とは分ける**（バージョン差由来の lockfile 差分と dedupe 由来の差分が
混ざるとレビュー不能になる）。dedupe エージェントには次を検証させる:

- 解消された重複の一覧（パッケージ名と統合先バージョン）、lockfile の行数差分
- **ダウングレードが起きていないこと**（`trustPolicy: no-downgrade` の意図に反する
  resolution 低下が無いか `git diff` で確認）
- overrides が引き続き効いていること（脆弱版が実パッケージとして復活していないか grep）
- `pnpm install --frozen-lockfile` / lint / typecheck / build / test がすべて通ること
- 差分がまったく無ければ PR を作らず「dedupe 済みで差分なし」と報告して終了

## 落とし穴（テンプレート外の判断が要るとき）

- pnpm install が新バージョンを解決しない — `minimumReleaseAge` が resolution を
  ブロックしている。バージョン選定に戻る
- deprecated 件数は `grep -c "deprecated:" pnpm-lock.yaml` で更新前後を比較し、
  変化があれば PR 本文へ
- PR 本文の日本語は textlint MCP（`lintFile`、引数は `filePaths` 配列）で
  エラー 0 を確認してから `gh pr create`
- pinact の `--verify-comment` は GitHub API を使うため token 無しだと rate limit の
  403 で失敗する。`GITHUB_TOKEN=${GITHUB_TOKEN:-$(gh auth token)} pinact run --check
--verify-comment` の形で実行する（hk hook と同じフォールバック）
