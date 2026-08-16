# Shots

Placeholders for the first live Viper apply of `servicenow`.
Visual landing: [../README.md](../README.md). Why these are isolated
sandboxes, not plain Agents: [../JOURNEY.md](../JOURNEY.md).

No reconstructed or fake UI captures in this scaffold. After apply,
drop real Chromium shots here:

| File (when captured) | What it should show |
|----------------------|---------------------|
| `ui-agents-grid.png` | kagent Agents list including **kagent/servicenow** with the Sandbox badge |
| `ui-chat-session.png` | Chat asking what tickets are open; real tool calls, not invented INCs |
| `cli-live-status.png` | `kubectl get sandboxagent servicenow` Ready |

Do not screenshot Vault `kv put` with a live password, and do not
commit `kubectl get secret -o yaml`.
