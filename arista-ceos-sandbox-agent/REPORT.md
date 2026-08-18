# Live lab report: Arista cEOS on Viper

**Status: LIVE**

**Date:** 2026-08-17 (evening ET, America/Toronto)
**Lab:** Sebastian’s Viper `172.16.10.135` — Containerlab host
**Checkout on Viper:** `/home/smaniak/src/kagent-agent-substrate-demos/arista-ceos-sandbox-agent`
**This file is a record.** Visual start: [README.md](README.md).
The how-to is [JOURNEY.md](JOURNEY.md).

Nothing here is invented. Every version, container id, mgmt IP, BGP
state, and ping count below was taken from a live `containerlab
inspect` / `docker` / EOS `Cli` session that evening. Cells that
were not captured say so. No reconstructed screenshots.

k3s-viper was left running. A kagent `SandboxAgent` was **not**
applied. There are no kagent chat shots.

---

## Why this lab (what this run is)

v1 is a 3-node `arista_ceos` fabric with eBGP underlay so a later
gVisor `SandboxAgent` can read eAPI. Isolated sandboxes, Vault, and
the kagent UI are **not** part of this run.

---

## Pins (confirmed live 2026-08-17 evening ET)

| Pin | Value | Live? |
|-----|--------|-------|
| Host | Viper `172.16.10.135` | yes |
| Containerlab | **0.78.2** (commit `8e6596157`, 2026-08-13), binary `/usr/local/bin/containerlab` | yes |
| Image | local `ceos:4.33.9M` / `ceos:latest` | yes |
| Image digest | `sha256:56fcaed9ef895428e760997eb59ebfca2df661c915f360ae2ba4284439c3bb4f` | yes |
| Image architecture | `linux/amd64` | yes |
| Image source | official `cEOS64-lab-4.33.9M.tar.xz` via `docker import` | yes |
| Hub | did **not** pull `sebbycorp/ceosimage` | yes |
| Mgmt net | `arista-ceos` `172.20.20.0/24` | yes |
| Underlay | eBGP IPv4, no MPLS | yes |
| kagent OSS | 0.10.0-rc2 | k3s-viper running; agent not applied |
| Agent Substrate | 0.0.9 | not in this v1 (agent not live) |

No secrets in git. Versions were not bumped.

---

## First boot (honest)

The first Containerlab boot died: systemd **Too many open files** /
inotify. Host fix applied at
`/etc/sysctl.d/99-containerlab-inotify.conf`:

- `fs.inotify.max_user_instances=8192`
- `fs.inotify.max_user_watches=1048576`

Then a clean redeploy. The objects below are from that second lab,
not the failed first boot.

---

## Vault (key names only; unused until the agent exists)

| | |
|--|--|
| Path (later) | `secret/platform/arista-ceos` |
| Keys (later) | `username`, `password`, `hosts_json` (not `host`) |
| This run | Lab AAA rendered on the Containerlab host from `.env` or Containerlab defaults. **Values are not recorded here.** |

---

## Objects (live inspect + docker)

| Kind | Name | Status |
|------|------|--------|
| Containerlab lab | `arista-ceos` | running (this evening) |
| Container | `clab-arista-ceos-spine1` | running · `ceos:4.33.9M` · id `ec9544c551ae` |
| Container | `clab-arista-ceos-leaf2` | running · `ceos:4.33.9M` · id `42ac270fca76` |
| Container | `clab-arista-ceos-leaf1` | running · `ceos:4.33.9M` · id `88b5b52016bf` |
| spine1 mgmt IPv4 | `172.20.20.2` | containerlab inspect + docker |
| leaf2 mgmt IPv4 | `172.20.20.3` | containerlab inspect + docker |
| leaf1 mgmt IPv4 | `172.20.20.4` | containerlab inspect + docker |
| EOS version (Cli, all three) | `4.33.9M-49063934.4339M` · architecture `x86_64` | yes |

---

## Verify (live Cli / inspect — not a reconstructed script log)

`./scripts/02-verify.sh` stdout was **not** saved this evening.
Do not treat the blocks below as that script. These are the live
Cli and inspect facts that were recorded.

### containerlab inspect + docker (running)

```text
clab-arista-ceos-spine1  ceos:4.33.9M  running  mgmt 172.20.20.2  id ec9544c551ae
clab-arista-ceos-leaf2   ceos:4.33.9M  running  mgmt 172.20.20.3  id 42ac270fca76
clab-arista-ceos-leaf1   ceos:4.33.9M  running  mgmt 172.20.20.4  id 88b5b52016bf
Mgmt net: arista-ceos 172.20.20.0/24
```

### EOS version (real Cli, all three)

Software image version `4.33.9M-49063934.4339M`, architecture `x86_64`.

### BGP (real Cli, all Established)

spine1 RID `10.255.0.1` local AS `65000`

- leaf1 `10.0.1.1` AS `65101` Estab PfxRcd `1`
- leaf2 `10.0.2.1` AS `65102` Estab PfxRcd `1`

leaf1 RID `10.255.0.11` local AS `65101`

- spine1 `10.0.1.0` AS `65000` Estab PfxRcd `2`

leaf2 RID `10.255.0.12` local AS `65102`

- spine1 `10.0.2.0` AS `65000` Estab PfxRcd `2`

Raw spine1 `show ip bgp summary`:

```text
BGP summary information for VRF default
Router identifier 10.255.0.1, local AS number 65000
  Description              Neighbor V AS           MsgRcvd   MsgSent  InQ OutQ  Up/Down State   PfxRcd PfxAcc
  leaf1                    10.0.1.1 4 65101              5         6    0    0 00:00:39 Estab   1      1
  leaf2                    10.0.2.1 4 65102              5         6    0    0 00:00:37 Estab   1      1
```

Leaf `show ip bgp summary` tables were not pasted this evening
beyond the Established / PfxRcd lines above. Do not invent MsgRcvd
or Up/Down for leaf1/leaf2.

### BGP table

| Node | Neighbor | Remote AS | State | PfxRcd |
|------|----------|-----------|-------|--------|
| spine1 | 10.0.1.1 | 65101 | Estab | 1 |
| spine1 | 10.0.2.1 | 65102 | Estab | 1 |
| leaf1 | 10.0.1.0 | 65000 | Estab | 2 |
| leaf2 | 10.0.2.0 | 65000 | Estab | 2 |

### Loopback pings

| From | To | Result |
|------|-----|--------|
| spine ↔ leaf loopbacks | — | work (packet counts not recorded this evening) |
| leaf1 | 10.255.0.12 | 3/3 replies, ttl=63, sourced from 10.255.0.11 |

Individual `repeat` lines for leaf1→spine1, leaf2→spine1,
spine1→leaves, and leaf2→leaf1 were not saved. Do not invent them.

### LLDP (captured on spine1 only)

| Local | Port | Neighbor | Neighbor port |
|-------|------|----------|---------------|
| spine1 | Ethernet1 / Et1 | leaf1 | not captured this evening |
| spine1 | Ethernet2 / Et2 | leaf2 | not captured this evening |
| leaf1 | Ethernet1 | — | not captured this evening |
| leaf2 | Ethernet1 | — | not captured this evening |

---

## Screenshots

**None.** `shots/` has no PNG/GIF from this run. Live Chromium shots
will follow when captured. See [shots/NOTES.md](shots/NOTES.md).
Do not attach a reconstructed topology PNG or a fake terminal.

- _(empty)_ — no `shots/*.png` or `shots/*.gif` in this commit

---

## What we did not do

- No `SandboxAgent` / MCP / ExternalSecret apply (k3s-viper left running)
- No kagent chat session
- No kagent / Substrate version bump
- No password **values** in this file or in git
- No invented BGP, LLDP, or ping results beyond the Cli text above
- No EVPN / MPLS
- No Linux clients
- No Hub pull of `sebbycorp/ceosimage`
- No reconstructed PNG/GIF
