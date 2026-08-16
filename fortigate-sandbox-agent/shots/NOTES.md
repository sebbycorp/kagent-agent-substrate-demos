# fortigate kagent live demo

Recorded Sun 2026-08-16 ~6:32–6:33pm ET (2026-08-16 22:32–22:33 UTC) against live Viper.
No cluster config or version bumps. No reconstructed GIF or screenshots.

## How

Box cannot reach 172.16.10.0/24. Reused existing SSH tunnel
`127.0.0.1:30500 -> Viper :30500` (ngrok `smaniak@2.tcp.ngrok.io:14618`).
**TUNNEL_READY: yes** (HTTP 200 on localhost:30500).
CLI proof via SSH + `docker exec k3s-viper kubectl` (text dump; no fake terminal PNG).

Live chat was two real A2A turns on SandboxAgent `kagent/fortigate`
(`POST /api/a2a-sandboxes/kagent/fortigate`, method `message/stream`) after
`POST /api/sessions` with `agent_ref: "kagent/fortigate"`. Session is in the live UI:

`http://172.16.10.135:30500/agents/kagent/fortigate/chat/01a00cb4-6f1c-79de-8821-5d41a0b66c61`

UI stills are **real Chromium** `--headless=new --screenshot` of the tunneled SPA
(onboarding already skipped in a prior kagent Chrome profile). Not reconstructed frames.

## What was asked

1. What is fw-maniak-hq running, and which WAN is up?
2. What's the YouTube policy?

## A2A answers (one line each)

1. fw-maniak-hq is FortiGate 80F / FortiOS v7.4.11 build 2878 (serial FGT80FTK22061709, VDOM root); wan1 down (DHCP 0.0.0.0), **wan2 up** (DHCP 24.141.221.254/20).
2. Two enabled YouTube policies: `Allow-YouTube-Whitelist` (id 8, `Grp-YouTube-Allowed`, always) and `Allow-YouTube-MasterBR-Night` (id 7, `YT-AppleTV-Master-122`, schedule `Allow-YT-MasterBR-8pm-2am`); no separate YouTube block policy in the compact list.

## Did the agent answer with real data?

Yes. Q1 ~6.64s (`fg_system_status`, `fg_list_interfaces`, `fg_interface_stats`).
Q2 ~11.98s (`fg_list_policies`, `fg_get_policy` x2, `fg_policy_stats`).
Hit counts returned live: policy 8 = 3,007,844 (154 active sessions); policy 7 = 18,902 (0 active).
Q2 is the same ambiguous demo question used before; the agent named the two YouTube-related policies it found and said it did not see a separate block policy.

## CLI proof (live)

```
sandboxagent.kagent.dev/fortigate         True    True
remotemcpserver.kagent.dev/fortigate-mcp  STREAMABLE_HTTP  ...:8084/mcp  True
pod/fortigate-mcp-745d4c9ff5-bxjvc        1/1 Running
```

ActorTemplate `fortigate-b8bc65944f9bc4df` (gVisor):

- location: `gs://ate-snapshots/kagent/fortigate`
- goldenSnapshot: `gs://ate-snapshots/kagent/fortigate/2bcc7a8b-48e0-4b20-aa0d-2bfe0ff5fb1e/2026-08-16T02:45:18Z-R7ZXMSV6CEC2D4NVN4XEX5UDO3`
- phase: Ready

Pins unchanged: kagent 0.10.0-rc2, Agent Substrate 0.0.9. No snapshotsConfig edits. No GCS wiring.

## Secrets

No FortiGate REST token, Vault token, SSH password, or private key on screen or in NOTES.
Host `fw-maniak-hq` / `172.16.10.1` are fine to name.

## Artifacts

- `/workspace/fortigate-shots/ui-agents-grid.png` — real Chromium, includes kagent/fortigate card (78939 bytes)
- `/workspace/fortigate-shots/ui-chat-session.png` — real Chromium, two-question conversation with live answers (252541 bytes; Q2 policy 7 is partially below the fold)
- `/workspace/fortigate-shots/cli-live-status.txt` — live kubectl dump (no fake terminal PNG)
- `a2a-q1-stream.txt` / `a2a-q2-stream.txt` / `session-tasks.json` / `q1-answer.md` / `q2-answer.md` / `meta.json`
