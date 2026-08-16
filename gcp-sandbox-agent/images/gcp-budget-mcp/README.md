# gcp-budget-mcp (GCP budget / capacity tools)

Small FastMCP **STREAMABLE_HTTP** server for the executive GCP agent.
Listens on **`:8084/mcp`** — same shape as live
`RemoteMCPServer/kagent-tool-server` and `aws-budget-mcp`.

Intended tags:

- local / node import: `gcp-budget-mcp:dev`
- published name: `ghcr.io/sebbycorp/gcp-budget-mcp:dev`

The Deployment uses `gcp-budget-mcp:dev` with `imagePullPolicy: IfNotPresent`.
Import the image **before** the pod can start.

```bash
# on Viper, from the demos repo root
docker build -t gcp-budget-mcp:dev gcp-sandbox-agent/images/gcp-budget-mcp
docker save gcp-budget-mcp:dev | docker exec -i k3s-viper ctr images import -
```

Env (no secrets in the image):

| Variable | Default | Source |
|----------|---------|--------|
| `GOOGLE_APPLICATION_CREDENTIALS` | `/var/secrets/gcp/credentials.json` | mounted file from Vault key `credentials_json` |
| `GOOGLE_CREDENTIALS` | (optional fallback) | same JSON as a string |
| `GCP_BILLING_ACCOUNT` | (required for billing tools) | Vault key `billing_account` |
| `GCP_PROJECT` | (required for compute tools) | Vault key `project` |
| `GCP_REGION` | `us-east1` | Vault key `region` |
| `MCP_HOST` / `MCP_PORT` | `0.0.0.0` / `8084` | listen address |

The process never prints the service-account JSON or `private_key`.
Health: `GET /health`. Self-check: `python server.py --self-check`.

Official google-cloud Python clients only. No generic `gcloud` CLI.
No project-delete / IAM-create tools.

Cloud Billing Accounts / Budgets / Catalog do **not** expose
month-to-date spend. `gcp_cost_month` and `gcp_cost_by_service` say
so instead of inventing `$0`.

Agent runbook: [../../JOURNEY.md](../../JOURNEY.md).
