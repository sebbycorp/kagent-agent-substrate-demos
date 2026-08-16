# Journey: FortiGate SandboxAgent live record

GitOps for this agent is already on Viper from
[sebbycorp/k8s-viper](https://github.com/sebbycorp/k8s-viper).
Do not re-apply from this folder. Do not bump kagent past
`0.10.0-rc2` or Substrate past `0.0.9`.

## What this folder is

The live Chromium record of asking `kagent/fortigate` two questions
on 2026-08-16. Start at [README.md](README.md). The numbered
runbook (tools, apply path, Vault key **names**) is
[docs/fortigate-agent.md](https://github.com/sebbycorp/k8s-viper/blob/main/docs/fortigate-agent.md).

## Chat (LAN)

1. Open `http://172.16.10.135:30500/` on the lab LAN (not this Pages site).
2. Pick **kagent/fortigate**. Classic `/api/a2a/kagent/fortigate` 404s;
   the UI uses `/api/a2a-sandboxes/kagent/fortigate`.
3. Ask:
   - `What is fw-maniak-hq running, and which WAN is up?`
   - `What's the YouTube policy?`
4. Expect real FortiOS answers. If a tool fails, the agent should say
   unavailable — do not invent a policy or WAN state.

## Secrets

Vault path name only: `secret/platform/fortigate`. Never paste the
REST token into git or chat.
