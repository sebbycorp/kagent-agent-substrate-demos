# aws-budget-mcp (AWS budget / capacity tools)

Small FastMCP **STREAMABLE_HTTP** server for the executive AWS agent.
Listens on **`:8084/mcp`** — same shape as live
`RemoteMCPServer/kagent-tool-server` and `fortigate-mcp`.

Intended tags:

- local / node import: `aws-budget-mcp:dev`
- published name: `ghcr.io/sebbycorp/aws-budget-mcp:dev`

The Deployment uses `aws-budget-mcp:dev` with `imagePullPolicy: IfNotPresent`.
Import the image **before** the pod can start.

```bash
# on Viper, from the demos repo root
docker build -t aws-budget-mcp:dev aws-sandbox-agent/images/aws-budget-mcp
docker save aws-budget-mcp:dev | docker exec -i k3s-viper ctr images import -
```

Env (no secrets in the image):

| Variable | Default | Source |
|----------|---------|--------|
| `AWS_ACCESS_KEY_ID` | (required) | Vault `secret/platform/aws-budget` key `access_key_id` |
| `AWS_SECRET_ACCESS_KEY` | (required) | Vault key `secret_access_key` |
| `AWS_DEFAULT_REGION` | `us-east-2` | Vault key `region` (optional) |
| `AWS_COST_REGION` | `us-east-2` | CE filter; CE API itself is us-east-1 |
| `MCP_HOST` / `MCP_PORT` | `0.0.0.0` / `8084` | listen address |

The process never prints credentials. Health: `GET /health`.
Self-check: `python server.py --self-check`.

Agent runbook: [../../JOURNEY.md](../../JOURNEY.md).
