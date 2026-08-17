# Live lab report: what we actually did on Viper

**Date:** 2026-08-17 (America/Toronto), ~10:48–10:56am ET
**Lab:** Sebastian’s Viper, kagent UI `http://172.16.10.135:30500/`
**This file is a record.** Visual start: [README.md](README.md).
Nothing here is invented; every number and object name was confirmed
live that morning.

GitOps for this agent still lives in
[sebbycorp/k8s-viper](https://github.com/sebbycorp/k8s-viper)
(`platform/kagent-ai/f5-bigip-*.yaml`, `images/f5-bigip-mcp/`,
`docs/f5-bigip-agent.md`). This folder is the live-run record.

---

## Why isolated sandboxes (not a plain Agent)

A normal kagent `Agent` is a Kubernetes Deployment: always on, same
isolation as any other pod. Fine for a cluster helper.

This `f5-bigip` agent talks to the lab BIG-IP. The model gets a
filesystem, memory, and a network for the whole chat. Substrate puts
that session in a **gVisor actor** (`SandboxAgent`) on WorkerPool
`kagent-default`: isolated sandbox (gVisor is the wall; tools still
call iControl REST through the MCP pod; the password stays in Vault),
idle chats snapshot (zstd) and free the worker, no always-on pod per
conversation, golden snapshot you can resume.

**Tradeoff on this lab:** nested gVisor on dockerized k3s, and
snapshots are in-cluster rustfs today (`gs://` is a URI prefix only),
not GCS.

These are isolated sandboxes, not plain Agents. The kagent UI shows
a **Sandbox: Agent Substrate** badge. Classic `/api/a2a/` 404s
because there is no `Agent` CR; the UI uses
`/api/a2a-sandboxes/kagent/f5-bigip`.

---

## Pins (unchanged)

| Pin | Value |
|-----|--------|
| kagent OSS | **0.10.0-rc2** (controller + UI images confirmed live) |
| Agent Substrate | **0.0.9** (worker `ateom-gvisor:v0.0.9`) |
| MCP image | `f5-bigip-mcp:dev` |

No `ignoreDifferences`. No secrets in git. Versions were not bumped.

---

## Vault (key names only)

| | |
|--|--|
| Path | `secret/platform/f5-bigip` |
| Keys | `host`, `username`, `password` |
| Host | `https://172.16.10.10` |
| ExternalSecret | `kagent/f5-bigip-mcp` → SecretSynced / Ready |

No F5 password or Vault token is in this file or in git.

---

## Live objects (2026-08-17 ~10:53am ET)

| Kind | Name | Status |
|------|------|--------|
| SandboxAgent | `kagent/f5-bigip` | Ready / Accepted |
| RemoteMCPServer | `kagent/f5-bigip-mcp` | Accepted, `STREAMABLE_HTTP` `:8084/mcp` |
| ExternalSecret | `kagent/f5-bigip-mcp` | SecretSynced / True |
| Pod | `f5-bigip-mcp-7f75b47b78-mdblb` | 1/1 Running, image `f5-bigip-mcp:dev` |
| ActorTemplate | `f5-bigip-3adfcbf7c448a873` | gVisor, phase Ready |
| Snapshot prefix | `gs://ate-snapshots/kagent/f5-bigip` | rustfs URI prefix |
| Golden snapshot | `gs://ate-snapshots/kagent/f5-bigip/2b9f5b6a-930d-471c-b679-22f31895f8c9/2026-08-17T14:32:42Z-23PD7HXZ5JL7OO7RNHUWZ5YOWS` | Ready |

Discovered MCP tools (live RemoteMCPServer status): `f5_system`,
`f5_list_vips`, `f5_vip_status`, `f5_list_pools`, `f5_pool_status`,
`f5_vip_brief`.

Session (LAN UI):
`http://172.16.10.135:30500/agents/kagent/f5-bigip/chat/01a01034-5a45-74b6-a29f-631e0de79170`

---

## Questions asked (live A2A)

1. What is this BIG-IP running, and which VIPs are up?
2. Which VIPs are down, and why (pool members)?

### Q1 (~12.6s)

Tools: `f5_system`, `f5_vip_brief`.

`f5_system` reached `https://172.16.10.10` (`ok: true`) but identity
fields were empty: product `null`, version `null`, build `null`.
Do not substitute an older TMOS peek.

`f5_vip_brief` returned **19** VIPs. Two were `available` / enabled:

| VIP | Destination | Pool | Availability | Enabled |
|-----|-------------|------|--------------|---------|
| `k8s_iceman_argocd_vs` | `/Common/172.16.20.60:443` | `/Common/k8s_iceman_argocd_pool` | `available` | `true` |
| `k8s_iceman_kagent_vs` | `/Common/172.16.20.62:8080` | `/Common/k8s_iceman_kagent_pool` | `available` | `true` |

The other 17 were `offline`.

### Q2 (~36.4s)

Tools: `f5_system`, `f5_vip_brief`, `f5_pool_status` ×16.

Same empty identity. All 17 offline VIPs were still enabled. Each
checked pool returned availability `"offline"` / enabled `"enabled"`
with reason **"The children pool member(s) are down"**. Members were
`state: down`, `session: monitor-enabled`.

| VIP | Destination | Pool | Down members |
|-----|-------------|------|--------------|
| `agentgateway-oss` | `/Common/172.16.20.30:8080` | `/Common/agentgetway-oss` | `172.16.10.144:30344`, `172.16.10.144:30513`, `172.16.10.148:30344`, `172.16.10.148:30513` |
| `argo.rooster.maniak.io` | `/Common/172.16.20.116:443` | `/Common/argo.rooster.maniak.io` | `172.16.10.130:31988`, `172.16.10.132:31988`, `172.16.10.133:31988`, `172.16.10.136:31988` |
| `dashboard-oss` | `/Common/172.16.20.33:80` | `/Common/dashboard-oss` | `172.16.10.144:32416`, `172.16.10.148:32416` |
| `goose.maniak.com` | `/Common/172.16.20.111:443` | `/Common/solo.maniak.com` | `172.16.10.161:30490`, `172.16.10.161:32635`, `172.16.10.162:30490`, `172.16.10.162:32635` |
| `k8s_iceman_vault_vs` | `/Common/172.16.20.61:8200` | `/Common/k8s_iceman_vault_pool` | `talos-cp:30820`, `talos-worker:30820` |
| `kagent-oss` | `/Common/172.16.20.36:80` | `/Common/kagent-oss` | `172.16.10.144:31438`, `172.16.10.144:32002`, `172.16.10.148:31438`, `172.16.10.148:32002` |
| `vs_argo_rooster_http` | `/Common/172.16.20.121:80` | `/Common/pool_argo_rooster_http` | `172.16.10.130:32178`, `172.16.10.132:32178`, `172.16.10.133:32178`, `172.16.10.136:32178` |
| `vs_argo_rooster_https` | `/Common/172.16.20.121:443` | `/Common/pool_argo_rooster_https` | `172.16.10.130:31988`, `172.16.10.132:31988`, `172.16.10.133:31988`, `172.16.10.136:31988` |
| `vs_github_gateway` | `/Common/172.16.20.125:8092` | `/Common/pool_github_gateway` | `172.16.10.130:31313`, `172.16.10.132:31313`, `172.16.10.133:31313`, `172.16.10.136:31313` |
| `vs_kagent_controller` | `/Common/172.16.20.131:8083` | `/Common/pool_kagent_controller` | `172.16.10.130:32083`, `172.16.10.132:32083`, `172.16.10.133:32083`, `172.16.10.136:32083` |
| `vs_mcp_gateway` | `/Common/172.16.20.123:8090` | `/Common/pool_mcp_gateway` | `172.16.10.130:30168`, `172.16.10.132:30168`, `172.16.10.133:30168`, `172.16.10.136:30168` |
| `vs_model_priority_gateway` | `/Common/172.16.20.124:8085` | `/Common/pool_model_priority_gateway` | `172.16.10.130:30689`, `172.16.10.132:30689`, `172.16.10.133:30689`, `172.16.10.136:30689` |
| `vs_solo_rooster` | `/Common/172.16.20.120:8080` | `/Common/pool_solo_rooster` | `172.16.10.130:31572`, `172.16.10.132:31572`, `172.16.10.133:31572`, `172.16.10.136:31572` |
| `vs_ui_rooster` | `/Common/172.16.20.130:80` | `/Common/pool_ui_rooster` | `172.16.10.130:31211`, `172.16.10.132:31211`, `172.16.10.133:31211`, `172.16.10.136:31211` |
| `vs_xai_gateway` | `/Common/172.16.20.122:8081` | `/Common/pool_xai_gateway` | `172.16.10.130:31990`, `172.16.10.132:31990`, `172.16.10.133:31990`, `172.16.10.136:31990` |
| `webui-https` | `/Common/172.16.20.31:443` | `/Common/webui-oss` | `172.16.10.144:30694`, `172.16.10.148:30694` |
| `webui-oss` | `/Common/172.16.20.31:80` | `/Common/webui-oss` | `172.16.10.144:30694`, `172.16.10.148:30694` |

Summary: **2** available, **17** offline, **19** total.

---

## Screenshots

Real Chromium `--headless=new --screenshot` of the tunneled kagent SPA
(`127.0.0.1:30500` → Viper `:30500`). Not reconstructed.

- [shots/ui-agents-grid.png](shots/ui-agents-grid.png) — Agents grid,
  includes the `kagent/f5-bigip` card
- [shots/ui-chat-session.png](shots/ui-chat-session.png) — both live
  answers in one session (the 17-row down table is below the fold)
- [shots/cli-live-status.txt](shots/cli-live-status.txt) — live
  kubectl dump (text only; no fake terminal PNG)

No reconstructed GIF.

---

## What we did not do

- No kagent / Substrate version bump
- No `snapshotsConfig` edits on the SandboxAgent
- No password in git
- No write tools (none exist on this MCP)
- No claim that https://viper.maniak.ai/agents/ is live (TLS name
  did not match when checked)
