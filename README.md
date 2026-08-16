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

Do **not** put AWS keys, GCP keys, or tokens in this git repo.

## Demos

| Demo | Start here | What you get |
|------|------------|--------------|
| [aws-sandbox-agent/](aws-sandbox-agent/) | **[JOURNEY.md](aws-sandbox-agent/JOURNEY.md)** | Secure gVisor `SandboxAgent` for AWS **budget and capacity** in **us-east-2**. FastMCP on `:8084/mcp`, Vault/ESO keys, snapshots aimed at a **new GCP project** GCS bucket. |

## How to use a demo

1. Open the demo folder README (what it is, what “done” looks like).
2. Walk [JOURNEY.md](aws-sandbox-agent/JOURNEY.md) in order — every UI click and CLI command, with *why*.
3. Keep `docs/cli-runbook.md` open if you only want copy-paste commands.
4. Never commit secret **values**. Manifests carry Vault **paths** and key **names** only.
