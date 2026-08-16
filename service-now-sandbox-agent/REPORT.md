# Live lab report: what we actually did on Viper

**Date:** 2026-08-16 (America/Toronto)
**Lab:** Sebastian’s Viper, kagent UI `http://172.16.10.135:30500/`
**This file is a record.** Visual start: [README.md](README.md).
The how-to is [JOURNEY.md](JOURNEY.md). Nothing here is invented;
every number and object name was confirmed live that afternoon.

---

## Why isolated sandboxes (not a plain Agent)

A normal kagent `Agent` is a Kubernetes Deployment: always on, same
isolation as any other pod. Fine for a cluster helper.

This `servicenow` agent talks to a ServiceNow instance. The model
gets a filesystem, memory, and a network for the whole chat.
Substrate puts that session in a **gVisor actor** (`SandboxAgent`)
on WorkerPool `kagent-default`: isolated sandbox (gVisor is the
wall; tools still call ServiceNow through the MCP pod; username /
password stay in Vault), idle chats snapshot (zstd) and free the
worker, no always-on pod per manager conversation, golden snapshot
you can resume.

**Tradeoff on this lab:** nested gVisor on dockerized k3s, and
snapshots are in-cluster rustfs today (`gs://` is a URI prefix only),
not GCS.

These are isolated sandboxes, not plain Agents. The kagent UI shows
a **Sandbox: Agent Substrate** badge. Classic `/api/a2a/<ns>/<name>`
404s because there is no `Agent` CR; the UI uses
`/api/a2a-sandboxes/kagent/servicenow`.

---

## Pins (unchanged)

| Pin | Value |
|-----|--------|
| kagent OSS | **0.10.0-rc2** |
| Agent Substrate | **0.0.9** |
| MCP image | `servicenow-mcp:dev` |

No `ignoreDifferences`. No secrets in git. Versions were not bumped.

---

## Vault (key names only)

| | |
|--|--|
| Path | `secret/platform/servicenow` |
| Keys | `host`, `username`, `password` |
| Host (name only) | `https://dev203166.service-now.com` |

No password, username **value**, or Vault token is in this file or
in git.

---

## Snapshots today

| | Live |
|--|--|
| atelet | S3 → in-cluster **rustfs** bucket `ate-snapshots` |
| SandboxAgent `servicenow` | **omits** `snapshotsConfig` |
| ActorTemplate | `servicenow-f5f2dec1f2a81a41` (gvisor, Ready) |
| ActorTemplate location | `gs://ate-snapshots/kagent/servicenow` (prefix only; bytes on rustfs) |
| Golden snapshot | `2026-08-16T15:45:24Z-HYSFX5R3DHWLRWYVP7YXOAF4SN` |

---

## Live status

| Object | Status |
|--------|--------|
| SandboxAgent `servicenow` | Ready=True, Accepted=True |
| RemoteMCPServer `servicenow-mcp` | Accepted (**8** tools), `STREAMABLE_HTTP` `http://servicenow-mcp.kagent:8084/mcp` |
| MCP pod | `servicenow-mcp-7c6c455c65-kvnrq` `1/1` Running, 0 restarts |
| ActorTemplate | Ready (gvisor) |
| Golden snapshot | ready on rustfs |

---

## kagent UI

Chat: `http://172.16.10.135:30500/agents/kagent/servicenow/chat`

Session: `01a00b42-ff06-737b-b8f7-0ea6683241bf`

The UI talks to `POST /api/a2a-sandboxes/kagent/servicenow`. Classic
`/api/a2a/kagent/servicenow` is **404** because there is no `Agent` CR.

Live Chromium screenshots of that SPA are not in `shots/` yet
(`ui-agents-grid.png`, `ui-chat-session.png`). They land when
captured. Do not invent them.

---

## Live A2A run (ServiceNow PDI)

Confirmed through that sandbox A2A path, not invented:

**Q1 — What IT tickets are open?**

25 active this page: **13 P1 / 4 P2 / 5 P3 / 3 P5**. Unassigned P1
**INC0007001** payroll server down (New).

**Q2 — Critical VPN and DNS**

| Incident | Short description | State | Assignee |
|----------|-------------------|-------|----------|
| INC0000015 | VPN | In Progress | Don Goodliffe |
| INC0000016 | rain leaking on main DNS server | In Progress | ITIL User |

---

## Shots

Only **live CLI** and **live UI** (Chromium of the kagent SPA).
See **[shots/](shots/)**.

| File | What it is |
|------|------------|
| `cli-live-status.png` | Live CLI, 2026-08-16. SandboxAgent Ready, RemoteMCPServer Accepted (8 tools), golden snapshot on rustfs. Real terminal capture — PNG not in this tree until the file is dropped in `shots/`. |
| `ui-agents-grid.png` | Live kagent UI — not attached this turn. |
| `ui-chat-session.png` | Live kagent UI — not attached this turn. |

No reconstructed reels. No invented frames.
