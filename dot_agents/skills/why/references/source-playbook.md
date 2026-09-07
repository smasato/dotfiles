# Source playbooks

Read a category playbook only when its evidence can resolve an open question. These are query examples, not mandatory searches. Adapt MCP examples to authorized CLI, API, or local access. Follow the parent brief's scope, budget, and stop condition when a playbook suggests broader exploration.

| Category                     | Playbook                                               | Example MCP it documents                                        |
| ---------------------------- | ------------------------------------------------------ | --------------------------------------------------------------- |
| Source control history       | [`code-archaeology.md`](./sources/code-archaeology.md) | git, `gh`                                                       |
| Issue / ticket tracker       | [`linear.md`](./sources/linear.md)                     | Linear (adapt for Jira, GitHub Issues, Plane, Shortcut)         |
| Long-form documents          | [`notion.md`](./sources/notion.md)                     | Notion (adapt for Confluence, Google Docs, Coda)                |
| Real-time team chat          | [`slack.md`](./sources/slack.md)                       | Slack (adapt for Discord, Microsoft Teams, Mattermost)          |
| Infrastructure observability | [`datadog.md`](./sources/datadog.md)                   | Datadog (adapt for New Relic, Honeycomb, Grafana, Splunk)       |
| Error / exception tracking   | [`sentry.md`](./sources/sentry.md)                     | Sentry (adapt for Rollbar, Bugsnag, Airbrake)                   |
| Product analytics warehouse  | [`databricks.md`](./sources/databricks.md)             | Databricks SQL (adapt for Snowflake, BigQuery, ClickHouse, dbt) |

Cross-cutting:

- [`incident-postmortem.md`](./sources/incident-postmortem.md). Add this when evidence suggests an incident motivated the target code.
