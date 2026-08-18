# arista-ceos shots

**No PNG/GIF in this directory.** Live Chromium shots will follow
when captured. Do not invent files to look finished.

## Live-verified in text (2026-08-17 evening ET, Viper)

Recorded in [REPORT.md](../REPORT.md) / [JOURNEY.md](../JOURNEY.md)
from real `containerlab inspect`, docker, and EOS `Cli`. Not from
screenshots:

- containerlab **0.78.2** (commit `8e6596157`), `/usr/local/bin/containerlab`
- image `ceos:4.33.9M` / `ceos:latest`,
  `sha256:56fcaed9ef895428e760997eb59ebfca2df661c915f360ae2ba4284439c3bb4f`,
  `linux/amd64`, official `cEOS64-lab-4.33.9M.tar.xz` import (no
  `sebbycorp/ceosimage` pull)
- nodes running: `clab-arista-ceos-spine1` `172.20.20.2` `ec9544c551ae`;
  `clab-arista-ceos-leaf2` `172.20.20.3` `42ac270fca76`;
  `clab-arista-ceos-leaf1` `172.20.20.4` `88b5b52016bf`
- mgmt net `arista-ceos` `172.20.20.0/24`
- EOS `4.33.9M-49063934.4339M` x86_64 on all three
- BGP Established (spine1 PfxRcd 1/1; leaf1/leaf2 PfxRcd 2)
- spine1 LLDP Et1=leaf1, Et2=leaf2
- spine/leaf loopback pings work; leaf1→`10.255.0.12` sourced from
  `10.255.0.11`: 3/3, ttl=63
- first boot: inotify / Too many open files; fixed via
  `/etc/sysctl.d/99-containerlab-inotify.conf`
- k3s-viper left running; `SandboxAgent` not applied; no kagent chat

## What is accepted

- Real Chromium `--headless=new --screenshot` (or a real interactive
  capture) of a tunneled or LAN kagent UI **after** the agent exists
- Real CLI dumps (`containerlab inspect`, `./scripts/02-verify.sh`,
  `docker exec … Cli`) saved as `.txt` from that session
- A date/time and the host (Viper) in the commit message or a short
  note in this file

## What is rejected

- Reconstructed GIFs or “sample” UI frames
- AI-generated topology pictures presented as a live run
- Hand-typed `show ip bgp summary` that was not copied from a device
- Screenshots that show `.env`, Vault tokens, eAPI basic-auth headers,
  or `username … secret …` lines
- Stock photos of Arista hardware

If a file lands here without a live provenance note, delete it.
Do not invent a `cli-live-status.txt` or a topology PNG.
