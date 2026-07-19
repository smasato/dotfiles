---
name: chezmoi-commit
description: chezmoi ソースの変更を検証してコミットする定型フロー。管理ファイルを編集した後に「コミットして」「/chezmoi-commit」と言われたら使う。chezmoi diff で差分を確認し、chezmoi apply で適用、drift がないことを確認してから conventional commit でコミットする。
---

# chezmoi-commit

chezmoi ソースの変更を検証してコミットするまでの手順。

## 手順

1. `chezmoi diff` を実行し、これから適用される差分を確認する。意図しない差分（他タスクの変更混入・テンプレート展開ミス）があれば停止して報告する。
2. `chezmoi apply` で変更をホームディレクトリへ適用する。
3. 再度 `chezmoi diff` を実行し、出力が空（drift なし）であることを確認する。差分が残る場合は原因（modify テンプレート・再ソートなど）を調査してから進む。
4. `git status` と `git diff` で変更ファイルを確認し、今回のタスクに関係するファイルのみ `git add` する。
5. 変更内容を要約した conventional commit メッセージ（`feat:` / `fix:` / `docs:` / `refactor:`）でコミットする。

## 注意

- ソース（このリポジトリ）だけを編集する。ターゲット側（`~/` 配下）を直接編集しない。
- `.chezmoidata/packages.yaml` を変更した場合はコミット前に `ruby scripts/yaml_sort.rb .chezmoidata/packages.yaml` でソートする。
- pre-commit フックは hk が実行する。`--no-verify` は使わない。
