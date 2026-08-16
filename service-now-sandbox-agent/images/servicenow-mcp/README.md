# servicenow-mcp (ServiceNow ticket tools)

Small FastMCP **STREAMABLE_HTTP** server for the manager-facing
ServiceNow agent. Listens on **`:8084/mcp`** — same shape as live
`RemoteMCPServer/kagent-tool-server` and `aws-budget-mcp`.

Intended tags:

- local / node import: `servicenow-mcp:dev`
- published name: `ghcr.io/sebbycorp/servicenow-mcp:dev`

The Deployment uses `servicenow-mcp:dev` with `imagePullPolicy: IfNotPresent`.
Import the image **before** the pod can start.

```bash
# on Viper, from the demos repo root
docker build -t servicenow-mcp:dev service-now-sandbox-agent/images/servicenow-mcp
docker save servicenow-mcp:dev | docker exec -i k3s-viper ctr images import -
```

Env (no secrets in the image):

| Variable | Default | Source |
|----------|---------|--------|
| `SERVICENOW_HOST` | (required) | Vault `secret/platform/servicenow` key `host` |
| `SERVICENOW_USERNAME` | (required) | Vault key `username` |
| `SERVICENOW_PASSWORD` | (required) | Vault key `password` |
| `SERVICENOW_TLS_VERIFY` | `true` | Prefer normal TLS. Set `false` only if the lab cert path requires it. |
| `MCP_HOST` / `MCP_PORT` | `0.0.0.0` / `8084` | listen address |

Host in git (name only, not a secret): `https://dev203166.service-now.com`.
Username and password **never** go in git.

The process never prints the password. Health: `GET /health` (host
name only). Self-check: `python server.py --self-check`.

Tools talk to Table API `/api/now/table/incident` (and `sys_user`,
`sc_req_item`, stats) with HTTP basic auth. No generic shell.

Agent runbook: [../../JOURNEY.md](../../JOURNEY.md).
