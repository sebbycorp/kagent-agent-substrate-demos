# aws-sandbox-agent

A **secure gVisor `SandboxAgent`** on OSS **kagent 0.10.0-rc2** + **Agent Substrate 0.0.9**.
Its job: help the executive team manage **AWS budget and capacity in us-east-2**.

This is a HOW-TO plus a working agent. Follow **[JOURNEY.md](JOURNEY.md)** if you
want to reproduce it by hand and understand each click.

**What we actually did on Viper** (2026-08-16, America/Toronto):
**[REPORT.md](REPORT.md)**.

## What you will have at the end

1. A Go declarative `SandboxAgent` named **`aws-budget`** in namespace `kagent`,
   talking through WorkerPool **`kagent-default`** (`ateom-gvisor:v0.0.9`).
2. A FastMCP server (`aws-budget-mcp:dev`) on **`:8084/mcp`**
   (`STREAMABLE_HTTP`), registered as `RemoteMCPServer/aws-budget-mcp`.
3. AWS credentials in **Vault** `secret/platform/aws-budget`, synced by
   External Secrets Operator. **No keys in git.**
4. Substrate snapshots on **rustfs** today (`gs://ate-snapshots/kagent/aws-budget`
   prefix; omit `snapshotsConfig`, same as hello-substrate / fortigate).
   GCP project **viper-kagent** / **gs://viper-kagent-ate-snapshots**
   already exist and are reserved for a later cluster-wide atelet
   cutover — do not create another, do not set that URI on this agent
   yet. See [docs/snapshots-gcs.md](docs/snapshots-gcs.md).
5. A chat in the kagent UI (`http://172.16.10.135:30500/`) that can answer:

   > What's our us-east-2 spend this month and are we over capacity?

   with **real** Cost Explorer / EC2 / quota numbers — never invented.

## Pins (do not bump)

| Piece | Value |
|-------|--------|
| kagent OSS Helm + CRDs | `0.10.0-rc2` |
| Agent Substrate Helm + CRDs | `0.0.9` |
| Worker image | `ghcr.io/kagent-dev/substrate/ateom-gvisor:v0.0.9` |
| Pattern | Go Declarative `SandboxAgent` + FastMCP + `RemoteMCPServer` + ExternalSecret |
| Model | `default-model-config` (Viper: gpt-5.5 via agentgateway) |
| AWS region | **us-east-2** only |

rc2 always writes `ActorTemplate` with `spec.pauseImage` and
`env[].valueFrom.secretKeyRef`. Substrate **0.0.9** accepts that shape.
**0.0.12** does not. Do not “upgrade to fix” a Ready=False agent.

## Folder

```text
aws-sandbox-agent/
  README.md                 # this file
  JOURNEY.md                # human story: every click + command, in order
  REPORT.md                 # what we actually did on Viper (2026-08-16)
  docs/
    architecture.md         # mermaid + request path
    cli-runbook.md          # copy-paste CLI only
    ui-runbook.md           # kagent UI + GCP + AWS console clicks
    snapshots-gcs.md        # rustfs today; reserved GCS for later cutover
    security.md             # least-privilege IAM, Vault/ESO, gVisor
  skills/                   # source for ConfigMap aws-budget-skills (not a gVisor mount)
    SKILL.md
    budget.md
    capacity.md
    executive-brief.md
  images/aws-budget-mcp/    # FastMCP image (Viper fortigate-mcp shape)
  k8s/                      # SandboxAgent + MCP + ExternalSecret + skills ConfigMap
  scripts/                  # prereqs, GCS bucket, image import, AWS smoke
```

## Start

| If you want… | Open |
|--------------|------|
| What we actually did on Viper | [REPORT.md](REPORT.md) |
| To understand and reproduce | [JOURNEY.md](JOURNEY.md) |
| Commands only | [docs/cli-runbook.md](docs/cli-runbook.md) |
| Console clicks only | [docs/ui-runbook.md](docs/ui-runbook.md) |
| Snapshot storage | [docs/snapshots-gcs.md](docs/snapshots-gcs.md) |
| IAM / Vault / gVisor | [docs/security.md](docs/security.md) |
| Agent skills | [skills/SKILL.md](skills/SKILL.md) |

## Honest limits

- Image must be imported on the k3s node (`ctr images import`) before the MCP pod starts.
- Vault path must exist or ExternalSecret stays unsynced.
- Cost Explorer and Budgets APIs live in **us-east-1**; tools still **filter** to us-east-2.
- There is **no** generic “run any aws cli” tool. No IAM create, no terminate, no budget-delete.
- Never commit AWS or GCP secret **values**.
