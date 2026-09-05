# pstack の Claude Code / Codex 移植版

Cursor 由来の 47 スキルと付属リソースを `dot_agents/skills/` で管理する。
`pstack-runtime` が実行環境ごとの委譲・モデル役割・履歴・監視・権限を定義する。
Claude と pclaude は既存の skills シンボリックリンクから、Codex は共有ストアから読む。

## 移植内容

- 委譲は Claude の Agent、Codex の公開された collaboration API を使う。
- Claude の継承用 `pstack-worker` とコメント確認用 `comment-sicko` を追加した。
  Codex には共有プロンプトを渡す。モデルの役割名を API のモデル名として渡さない。
- Cursor 固有の履歴ディレクトリやメッセージ形式を、ホスト別の確認手順に変更した。
- Cursor のクラウド VM、永続ループ、ゴールを前提にせず、利用可能な機能と上限に従う。
  セッション終了後のモデル実行はホストの対応が必要。
- Graphite 依存のスタック操作を既存の gh-stack に移した。
  `orch frontier set` は gh-stack の順序と GitHub の head を照合する。
  `--prs` は独立 PR の明示キューとして扱い、指定順で GitHub の状態を取得する。
- 実行時の自動パッケージインストールを廃止し、chezmoi の導入スクリプトで
  `bun install --frozen-lockfile` を実行する。
- 明示起動のスキルには Claude の frontmatter と Codex の `agents/openai.yaml` を併記する。

新規プロジェクト用の共有スキルは `.agents/skills/` に置き、Claude に必要な場合は
`.claude/skills/` からリンクする。既存プロジェクトの構成は保持する。

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

`check-pstack.py` は相対リンク、名前、ホスト依存の残存、明示起動ポリシーを検査する。
CLI テストは一時 Git リポジトリと分離した GitHub 応答で台帳・head 不一致・キュー・監視を検証する。
外部 PR の作成やマージは行わない。これらの検証は、全スキルの実タスクでの性能を保証するものではない。

GitHub への接続には gh 認証、スタックには gh-stack と対象リポジトリの対応が必要。
Bot UI は既存の外部 webhook サービスのクライアントであり、そのサービスの用意は別途必要。
