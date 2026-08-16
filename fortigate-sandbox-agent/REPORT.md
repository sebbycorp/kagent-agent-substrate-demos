# Live lab report: what we actually did on Viper

**Date:** 2026-08-16 (America/Toronto), ~6:32–6:33pm ET
**Lab:** Sebastian’s Viper, kagent UI `http://172.16.10.135:30500/`
**This file is a record.** Visual start: [README.md](README.md).
Nothing here is invented; every number and object name was confirmed
live that evening.

GitOps for this agent still lives in
[sebbycorp/k8s-viper](https://github.com/sebbycorp/k8s-viper)
(`platform/kagent-ai/fortigate-*.yaml`, `images/fortigate-mcp/`,
`docs/fortigate-agent.md`). This folder is the live-run record.

---

## Why isolated sandboxes (not a plain Agent)

A normal kagent `Agent` is a Kubernetes Deployment: always on, same
isolation as any other pod. Fine for a cluster helper.

This `fortigate` agent talks to a home FortiGate. The model gets a
filesystem, memory, and a network for the whole chat. Substrate puts
that session in a **gVisor actor** (`SandboxAgent`) on WorkerPool
`kagent-default`: isolated sandbox (gVisor is the wall; tools still
call FortiOS through the MCP pod; the REST token stays in Vault),
idle chats snapshot (zstd) and free the worker, no always-on pod per
conversation, golden snapshot you can resume.

**Tradeoff on this lab:** nested gVisor on dockerized k3s, and
snapshots are in-cluster rustfs today (`gs://` is a URI prefix only),
not GCS.

These are isolated sandboxes, not plain Agents. The kagent UI shows
a **Sandbox: Agent Substrate** badge. Classic `/api/a2a/<ns>/<name>`
404s because there is no `Agent` CR; the UI uses
`/api/a2a-sandboxes/kagent/fortigate`.

---

## Pins (unchanged)

| Pin | Value |
|-----|--------|
| kagent OSS | **0.10.0-rc2** |
| Agent Substrate | **0.0.9** |
| MCP image | `fortigate-mcp:dev` |

No `ignoreDifferences`. No secrets in git. Versions were not bumped.

---

## Vault (key names only)

| | |
|--|--|
| Path | `secret/platform/fortigate` |
| Box | FortiGate 80F · `fw-maniak-hq` · `172.16.10.1` |
| FortiOS | v7.4.11 build 2878 · VDOM `root` |

No REST token or Vault token is in this file or in git.

---

## Live objects (2026-08-16 ~6:32pm ET)

| Kind | Name | Status |
|------|------|--------|
| SandboxAgent | `kagent/fortigate` | Ready / Accepted |
| RemoteMCPServer | `kagent/fortigate-mcp` | Accepted, `STREAMABLE_HTTP` `:8084/mcp` |
| Pod | `fortigate-mcp-745d4c9ff5-bxjvc` | 1/1 Running |
| ActorTemplate | `fortigate-b8bc65944f9bc4df` | gVisor, phase Ready |
| Snapshot prefix | `gs://ate-snapshots/kagent/fortigate` | rustfs URI prefix |
| Golden snapshot | `gs://ate-snapshots/kagent/fortigate/2bcc7a8b-48e0-4b20-aa0d-2bfe0ff5fb1e/2026-08-16T02:45:18Z-R7ZXMSV6CEC2D4NVN4XEX5UDO3` | Ready |

Session (LAN UI):
`http://172.16.10.135:30500/agents/kagent/fortigate/chat/01a00cb4-6f1c-79de-8821-5d41a0b66c61`

---

## Questions asked (live A2A)

1. What is fw-maniak-hq running, and which WAN is up?
2. What's the YouTube policy?

### Q1 (~6.6s)

Tools: `fg_system_status`, `fg_list_interfaces`, `fg_interface_stats`.

fw-maniak-hq is FortiGate **80F** / FortiOS **v7.4.11** build 2878
(serial `FGT80FTK22061709`, VDOM `root`). **wan1 down** (DHCP
`0.0.0.0`). **wan2 up** (DHCP `24.141.221.254/20`).

### Q2 (~12.0s)

Tools: `fg_list_policies`, `fg_get_policy` ×2, `fg_policy_stats`.

Two enabled YouTube-related policies. No separate YouTube block
policy in the compact list returned.

| ID | Name | Source | Schedule | Hits | Active |
|----|------|--------|----------|-----:|-------:|
| 8 | `Allow-YouTube-Whitelist` | `Grp-YouTube-Allowed` | always | 3,007,844 | 154 |
| 7 | `Allow-YouTube-MasterBR-Night` | `YT-AppleTV-Master-122` | `Allow-YT-MasterBR-8pm-2am` | 18,902 | 0 |

Both: from `corp` → `BELL_35` / `wan2`, action accept, NAT on.

---

## Screenshots

Real Chromium `--screenshot` of the tunneled kagent SPA
(`127.0.0.1:30500` → Viper `:30500`). Not reconstructed.

- [shots/ui-agents-grid.png](shots/ui-agents-grid.png) — Agents grid,
  includes the `kagent/fortigate` card
- [shots/ui-chat-session.png](shots/ui-chat-session.png) — both live
  answers in one session (policy 7 is partly below the fold)
- [shots/cli-live-status.txt](shots/cli-live-status.txt) — live
  kubectl dump (text only; no fake terminal PNG)

No reconstructed GIF.

---

## What we did not do

- No kagent / Substrate version bump
- No `snapshotsConfig` on the SandboxAgent
- No token in git
- No write tools (`fg_create_policy`, disable, etc.)
