# gcp-sandbox-agent

A gVisor `SandboxAgent` for executive GCP budget and capacity in
**us-east1** (org **maniak.io**) on Viper (kagent **0.10.0-rc2** +
Agent Substrate **0.0.9**).

## Live screenshots

![Five SandboxAgent cards in the kagent UI, including gcp-budget](shots/ui-agents-grid.png)

*Live kagent UI, 2026-08-16. Isolated sandboxes (not plain Agents) —
`kagent/gcp-budget` is on the grid.*

![Live gcp-budget chat: billing ImportError + 0 VMs us-east1](shots/ui-chat-session.png)

*Live kagent UI, 2026-08-16. Isolated sandbox chat: billing/budgets/MTD
unavailable (`billing_budgets_v1` ImportError); 0 VMs in us-east1,
not near quota.*

How-to is **[JOURNEY.md](JOURNEY.md)**. What we actually did on Viper
(2026-08-16, America/Toronto): **[REPORT.md](REPORT.md)**.

## Why isolated sandboxes (not a plain Agent)

A normal kagent `Agent` is a Kubernetes Deployment: always on, same
isolation as any other pod. Fine for a cluster helper.

This agent talks to the GCP bill and Compute Engine inventory. The
model gets a filesystem, memory, and a network for the whole chat.
Substrate puts that session in a **gVisor actor** (`SandboxAgent`) on
WorkerPool `kagent-default`:

- Isolated sandbox: gVisor is the wall between the model session and
  the Viper/k3s host. Tools still call GCP through the MCP pod; the
  service-account JSON stays in Vault, not in the actor.
- Idle chats snapshot (zstd) and free the worker. Next message
  restores the same session instead of booting a new container.
- No always-on pod per executive conversation.
- Golden snapshot you can resume.

**Tradeoff on this lab:** nested gVisor on dockerized k3s, and
snapshots are in-cluster rustfs today (`gs://` is a URI prefix only),
not GCS.

The kagent UI shows a **Sandbox: Agent Substrate** badge. Classic
`/api/a2a/<ns>/<name>` 404s (no `Agent` CR); the UI uses
`/api/a2a-sandboxes/kagent/gcp-budget`.

## Architecture

Chat → kagent UI `:30500` → A2A sandboxes → gVisor actor →
`RemoteMCPServer` → `gcp-budget-mcp` → GCP **us-east1**. Vault / ESO
sit on the side (keys never in the actor). Full request path and
snapshot notes: **[docs/architecture.md](docs/architecture.md)**.

```mermaid
flowchart LR
  chat["Chat"]
  ui["kagent UI<br/>:30500"]
  a2a["A2A sandboxes"]
  actor["gVisor actor<br/>ateom-gvisor:v0.0.9"]
  rmcp["RemoteMCPServer<br/>gcp-budget-mcp"]
  mcp["gcp-budget-mcp<br/>:8084/mcp"]
  gcp["GCP us-east1"]
  vault["Vault"]
  eso["ESO"]

  chat --> ui --> a2a --> actor --> rmcp --> mcp --> gcp
  vault --> eso --> mcp
```

## What you will have at the end

1. A Go declarative `SandboxAgent` named **`gcp-budget`** in namespace `kagent`,
   talking through WorkerPool **`kagent-default`** (`ateom-gvisor:v0.0.9`).
2. A FastMCP server (`gcp-budget-mcp:dev`) on **`:8084/mcp`**
   (`STREAMABLE_HTTP`), registered as `RemoteMCPServer/gcp-budget-mcp`.
3. GCP credentials in **Vault** `secret/platform/gcp-budget`
   (keys `credentials_json`, `billing_account`, `project`, `region`),
   synced by External Secrets Operator. **No keys in git.**
4. Substrate snapshots on **rustfs** today (`gs://ate-snapshots/kagent/gcp-budget`
   prefix; omit `snapshotsConfig`, same as hello-substrate / fortigate /
   aws-budget / servicenow).
5. A chat in the kagent UI (`http://172.16.10.135:30500/`) that can answer:

   > What's our us-east1 spend this month and are we over capacity?

   with **real** Cloud Billing / Compute numbers — never invented.
   Cloud Billing Accounts / Budgets / Catalog do not expose
   month-to-date spend; the tools say **unavailable** instead of
   guessing a dollar amount.

## Pins (do not bump)

| Piece | Value |
|-------|--------|
| kagent OSS Helm + CRDs | `0.10.0-rc2` |
| Agent Substrate Helm + CRDs | `0.0.9` |
| Worker image | `ghcr.io/kagent-dev/substrate/ateom-gvisor:v0.0.9` |
| Pattern | Go Declarative `SandboxAgent` + FastMCP + `RemoteMCPServer` + ExternalSecret |
| Model | `default-model-config` (Viper: gpt-5.5 via agentgateway) |
| GCP region | **us-east1** only |
| Org | **maniak.io** |
| Billing account (id only) | `011C38-867461-BE95B1` |
| Projects (names only) | viper-kagent, maniak-io, qr-maniak-io |

rc2 always writes `ActorTemplate` with `spec.pauseImage` and
`env[].valueFrom.secretKeyRef`. Substrate **0.0.9** accepts that shape.
**0.0.12** does not. Do not “upgrade to fix” a Ready=False agent.

## Folder

```text
gcp-sandbox-agent/
  README.md                 # visual landing (this file)
  JOURNEY.md                # how-to
  REPORT.md                 # what we actually did on Viper (2026-08-16)
  shots/                    # live Chromium UI + live CLI dump
  docs/                     # architecture, runbooks, security
  skills/                   # source for ConfigMap gcp-budget-skills
  images/gcp-budget-mcp/    # FastMCP image
  k8s/                      # SandboxAgent + MCP + ExternalSecret + skills ConfigMap
  scripts/                  # prereqs, image import, GCP smoke
```

## Docs

| If you want… | Open |
|--------------|------|
| Architecture (full mermaid + request path) | [docs/architecture.md](docs/architecture.md) |
| How-to (every click) | [JOURNEY.md](JOURNEY.md) |
| What we actually did on Viper | [REPORT.md](REPORT.md) |
| IAM / Vault / gVisor | [docs/security.md](docs/security.md) |
| Commands only | [docs/cli-runbook.md](docs/cli-runbook.md) |
| Console clicks only | [docs/ui-runbook.md](docs/ui-runbook.md) |
| Agent skills | [skills/SKILL.md](skills/SKILL.md) |
| All shots | [shots/](shots/) |

## Honest limits

- Image must be imported on the k3s node (`ctr images import`) before the MCP pod starts.
- Vault path must exist or ExternalSecret stays unsynced.
- Cloud Billing does **not** return month-to-date spend. Tools say unavailable.
- First live Q1 (2026-08-16) hit `ImportError: billing_budgets_v1` from the old `from google.cloud import billing_budgets_v1` alias. The working import is `from google.cloud.billing import budgets_v1`. After rebuild, Cloud Billing returned `Unauthenticated`. Do not invent spend.
- There is **no** generic “run any gcloud” tool. No project-delete, no IAM-create.
- Never commit GCP service-account JSON or Vault secret **values**.
