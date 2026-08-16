# Live lab report: what we actually did on Viper

**Date:** 2026-08-16 (America/Toronto)
**Lab:** Sebastian’s Viper, kagent UI `http://172.16.10.135:30500/`
**This file is a record.** The how-to is [JOURNEY.md](JOURNEY.md). Nothing here is invented; every number and object name was confirmed live that morning.

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

Agents grid at `http://172.16.10.135:30500/` showed three SandboxAgent cards: **aws-budget**, **fortigate**, **hello-substrate**.

Chat: `http://172.16.10.135:30500/agents/kagent/aws-budget/chat`

The UI talks to `POST /api/a2a-sandboxes/kagent/aws-budget`. Classic `/api/a2a/kagent/aws-budget` is **404** because there is no `Agent` CR.

---

## Live A2A run (us-east-2)

Confirmed through that sandbox A2A path, not invented:

| | |
|--|--|
| Month-to-date spend | **$0.67** |
| Budget | **4.13%** of **$100** |
| EC2 / ASG / RDS / EBS | **0 / 0 / 0 / 0** |
| `whoami` | `aws-budget-agent` |

---

## Shots

Screenshots and gifs of this live Viper run belong in **[shots/](shots/)**. Image files are not in this repo yet.

The demo GIF/mp4 at box path `/workspace/aws-budget-shots/` is a **reconstructed reel of that real A2A turn**, not a Chromium pixel capture of the SPA. That box path is not this folder.
