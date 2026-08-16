# Shots

Live Viper captures for `servicenow` (2026-08-16, America/Toronto).
Visual landing: [../README.md](../README.md). What we actually did:
[../REPORT.md](../REPORT.md). Why these are isolated sandboxes, not
plain Agents: [../JOURNEY.md](../JOURNEY.md).

**Only live UI and live CLI.** Captions must say live UI / live CLI.
No reconstructed reels. No invented frames. No
`servicenow-kagent-demo.gif`.

| File | Status | What it is |
|------|--------|------------|
| `cli-live-status.png` | Attached this turn; **file did not persist** in the agent workspace. Drop the real PNG here. Do not generate a replacement. | Live CLI. `kubectl -n kagent get sandboxagent,remotemcpserver,pod` plus ActorTemplate `servicenow-f5f2dec1f2a81a41`. Ready=True, RemoteMCPServer Accepted, `STREAMABLE_HTTP` `http://servicenow-mcp.kagent:8084/mcp`, pod `1/1` Running, golden snapshot `gs://ate-snapshots/kagent/servicenow` on rustfs, 8 MCP tools. Footer: `Viper · 172.16.10.135 · no secrets on screen`. |
| `ui-agents-grid.png` | Waiting on a follow-up attach | Live kagent UI (Chromium of the SPA). Agents list including **kagent/servicenow** with the Sandbox badge. |
| `ui-chat-session.png` | Waiting on a follow-up attach | Live kagent UI (Chromium of the SPA). Chat session `01a00b42-ff06-737b-b8f7-0ea6683241bf` — open tickets + critical VPN/DNS. |

Do not screenshot Vault `kv put` with a live password, and do not
commit `kubectl get secret -o yaml`.
