# OMP の MCP 設定

`~/.omp/agent/mcp.json` は chezmoi のテンプレートで管理する（`dot_omp/private_agent/mcp.json.tmpl`）。
ファイルにはサーバー定義だけを書き、秘密値は書かない。認証情報は次の 2 か所に置く。

| サーバー  | 配置先     | 認証方式          | 秘密値の置き場所                                  |
| --------- | ---------- | ----------------- | ------------------------------------------------- |
| `devin`   | 全環境     | API キー (Bearer) | macOS Keychain（`devin-mcp`、`devin-mcp-org-id`） |
| `datadog` | 仕事用のみ | OAuth             | omp の認証ストア（`~/.omp/agent/agent.db`）       |
| `linear`  | 全環境     | OAuth             | omp の認証ストア（`~/.omp/agent/agent.db`）       |

`datadog` は `{{ if .work }}` で囲んであり、`.work = true` の環境にだけ配置される。

`mcp.json` を編集するときは chezmoi のソースを直接編集し、`chezmoi apply` で反映する。
`/mcp add`・`/mcp enable`・`/mcp disable`・`/mcp reauth` は `~/.omp/agent/mcp.json` を書き換えることがある。
実行した後は `chezmoi diff` で差分を確かめ、残す変更は手でテンプレートへ書き写す。
テンプレートなので `chezmoi re-add` ではソースへ戻らない。

## Devin の API キーと Org ID

`devin` のヘッダーは `!` で始まるコマンドとして書いてあり、omp が接続時に実行して値を得る。

```json
"Authorization": "!k=$(security find-generic-password -s devin-mcp -w) && printf 'Bearer %s' \"$k\"",
"X-Org-Id": "!security find-generic-password -s devin-mcp-org-id -w 2>/dev/null"
```

コマンドが失敗するか空文字を返すと、そのヘッダーは送られない（30 秒後に再試行される）。
新しい Mac で設定するとき、またはキーを作り直したときは Keychain に登録し直す。
`-w` を末尾に置くと値を対話入力できるので、シェル履歴に秘密値が残らない。
`-U` は既存のエントリを上書きする。

```sh
security add-generic-password -U -a "$USER" -s devin-mcp -w
security add-generic-password -U -a "$USER" -s devin-mcp-org-id -w
```

API キーには `Bearer ` を付けずに保存する。ヘッダーを組み立てるときにコマンド側で付ける。
登録できたかは次のコマンドで確かめる（値が表示されるので画面共有中は実行しない）。

```sh
security find-generic-password -s devin-mcp -w >/dev/null && echo ok
```

omp は成功したコマンドの結果をプロセス内でキャッシュする。
起動中の omp に新しいキーを使わせるには、`/mcp reconnect devin` を実行するか omp を再起動する。

## Datadog と Linear の OAuth

`datadog` と `linear` は `mcp.json` に URL だけを書いている。
OAuth の認証情報は、プロファイルとサーバー URL ごとに omp の認証ストアへ保存される
（`mcp_oauth:profile:<profile>:<url>`）。`mcp.json` には書き込まれない。

新しい Mac で設定するとき、またはトークンが失効したときは omp の中で再認証する。

```text
/mcp reauth datadog
/mcp reauth linear
```

ブラウザで認可すると認証ストアに保存される。
`/mcp reauth` は URL だけを書いたサーバー定義を書き換えないため、chezmoi との差分は出ない。

## プロファイル

omp のプロファイルは、ほかのプロファイルの `mcp.json` を読まない。
`experimental` と `security` で MCP を使うには、`~/.omp/profiles/<name>/agent/mcp.json` を別に用意し、
そのプロファイルで起動して OAuth を認可し直す（`omp --profile <name>` から `/mcp reauth <server>`）。
Keychain の値はプロファイルをまたいで共有される。
