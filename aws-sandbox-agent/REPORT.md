# Live lab report: what we actually did on Viper

**Date:** 2026-08-16 (America/Toronto)
**Lab:** Sebastian’s Viper, kagent UI `http://172.16.10.135:30500/`
**This file is a record.** Visual start: [README.md](README.md).
The how-to is [JOURNEY.md](JOURNEY.md). Nothing here is invented;
every number and object name was confirmed live that morning.

---

## Why isolated sandboxes (not a plain Agent)

A normal kagent `Agent` is a Kubernetes Deployment: always on, same
isolation as any other pod. Fine for a cluster helper.

This `aws-budget` agent talks to the AWS bill. The model gets a
filesystem, memory, and a network for the whole chat. Substrate puts
that session in a **gVisor actor** (`SandboxAgent`) on WorkerPool
`kagent-default`: isolated sandbox (gVisor is the wall; tools still
call AWS through the MCP pod; keys stay in Vault), idle chats
snapshot (zstd) and free the worker, no always-on pod per executive
conversation, golden snapshot you can resume.

**Tradeoff on this lab:** nested gVisor on dockerized k3s, and
snapshots are in-cluster rustfs today (`gs://` is a URI prefix only),
not GCS.

These are isolated sandboxes, not plain Agents. The kagent UI shows a
**Sandbox: Agent Substrate** badge on the three cards. Classic
`/api/a2a/<ns>/<name>` 404s because there is no `Agent` CR; the UI
uses `/api/a2a-sandboxes/kagent/aws-budget`.

---

## Repo we applied

`main` after PR #1 and PR #2. Clone on Viper only:

`/home/smaniak/src/kagent-agent-substrate-demos` at `5acac53`.

| Pin | Value |
|-----|--------|
| kagent OSS | **0.10.0-rc2** |
| Agent Substrate | **0.0.9** |

No `ignoreDifferences`. No secrets in git. Versions were not bumped.

---

## What we did not wire

GCP project **viper-kagent** (89434469276, org **maniak.io**) and bucket **gs://viper-kagent-ate-snapshots** (`us-east1`) exist. They are **reserved**. We did not point atelet or this SandboxAgent at them.

Today:

| | Live |
|--|--|
| atelet | S3 → in-cluster **rustfs** bucket `ate-snapshots` |
| SandboxAgent `aws-budget` | **omits** `snapshotsConfig` |
| ActorTemplate location | `gs://ate-snapshots/kagent/aws-budget` (prefix only; bytes on rustfs) |

---

## AWS identity (names only)

| | |
|--|--|
| Account | **616973157416** |
| IAM user | `aws-budget-agent` |
| Policy | customer-managed `AwsBudgetAgentReadOnly` (read-mostly **us-east-2**) |
| Vault | `secret/platform/aws-budget` |
| Vault keys | `access_key_id`, `secret_access_key`, `region=us-east-2` |

No access-key **values**, tokens, or secret strings are in this file or in git.

---

## What we applied on Viper

1. Built image `aws-budget-mcp:dev` on Viper.
2. `ctr images import` into k3s. Deployment `imagePullPolicy: IfNotPresent`.
3. Applied with **host kustomize piped into k3s** (not `apply -k` against a host path):

```bash
kubectl kustomize aws-sandbox-agent/k8s | docker exec -i k3s-viper kubectl apply -f -
```

Objects that landed:

- ConfigMap `aws-budget-skills`
- Service / Deployment `aws-budget-mcp`
- ExternalSecret
- RemoteMCPServer
- SandboxAgent `aws-budget`

**Skills:** kagent 0.10.0-rc2 rejects `spec.skills` on `SandboxAgent`. The ConfigMap plus `promptTemplate` inlines the skill text into `systemMessage`.

---

## Live status (~9:21–9:50 AM ET)

| Object | Status |
|--------|--------|
| ExternalSecret | `SecretSynced` |
| MCP pod | `1/1` |
| RemoteMCPServer | Accepted (**11** tools) |
| SandboxAgent | Ready |
| ActorTemplate | `aws-budget-8362477e07b85896` (gvisor) |
| Golden snapshot | ready |

---

## kagent UI

Agents grid at `http://172.16.10.135:30500/` showed three SandboxAgent
cards: **aws-budget**, **fortigate**, **hello-substrate**. All three
**OpenAI gpt-5.5**. `aws-budget` description: “Executive AWS budget
and capacity assistant for us-east-2 (gVisor).”

**Live UI** (Chromium screenshot, 2026-08-16 — not reconstructed):

![kagent Agents grid — three SandboxAgent cards](shots/ui-agents-grid.png)

Chat: `http://172.16.10.135:30500/agents/kagent/aws-budget/chat`

The UI talks to `POST /api/a2a-sandboxes/kagent/aws-budget`. Classic
`/api/a2a/kagent/aws-budget` is **404** because there is no `Agent` CR.

---

## Live A2A run (us-east-2)

Confirmed through that sandbox A2A path, not invented:

| | |
|--|--|
| Month-to-date spend | **$0.67** |
| Budget | **$4.13 / $100** (4.13% used) |
| EC2 / ASG / RDS / EBS | **0 / 0 / 0 / 0** |
| `whoami` | `aws-budget-agent` |
| Tool calls | **10/10** |

**Live UI** (Chromium screenshot of the same chat, 2026-08-16 — not
reconstructed):

![kagent/aws-budget live chat — spend and capacity](shots/ui-chat-session.png)

---

## Shots

Live Chromium screenshots and the reconstructed reel live in
**[shots/](shots/)**.

| File | What it is |
|------|------------|
| [ui-agents-grid.png](shots/ui-agents-grid.png) | Live kagent UI, 2026-08-16. Three SandboxAgent cards, all OpenAI gpt-5.5. |
| [ui-chat-session.png](shots/ui-chat-session.png) | Live kagent UI, 2026-08-16. Spend/capacity turn: 10/10 tools, MTD $0.67, budget $4.13 / $100, 0 EC2/ASG/RDS/EBS. |
| [aws-budget-kagent-demo.gif](shots/aws-budget-kagent-demo.gif) | **Reconstructed reel** of that same live A2A turn — not a Chromium pixel capture of the SPA. ([mp4](shots/aws-budget-kagent-demo.mp4)) |
