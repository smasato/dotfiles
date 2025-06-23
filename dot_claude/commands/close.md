# Close Claude Code Session

I run this command when ending a session in Claude Code.

## Purpose

1. Review the work done in this session
2. Identify improvements or tasks to address before the next session
3. Document any issues with CLAUDE.md or unclear instructions

## Instructions

Please append your feedback to `./tmp/CLOSE.md` using the pre-generated timestamp heading.

First, You should execute the following command to create a timestamp heading:

```bash
echo "# $(date '+%Y-%m-%d %H:%M:%S')" >> ./tmp/CLOSE.md
echo "" >> ./tmp/CLOSE.md
```

Then, please add your session review under this heading with the following information:

- Summary of work completed
- Any unclear or ambiguous instructions encountered
- Missing information in CLAUDE.md or project documentation
- Environment setup issues
- Suggestions for workflow improvements
- Tasks to address in the next session

## Example Format

```markdown
# 2025-06-23 10:00:00

## セッションサマリー
- Homebrew bundle ファイルの更新スクリプトを実装
- chezmoi テンプレートの修正

## 改善提案

### ドキュメント関連
- CLAUDE.md にテスト実行コマンドの記載が不足していた
- README.md の環境構築手順が古い（mise の設定が反映されていない）

### 環境・設定
- brew.rb スクリプトの依存関係チェックが必要
- .chezmoidata.yaml のデフォルト値設定を追加すべき

### ワークフロー
- PR 作成前の自動チェックスクリプトがあると便利
- chezmoi apply の前に diff を確認する習慣をつける

## 次回への申し送り
- テストカバレッジの改善
- CI/CD パイプラインの設定
```


