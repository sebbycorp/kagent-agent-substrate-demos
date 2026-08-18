# Skills index — `arista-ceos` (intended)

All agent skills for this demo live in this folder. They are **not**
mounted into a gVisor actor. There is **no** `SandboxAgent` in this
v1 folder. Keep the files anyway so the future MCP / ConfigMap has a
single source of read-only operations.

kagent **0.10.0-rc2** `SandboxAgentSpec` CEL-rejects `spec.skills`
(*"spec.skills is not supported for sandbox agents"*). Live Viper
agents put instructions in `declarative.systemMessage`. When this
demo grows a ConfigMap, include these files the same way. Do not
invent extra skills in chat or in a second repo.

| Skill | File | When to use |
|-------|------|-------------|
| Fabric | [fabric.md](fabric.md) | BGP sessions, LLDP, interface up/down |
| Routing | [routing.md](routing.md) | Loopbacks, `show ip route`, reachability |
| Executive brief | [executive-brief.md](executive-brief.md) | One short fabric-health answer |

## Standing rules (every skill)

1. Fabric is the Containerlab lab **`arista-ceos`**: `spine1` (AS
   65000), `leaf1` (AS 65101), `leaf2` (AS 65102). Do not invent a
   fourth switch or an EVPN overlay.
2. **Read-only.** No `configure`, no `write`, no neighbor shutdown,
   no image upgrade. If a write tool is added later, ask first.
3. **Never invent** BGP state, prefixes, LLDP neighbors, or ping
   results. If eAPI fails or returns empty, say so.
4. **Never print** eAPI passwords, basic-auth headers, or Vault
   tokens. Hostnames and mgmt IPs from inspect are fine.
5. Do not hardcode Management0 addresses. Use node names / Docker
   DNS / inspect.
6. No generic EOS CLI dump of the full running-config (it can
   include the lab AAA line). Prefer the named tools.

## Intended tool map (not deployed)

These `arista_*` names match the intended k8s-viper MCP. They do not
exist on Viper today (agent is not live). Do not claim a chat used
them.

| Skill | Intended tools |
|-------|----------------|
| Fabric | `arista_whoami`, `arista_bgp_summary`, `arista_lldp`, `arista_interfaces` |
| Routing | `arista_routes`, `arista_ping` |
| Executive brief | compose from the above (still must call tools) |
