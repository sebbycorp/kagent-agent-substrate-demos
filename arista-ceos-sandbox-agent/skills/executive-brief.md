# Skill: executive brief

One short fabric-health brief someone can read in **30 seconds**.
There is no composed MCP tool yet — call the live eAPI tools and
write this shape. If a tool errors, keep the line and write
`unavailable (<reason>)`.

## Shape

```text
Lab: arista-ceos  As of: <tool time>
Nodes: spine1 AS65000, leaf1 AS65101, leaf2 AS65102
EOS: <version per node, or unavailable>
BGP: <Established count>/4 expected sessions
LLDP: <which designed links seen>
Loopbacks: <which of 10.255.0.1/11/12 ping>
Risk: <one sentence, or “none from these reads”>
```

## Rules

- Four to eight lines. No essay.
- Every state and version comes from a tool result in this turn.
- Never attach eAPI passwords, Vault tokens, or a startup-config
  snippet that includes `secret`.
- Do not mention EVPN/MPLS as present. v1 is eBGP IPv4 only.
