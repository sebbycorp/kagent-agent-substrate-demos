# Journey: F5 BIG-IP SandboxAgent live record

GitOps for this agent is already on Viper from
[sebbycorp/k8s-viper](https://github.com/sebbycorp/k8s-viper).
Do not re-apply from this folder. Do not bump kagent past
`0.10.0-rc2` or Substrate past `0.0.9`.

## What this folder is

The live Chromium record of asking `kagent/f5-bigip` two questions
on 2026-08-17. Start at [README.md](README.md). The numbered
runbook (tools, apply path, Vault key **names**) is
[docs/f5-bigip-agent.md](https://github.com/sebbycorp/k8s-viper/blob/main/docs/f5-bigip-agent.md).

## Chat (LAN)

1. Open `http://172.16.10.135:30500/` on the lab LAN (not a Pages site).
2. Pick **kagent/f5-bigip**. Classic `/api/a2a/kagent/f5-bigip` 404s;
   the UI uses `/api/a2a-sandboxes/kagent/f5-bigip`.
3. Ask:
   - `What is this BIG-IP running, and which VIPs are up?`
   - `Which VIPs are down, and why (pool members)?`
4. Expect real iControl answers. If a tool fails or returns empty /
   Unauthenticated, the agent should say so — do not invent a VIP
   name, destination, or availability.

## Secrets

Vault path name only: `secret/platform/f5-bigip` (keys `host`,
`username`, `password`). Never paste the F5 password into git or chat.
