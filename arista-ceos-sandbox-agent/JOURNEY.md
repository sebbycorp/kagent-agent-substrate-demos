# Journey: Arista cEOS Containerlab fabric on Viper

**Visual start:** [README.md](README.md) (architecture; live shots
pending). **Live lab record:** [REPORT.md](REPORT.md) — template only
until someone actually deploys this on Viper. Do not fill REPORT.md
from memory.

This is the human path for **v1: three cEOS switches, eBGP underlay**.
The gVisor `SandboxAgent` / FastMCP / Vault wiring is **not** in this
folder yet. Do not apply leftover `k8s/` manifests from other demos
and call it this lab.

Lab host: Sebastian’s Viper **`172.16.10.135`**, Ubuntu **24.04**,
Docker **29.4.0**, **amd64**. Containerlab is **not installed** yet.
The lab is **not deployed**. The agent is **not live**. kubectl is
irrelevant until the agent lands.

---

## 0. License and image (read this first)

cEOS is **Arista-licensed**. You must already be allowed to run the
official lab image on Viper. This git repo does **not** store the
tarball and does not add Docker credentials.

**Do not `docker pull`.** Do not use a Hub image. Import the official
file Arista published:

```bash
docker import cEOS64-lab-4.33.9M.tar.xz ceos:4.33.9M
```

That local name **`ceos:4.33.9M`** (`linux/amd64`) is the default in
[clab/topology.yml](clab/topology.yml). Scripts fail if it is missing
and print the import command above. They will not pull.

Override (local name only — any one is enough):

```bash
# A. environment
export CEOS_IMAGE=ceos:4.33.9M

# B. .env (gitignored)
cp arista-ceos-sandbox-agent/.env.example arista-ceos-sandbox-agent/.env
# edit CEOS_IMAGE=   (still a local docker image name)

# C. YAML
# change kinds.arista_ceos.image in clab/topology.yml
```

---

## 1. Why three switches and eBGP (not MPLS)

v1 needs a fabric an agent can **read** later: hostnames, BGP state,
loopback reachability, LLDP. eBGP on point-to-point `/31`s is widely
supported on cEOS and is the usual underlay before EVPN.

ASNs and loopbacks (also on the README):

| Node | ASN | Loopback0 |
|------|-----|-----------|
| spine1 | 65000 | 10.255.0.1/32 |
| leaf1 | 65101 | 10.255.0.11/32 |
| leaf2 | 65102 | 10.255.0.12/32 |

Links: spine1 `eth1` ↔ leaf1 `eth1` (`10.0.1.0/31`); spine1 `eth2` ↔
leaf2 `eth1` (`10.0.2.0/31`). Linux `ethN` is EOS `EthernetN`.

Planned management pool: **`172.20.20.0/24`**. Do not hardcode
per-node Management0 addresses.

No Alpine clients. A host ping to a loopback would need extra routing
or extra NICs; EOS-to-EOS ping is the check.

---

## 2. Lab-only credentials (not Vault yet)

Containerlab’s `arista_ceos` kind normally creates `admin`/`admin` and
enables eAPI. A **custom startup-config replaces that file**, so
`scripts/01-deploy.sh` injects AAA when it renders
`clab/generated/*.cfg` (gitignored).

1. Copy [`.env.example`](.env.example) to `.env` on Viper.
2. Leave the Containerlab defaults, or put another **lab-only**
   alphanumeric user/password in `.env`.
3. Never commit `.env`. Never paste the password into git, chat, or
   screenshots.

When the kagent MCP is added, it must read Vault
`secret/platform/arista-ceos` (key **names** only in git:
`username`, `password`, `hosts_json`). `hosts_json` is a JSON list of
discovered eAPI endpoints — not a single `host` key. Do not copy
`.env` into a cluster Secret manifest.

---

## 3. Prerequisites

On Viper, from this folder:

```bash
cd arista-ceos-sandbox-agent
./scripts/00-prereqs.sh
```

You want `docker` (already **29.4.0** on Viper), `python3`, the local
image **`ceos:4.33.9M`**, and `containerlab` (or `clab`).

**Containerlab is not installed on Viper yet.** The prereq script
reports `MISS containerlab` until you install it from
https://containerlab.dev. Deploy will also fail without it.

Missing `ceos:4.33.9M` is a hard fail with the `docker import`
command. There is no Hub fallback.

cEOS boot is heavy. Plan on the order of **2 GB RAM per node** and a
few minutes after `containerlab deploy` before eAPI answers.

---

## 4. Deploy

Not run yet. After containerlab is installed and `ceos:4.33.9M`
exists locally:

```bash
./scripts/01-deploy.sh
```

What that does, in order:

1. Renders `clab/generated/{spine1,leaf1,leaf2}.cfg` from
   `clab/configs/*.cfg.tmpl` (AAA from `.env` or Containerlab
   defaults; password not printed).
2. Writes `clab/generated/topology.yml` with `CEOS_IMAGE` applied.
3. Refuses to continue if `ceos:4.33.9M` (or your override) is not a
   local image — no `docker pull`.
4. `containerlab deploy -t clab/generated/topology.yml --reconfigure`
   so an old lab directory cannot shadow the rendered startup-config.
5. Waits up to five minutes for HTTP eAPI `show hostname` on each
   node’s Docker IPv4 (from the `172.20.20.0/24` pool, not hardcoded).

`--reconfigure` destroys an existing lab of the same name. That is
intentional for a disposable fabric.

---

## 5. Verify (live output only)

```bash
./scripts/02-verify.sh
```

The script must be run against a real lab. It checks:

1. All three containers running (`clab-arista-ceos-{spine1,leaf1,leaf2}`).
2. eAPI HTTP `show hostname` / `show version` on each mgmt IPv4.
3. BGP **Established** on both spine–leaf sessions (and the leaf side
   of each).
4. Loopback pings via `Cli` (spine ↔ leaves, and leaf1 ↔ leaf2 via
   the spine).
5. LLDP neighbors on the two point-to-point links.

It prints the Cli/eAPI text it got. If a session is Idle, the script
**fails** and shows that state. Do not replace a failure with a
hand-written “Established” block in REPORT.md.

---

## 6. Destroy

```bash
./scripts/03-destroy.sh
```

Removes the Containerlab lab and containers. Generated configs stay
on disk (they contain lab AAA). Delete them locally if you want:

```bash
rm -f clab/generated/*.cfg clab/generated/topology.yml
```

---

## 7. What you should see when it is actually up

After a successful verify — and only then — you may record in
REPORT.md:

- container names and `docker inspect` mgmt IPs
- EOS version strings from eAPI
- BGP neighbor states
- ping success/fail lines
- LLDP neighbor names

Until that run exists, REPORT.md stays **NOT YET RUN**. Shot slots
stay empty ([shots/NOTES.md](shots/NOTES.md) only).

Intended later chat (do not pretend it works today):

> Which BGP sessions are up, and can leaf1 reach leaf2’s loopback?

Skills for that future agent: [skills/SKILL.md](skills/SKILL.md)
(`arista_*` tools). Read-only. Never invent a neighbor.

---

## Secrets

| Where | What is allowed in git |
|-------|------------------------|
| `.env.example` | Local image name; lab-only placeholder user/password **example** |
| `.env` | Local only (gitignored) |
| Vault (later) | Path `secret/platform/arista-ceos` — keys `username`, `password`, `hosts_json` |
| Screenshots | No password, no `Authorization` header, no `vault kv put` values |

---

## What this journey does not do

- No kagent / Substrate version bump
- No `SandboxAgent` apply (agent is not live)
- No MCP image build
- No EVPN, VXLAN, or MPLS
- No Linux clients
- No Hub `docker pull`
- No claim that verify has passed on Viper
- No reconstructed or AI screenshots
