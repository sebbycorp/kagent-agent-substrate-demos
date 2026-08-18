# Live lab report: Arista cEOS on Viper

**Status: NOT YET RUN**

**Date:** _not yet run_
**Lab:** Sebastian’s Viper — Containerlab host (kagent UI not in scope for v1)
**This file is a template.** Visual start: [README.md](README.md).
The how-to is [JOURNEY.md](JOURNEY.md).

Do **not** treat any table below as live data. Every cell that would
hold a version, IP, BGP state, ping result, or screenshot path is
marked `_not yet run_`. Fill this file only after
`./scripts/01-deploy.sh` and `./scripts/02-verify.sh` have been
executed on Viper, and paste **that** output. If a check failed, write
the failure. Do not invent an Established session.

---

## Why this lab (not a live claim)

v1 is a 3-node `arista_ceos` fabric with eBGP underlay so a later
gVisor `SandboxAgent` can read eAPI. Isolated sandboxes, Vault, and
the kagent UI are **not** part of this run until they are applied
elsewhere and recorded here with dates.

---

## Pins (intended; not confirmed live)

| Pin | Value | Live? |
|-----|--------|-------|
| Host | Viper `172.16.10.135` · Ubuntu 24.04 · Docker 29.4.0 · amd64 | _not yet run_ |
| Containerlab | `arista_ceos` kind; binary **not installed** on Viper yet | _not yet run_ |
| Image | local `ceos:4.33.9M` from `docker import cEOS64-lab-4.33.9M.tar.xz` (no Hub pull) | _not yet run_ |
| Image architecture | `linux/amd64` | _not yet run_ |
| Mgmt subnet (planned) | `172.20.20.0/24` — no hardcoded Ma0 | _not yet run_ |
| Underlay | eBGP IPv4, no MPLS | _not yet run_ |
| kagent OSS | 0.10.0-rc2 | not in this v1 (agent not live) |
| Agent Substrate | 0.0.9 | not in this v1 (agent not live) |

No secrets in git. Versions were not bumped.

---

## Vault (key names only; unused until the agent exists)

| | |
|--|--|
| Path (later) | `secret/platform/arista-ceos` |
| Keys (later) | `username`, `password`, `hosts_json` (not `host`) |
| This run | Lab AAA rendered on the Containerlab host from `.env` or Containerlab defaults. **Values are not recorded here.** |

---

## Objects (fill from live inspect)

| Kind | Name | Status |
|------|------|--------|
| Containerlab lab | `arista-ceos` | _not yet run_ |
| Container | `clab-arista-ceos-spine1` | _not yet run_ |
| Container | `clab-arista-ceos-leaf1` | _not yet run_ |
| Container | `clab-arista-ceos-leaf2` | _not yet run_ |
| spine1 mgmt IPv4 | _from docker inspect_ | _not yet run_ |
| leaf1 mgmt IPv4 | _from docker inspect_ | _not yet run_ |
| leaf2 mgmt IPv4 | _from docker inspect_ | _not yet run_ |
| EOS version (eAPI) | _from `show version`_ | _not yet run_ |

---

## Verify script (paste live output)

Command: `./scripts/02-verify.sh`

```text
_not yet run — paste the script's stdout/stderr here. Do not write a
fake PASS block._
```

### Expected checks (for the operator; not results)

1. All 3 containers running
2. EOS/eAPI reachable on each mgmt IPv4
3. BGP Established: spine1↔leaf1, spine1↔leaf2
4. Loopbacks reachable (including leaf1↔leaf2 via spine1)
5. LLDP neighbors on Ethernet1/Ethernet2 as designed

### BGP (fill from eAPI / verify)

| Node | Neighbor | Remote AS | State |
|------|----------|-----------|-------|
| spine1 | 10.0.1.1 | 65101 | _not yet run_ |
| spine1 | 10.0.2.1 | 65102 | _not yet run_ |
| leaf1 | 10.0.1.0 | 65000 | _not yet run_ |
| leaf2 | 10.0.2.0 | 65000 | _not yet run_ |

### Loopback pings (fill from Cli)

| From | To | Result |
|------|-----|--------|
| leaf1 | 10.255.0.1 | _not yet run_ |
| leaf2 | 10.255.0.1 | _not yet run_ |
| spine1 | 10.255.0.11 | _not yet run_ |
| spine1 | 10.255.0.12 | _not yet run_ |
| leaf1 | 10.255.0.12 | _not yet run_ |
| leaf2 | 10.255.0.11 | _not yet run_ |

### LLDP (fill from eAPI)

| Local | Port | Neighbor | Neighbor port |
|-------|------|----------|---------------|
| spine1 | Ethernet1 | leaf1 | _not yet run_ |
| spine1 | Ethernet2 | leaf2 | _not yet run_ |
| leaf1 | Ethernet1 | spine1 | _not yet run_ |
| leaf2 | Ethernet1 | spine1 | _not yet run_ |

---

## Screenshots

**None.** Live shots are pending. See [shots/NOTES.md](shots/NOTES.md).
Do not attach a reconstructed topology PNG or a fake terminal.

When a run exists, list only files that were captured from that run:

- _not yet run_ — `shots/…`

---

## What we did not do

- No Viper deploy in the change that added this folder
- No kagent / Substrate version bump
- No `SandboxAgent` / MCP / ExternalSecret apply
- No password **values** in this file or in git
- No invented BGP, LLDP, or ping results
- No EVPN / MPLS
- No Linux clients
