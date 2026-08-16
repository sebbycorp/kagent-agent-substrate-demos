# gcp-budget kagent live demo

Recorded Sun 2026-08-16 ~1:59–2:05pm ET (2026-08-16 17:59–18:05 UTC) against live Viper.
No cluster config or version bumps. No reconstructed GIF.

## How

Box cannot reach 172.16.10.0/24. Reused existing SSH tunnel
`127.0.0.1:30500 -> Viper :30500` (ngrok `smaniak@2.tcp.ngrok.io:14618`).
**TUNNEL_READY: yes** (HTTP 200 on localhost:30500).
CLI proof via SSH + `docker exec k3s-viper kubectl` (text dump; this executor
cannot screenshot a real terminal — UI automation via Shell is blocked).

Live chat was two real A2A turns on SandboxAgent `kagent/gcp-budget`
(`POST /api/a2a-sandboxes/kagent/gcp-budget`, method `message/stream`) after
`POST /api/sessions` with `agent_ref: "kagent/gcp-budget"`. Session is in the live UI:

`http://172.16.10.135:30500/agents/kagent/gcp-budget/chat/01a00bb9-52b7-77e4-bce9-4b3d32b1d5ce`

UI stills are **real Chromium** `--screenshot` of the tunneled SPA (onboarding
already skipped in a prior kagent Chrome profile). Not reconstructed frames.

## What was asked

1. What's our GCP budget status and which projects are on the billing account?
2. Any compute running in us-east1, and are we near quota?

## A2A answers (one line each)

1. Billing account `011C38-867461-BE95B1` / budgets / linked projects / **MTD spend all unavailable** (`ImportError: cannot import name 'billing_budgets_v1' from 'google.cloud'`). Resource Manager projects in scope: `viper-kagent`, `maniak-io`, `qr-maniak-io`. Budget name (e.g. trail budget $1) was **not returned**.
2. **0 VMs** in `us-east1` (0 running / 0 stopped / 0 disks) on `viper-kagent`; **not near quota** (CPUs 0/200, instances 0/24).

## Did the agent answer with real data?

Yes, with honest gaps. Q1 ~18.0s (gcp_whoami, gcp_cost_month, gcp_budgets, gcp_cost_by_service, gcp_projects).
Q2 ~15.0s (gcp_projects, gcp_compute_capacity, gcp_quotas).
Cloud Billing APIs did **not** return MTD spend — recorded as unavailable, not invented.

Identity mentioned: `gcp-budget-agent@viper-kagent.iam.gserviceaccount.com` (email only).
Org: `maniak.io`. Region scope: `us-east1`.

## CLI proof (live)

```
sandboxagent.kagent.dev/gcp-budget        True    True
remotemcpserver.kagent.dev/gcp-budget-mcp STREAMABLE_HTTP  ...:8084/mcp  True
pod/gcp-budget-mcp-5664dfb8f7-pwlwv       1/1 Running
```

ActorTemplate `gcp-budget-82cc62c613737d64` (gVisor):

- location: `gs://ate-snapshots/kagent/gcp-budget`
- goldenSnapshot: `gs://ate-snapshots/kagent/gcp-budget/5edafe3c-5cec-4d67-92bd-29c29ab75444/2026-08-16T17:55:34Z-XIKENZRG7IHYGCONXJZFBBFY2R`
- phase: Ready

## Secrets

No SA JSON, private keys, Vault tokens, or SSH passwords on screen or in NOTES.

## Artifacts

- `/workspace/gcp-budget-shots/ui-agents-grid.png` — real Chromium, includes gcp-budget card
- `/workspace/gcp-budget-shots/ui-chat-session.png` — real Chromium, two-question conversation (not connection-refused)
- `/workspace/gcp-budget-shots/cli-live-status.txt` — live kubectl dump (no fake terminal PNG)
- `a2a-q1-stream.txt` / `a2a-q2-stream.txt` / `session-tasks.json` — redacted live turns
