# f5-bigip kagent live demo

Recorded Mon 2026-08-17 ~10:48–10:56am ET (2026-08-17 14:48–14:56 UTC) against live Viper.
No cluster config or version bumps. No reconstructed GIF or screenshots.

## How

Box cannot reach 172.16.10.0/24. Opened SSH tunnel
`127.0.0.1:30500 -> Viper :30500` (ngrok `smaniak@2.tcp.ngrok.io:14618`).
**TUNNEL_READY: yes** (HTTP 200 on localhost:30500).
CLI proof via SSH + `docker exec k3s-viper kubectl` (text dump; no fake terminal PNG).

Live chat was two real A2A turns on SandboxAgent `kagent/f5-bigip`
(`POST /api/a2a-sandboxes/kagent/f5-bigip`, method `message/stream`) after
`POST /api/sessions` with `agent_ref: "kagent/f5-bigip"`. Session is in the live UI:

`http://172.16.10.135:30500/agents/kagent/f5-bigip/chat/01a01034-5a45-74b6-a29f-631e0de79170`

UI stills are **real Chromium** `--headless=new --screenshot` of the tunneled SPA
(onboarding skipped via the same local HTML inject used on prior Viper
records so the live agents grid and chat render). Not reconstructed frames.

## What was asked

1. What is this BIG-IP running, and which VIPs are up?
2. Which VIPs are down, and why (pool members)?

## A2A answers (one line each)

1. Host `https://172.16.10.10` answered (`f5_system` ok) but product/version/build were `null`. Two of 19 VIPs available: `k8s_iceman_argocd_vs` `172.16.20.60:443` and `k8s_iceman_kagent_vs` `172.16.20.62:8080`.
2. 17 VIPs offline / still enabled; each checked pool reason was "The children pool member(s) are down" (members `state: down`, `session: monitor-enabled`).

## Did the agent answer with real data?

Yes. Q1 ~12.64s (`f5_system`, `f5_vip_brief`).
Q2 ~36.36s (`f5_system`, `f5_vip_brief`, `f5_pool_status` ×16).
Identity fields were empty — recorded as `null`, not replaced with an older iControl peek.

## CLI proof (live)

```
sandboxagent.kagent.dev/f5-bigip         True    True
remotemcpserver.kagent.dev/f5-bigip-mcp  STREAMABLE_HTTP  ...:8084/mcp  True
pod/f5-bigip-mcp-7f75b47b78-mdblb        1/1 Running
```

ActorTemplate `f5-bigip-3adfcbf7c448a873` (gVisor):

- location: `gs://ate-snapshots/kagent/f5-bigip`
- goldenSnapshot: `gs://ate-snapshots/kagent/f5-bigip/2b9f5b6a-930d-471c-b679-22f31895f8c9/2026-08-17T14:32:42Z-23PD7HXZ5JL7OO7RNHUWZ5YOWS`
- phase: Ready

Pins unchanged: kagent 0.10.0-rc2, Agent Substrate 0.0.9. No snapshotsConfig edits. No GCS wiring.

## Secrets

No F5 password, Vault token, SSH password, GoDaddy PAT, or private key on screen or in NOTES.
Host `https://172.16.10.10` is fine to name.

## Artifacts

- `/workspace/f5-bigip-shots/ui-agents-grid.png` — real Chromium, includes kagent/f5-bigip card (83185 bytes)
- `/workspace/f5-bigip-shots/ui-chat-session.png` — real Chromium, two-question conversation with live answers (175542 bytes; 17-row down table is below the fold)
- `/workspace/f5-bigip-shots/cli-live-status.txt` — live kubectl dump (no fake terminal PNG)
- `a2a-q1-stream.txt` / `a2a-q2-stream.txt` / `session-tasks.json` (box only; not committed)
