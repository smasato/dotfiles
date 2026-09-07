# 共通の作業原則と任意の実行手順

Cursor 由来の 46 スキルと付属リソースを `dot_agents/skills/` で管理する。
上流の手順を一律に適用せず、必要な原則を既存の作業フローへ取り込む。
互換性のため `poteto-mode` と `pstack-runtime` の名前と配置は維持する。

## 構成

- `poteto-mode` は明示起動の軽量な作業モード。範囲の確認、調査、実装、検証を基本とし、
  全原則の読み込み、設計コンペ、コメント監査、PR 作成を毎回要求しない。
- `pstack-runtime` は権限と検証の共通契約。委譲、履歴、監視、ローカル配置の詳細は
  必要な参照文書だけを読む。単純な文章処理や原則スキルからの一律参照は廃止した。
- `references/delegation.md` は書き込み先と操作の所有権を定義する。独立作業は並列化し、
  同じ作業ツリーの Git 操作や共有ブラウザは担当者を限定する。フックの副作用も考慮する。
- `references/history.md` と `references/monitoring.md` は対象を絞った履歴分析、停止、
  引き継ぎを扱う。履歴の要約と実行の証拠を区別し、再開時は現在の状態を確認する。
- Claude と Codex の参照文書は任意のアダプター。実行環境に公開された API とモデルを使い、
  未対応の環境でも共通契約に従って処理する。独立レビューができなければ、その制約を報告する。
- 既存の playbook と原則スキルは専門作業向けの参照として残す。共通契約の権限境界が適用され、
  呼び出すだけで編集・公開・マージが許可されるわけではない。個別手順の統合・削除は別途行う。

## ローカルの連携

Claude と pclaude は既存の skills シンボリックリンクから、Codex は共有ストアから読む。
Claude の `pstack-worker` はモデル継承用、`comment-sicko` は明示的なコメント監査用とする。
配置やコマンドの前提は `pstack-runtime/references/workspace.md` にまとめる。

- セッション終了後のモデル実行にはホストの対応が必要。バックグラウンドプロセスだけでは継続できない。
- Graphite 依存のスタック操作を既存の gh-stack に移した。
  `orch frontier set` は gh-stack の順序と GitHub の head を照合する。
  `--prs` は独立 PR の明示キューとして扱い、指定順で GitHub の状態を取得する。
- 実行時の自動パッケージインストールを廃止し、chezmoi の導入スクリプトで
  `bun install --frozen-lockfile` を実行する。
- 明示起動のスキルには Claude の frontmatter と Codex の `agents/openai.yaml` を併記する。

新規プロジェクト用の共有スキルは `.agents/skills/` に置き、Claude に必要な場合は
`.claude/skills/` からリンクする。既存プロジェクトの構成は保持する。

## 公開する情報の境界

このリポジトリには汎用的な作業ルールだけを記録する。非公開の履歴、セッション ID、
勤務先・顧客・製品の名称、内部 URL、業務固有の具体例や検証記録は含めない。
履歴を分析する場合も、根拠は公開文書へ転記せず、一時的な抽出物は分析後に削除する。

## 導入と更新

通常の `chezmoi apply` で管理ファイルと CLI 依存を配置する。
`run_onchange_after_skills.sh` は移植対象を上流から取得しない。
`tdd` / `teach` と名前が衝突する取得元も明示リストから除外した。

`pstack-runtime/scripts/detach-cli-lock.mjs` は、移植した名前と取得元パスが一致する
`cursor/plugins` エントリだけを skills CLI の lock から外す。
初回変更前の lock を `.skill-lock.json.before-pstack-port` に保存する。
スキル本体や他の取得元の登録は削除しない。skills CLI と同時には実行しない。

上流更新は自動追従しない。元の取得元とディレクトリハッシュは
`dot_agents/skills/pstack-runtime/references/upstream.json` に記録している。
これは配置されていたスナップショットの一覧であり、単一コミットの checkout ではない。
更新時は upstream と比較して必要な変更を移植し、下記のチェックを通す。
元のライセンスはこのディレクトリの `pstack-LICENSE` と `cursor-team-kit-LICENSE` に同梱する。

## 検証

```sh
python3 scripts/check-pstack.py
python3 scripts/test-pstack.py
```

空の一時ディレクトリを用意し、実際に配置されるファイル名・実行権限で検証できる。

```sh
python3 scripts/check-pstack.py --stage <empty-temp-dir>
bun install --frozen-lockfile --cwd <empty-temp-dir>/poteto-mode/scripts
cd <empty-temp-dir>/poteto-mode/scripts
bun test orch watch-pr
bun run typecheck
```

`check-pstack.py` は相対リンク、名前、既知の旧ホスト依存、一律 runtime 読み込みの定型文、
明示起動ポリシーを検査する。runtime 参照自体は必須ではなく、記載したリンクの整合性を検査する。
`test-pstack.py` はこの検証規則と配置・所有権移行を一時ディレクトリで確認する。
CLI テストは一時 Git リポジトリと分離した GitHub 応答で台帳・head 不一致・キュー・監視を検証する。
外部 PR の作成やマージは行わない。これらの検証は、全スキルの実タスクでの性能を保証するものではない。

GitHub への接続には gh 認証、スタックには gh-stack と対象リポジトリの対応が必要。
Bot UI は既存の外部 webhook サービスのクライアントであり、そのサービスの用意は別途必要。
