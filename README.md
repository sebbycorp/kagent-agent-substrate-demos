# kagent-agent-substrate-demos

How-to demos for **OSS kagent + Agent Substrate** (gVisor `SandboxAgent`s).
The repo started as a stub README; each folder is a complete, human-reproducible
lab you can follow without inventing CRD fields or bumping pins.

Proven runtime on Sebastian's Viper lab (`172.16.10.135`):

| Piece | Pin |
|-------|-----|
| kagent OSS | **0.10.0-rc2** |
| Agent Substrate | **0.0.9** (not 0.0.12 — rc2 `ActorTemplate`s need `valueFrom` + `pauseImage`) |
| Worker image | `ghcr.io/kagent-dev/substrate/ateom-gvisor:v0.0.9` |
| WorkerPool | `kagent-default` |
| UI | NodePort **30500** |

Do **not** put AWS keys, GCP service-account JSON, ServiceNow passwords, or tokens in this git repo.

## Demos

| Demo | Start here | What you get |
|------|------------|--------------|
| [aws-sandbox-agent/](aws-sandbox-agent/) | **[README.md](aws-sandbox-agent/README.md)** | Isolated gVisor `SandboxAgent` (not a plain Agent Deployment) for AWS **budget and capacity** in **us-east-2**. FastMCP on `:8084/mcp`, Vault/ESO keys, snapshots on **rustfs** today (`gs://ate-snapshots/kagent/aws-budget`). Screenshots + architecture on the README; how-to in [JOURNEY.md](aws-sandbox-agent/JOURNEY.md). |
| [service-now-sandbox-agent/](service-now-sandbox-agent/) | **[README.md](service-now-sandbox-agent/README.md)** | Isolated gVisor `SandboxAgent` (not a plain Agent Deployment) for **ServiceNow IT tickets** on a personal developer instance (host name only: `https://dev203166.service-now.com`). FastMCP on `:8084/mcp`, Vault/ESO keys (`secret/platform/servicenow`), snapshots on **rustfs** today (`gs://ate-snapshots/kagent/servicenow`). Architecture on the README; how-to in [JOURNEY.md](service-now-sandbox-agent/JOURNEY.md); live Viper record in [REPORT.md](service-now-sandbox-agent/REPORT.md). |
| [gcp-sandbox-agent/](gcp-sandbox-agent/) | **[README.md](gcp-sandbox-agent/README.md)** | Isolated gVisor `SandboxAgent` (not a plain Agent Deployment) for GCP **budget and capacity** in **us-east1** (org **maniak.io**). FastMCP on `:8084/mcp`, Vault/ESO keys (`secret/platform/gcp-budget`), snapshots on **rustfs** today (`gs://ate-snapshots/kagent/gcp-budget`). Architecture on the README; how-to in [JOURNEY.md](gcp-sandbox-agent/JOURNEY.md). |

## How to use a demo

1. Open the demo folder README (screenshots + architecture — what it is, what “done” looks like).
2. Walk that demo’s `JOURNEY.md` in order — every UI click and CLI command, with *why*.
3. Keep `docs/cli-runbook.md` open if you only want copy-paste commands.
4. Never commit secret **values**. Manifests carry Vault **paths** and key **names** only.
