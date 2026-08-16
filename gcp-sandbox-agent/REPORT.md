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

This `gcp-budget` agent talks to the GCP bill and Compute Engine
inventory. The model gets a filesystem, memory, and a network for the
whole chat. Substrate puts that session in a **gVisor actor**
(`SandboxAgent`) on WorkerPool `kagent-default`: isolated sandbox
(gVisor is the wall; tools still call GCP through the MCP pod; the
service-account JSON stays in Vault), idle chats snapshot (zstd) and
free the worker, no always-on pod per executive conversation, golden
snapshot you can resume.

**Tradeoff on this lab:** nested gVisor on dockerized k3s, and
snapshots are in-cluster rustfs today (`gs://` is a URI prefix only),
not GCS.

These are isolated sandboxes, not plain Agents. The kagent UI shows
a **Sandbox: Agent Substrate** badge. Classic `/api/a2a/<ns>/<name>`
404s because there is no `Agent` CR; the UI uses
`/api/a2a-sandboxes/kagent/gcp-budget`.

---

## Pins (unchanged)

| Pin | Value |
|-----|--------|
| kagent OSS | **0.10.0-rc2** |
| Agent Substrate | **0.0.9** |
| MCP image | `gcp-budget-mcp:dev` |

No `ignoreDifferences`. No secrets in git. Versions were not bumped.

---

## Vault (key names only)

| | |
|--|--|
| Path | `secret/platform/gcp-budget` |
| Keys | `credentials_json`, `billing_account`, `project`, `region` |
| Project | `viper-kagent` |
| Region | `us-east1` |
| Billing account (id only) | `011C38-867461-BE95B1` |
| SA (email only) | `gcp-budget-agent@viper-kagent.iam.gserviceaccount.com` |

No service-account JSON, private key, or Vault token is in this file
or in git.

---

## Live objects (2026-08-16 ~1:59–2:05pm ET)

| Kind | Name | Status |
|------|------|--------|
| SandboxAgent | `kagent/gcp-budget` | Ready / Accepted |
| RemoteMCPServer | `kagent/gcp-budget-mcp` | Accepted, `STREAMABLE_HTTP` `:8084/mcp` |
| Pod | `gcp-budget-mcp-5664dfb8f7-pwlwv` | 1/1 Running |
| ActorTemplate | `gcp-budget-82cc62c613737d64` | gVisor, phase Ready |
| Snapshot prefix | `gs://ate-snapshots/kagent/gcp-budget` | rustfs URI prefix |
| Golden snapshot | `gs://ate-snapshots/kagent/gcp-budget/5edafe3c-5cec-4d67-92bd-29c29ab75444/2026-08-16T17:55:34Z-XIKENZRG7IHYGCONXJZFBBFY2R` | Ready |

Session (live UI):
`http://172.16.10.135:30500/agents/kagent/gcp-budget/chat/01a00bb9-52b7-77e4-bce9-4b3d32b1d5ce`

---

## Questions asked (live A2A)

1. What's our GCP budget status and which projects are on the billing account?
2. Any compute running in us-east1, and are we near quota?

### Q1 (~18.0s)

Tools: `gcp_whoami`, `gcp_cost_month`, `gcp_budgets`,
`gcp_cost_by_service`, `gcp_projects`.

Billing account `011C38-867461-BE95B1` / linked projects / budgets /
**MTD spend all unavailable**. Runtime error from the billing tools:

`ImportError: cannot import name 'billing_budgets_v1' from 'google.cloud'`

Resource Manager (not the same as billing-account linkage) listed
projects in scope: `viper-kagent`, `maniak-io`, `qr-maniak-io`.

The known lab budget name (`trail budget`, $1) was **not returned**.
Spend was recorded as unavailable, not invented.

Identity used: `gcp-budget-agent@viper-kagent.iam.gserviceaccount.com`.
Org: `maniak.io`. Region scope: `us-east1`.

### Q2 (~15.0s)

Tools: `gcp_projects`, `gcp_compute_capacity`, `gcp_quotas`.

No compute running in `us-east1` on `viper-kagent`. Not near quota.

| Quota | Usage | Limit | Status |
|-------|------:|------:|--------|
| CPUs | 0 | 200 | OK |
| Instances | 0 | 24 | OK |
| Total disk GB | 0 | 4096 | OK |
| SSD total GB | 0 | 500 | OK |
| In-use addresses | 0 | 8 | OK |

Instances: 0 running / 0 stopped. Disks: 0.

---

## Screenshots

Real Chromium `--screenshot` of the tunneled kagent SPA
(`127.0.0.1:30500` → Viper `:30500`). Not reconstructed.

- [shots/ui-agents-grid.png](shots/ui-agents-grid.png) — Agents grid,
  includes the `kagent/gcp-budget` card
- [shots/ui-chat-session.png](shots/ui-chat-session.png) — both live
  answers in one session
- [shots/cli-live-status.txt](shots/cli-live-status.txt) — live
  kubectl dump (text only; no fake terminal PNG)

No GIF. Reconstructed reels are not allowed.

---

## Honest gap

`images/gcp-budget-mcp/requirements.txt` already pins
`google-cloud-billing-budgets==1.21.0`, but the running
`gcp-budget-mcp:dev` image raised `ImportError: billing_budgets_v1`.
Rebuild / re-import the image, then re-ask Q1 so `trail budget` $1
can show. Do not invent spend while that import fails.

---

## What we did not do

- No kagent / Substrate version bump
- No `snapshotsConfig` on the SandboxAgent
- No atelet cutover to `gs://viper-kagent-ate-snapshots`
- No secrets in git or in these shots
