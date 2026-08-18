# Journey: Arista cEOS Containerlab fabric on Viper

**Visual start:** [README.md](README.md) (architecture; live shots
pending). **Live lab record:** [REPORT.md](REPORT.md) — template only
until someone actually deploys this on Viper. Do not fill REPORT.md
from memory.

This is the human path for **v1: three cEOS switches, eBGP underlay**.
The gVisor `SandboxAgent` / FastMCP / Vault wiring is **not** in this
folder yet. Do not apply leftover `k8s/` manifests from other demos
and call it this lab.

Lab host: Sebastian’s Viper. Containerlab talks to local Docker. kubectl
is irrelevant until the agent lands.

---

## 0. License and image (read this first)

cEOS is **Arista-licensed**. You must already be allowed to run the
image on Viper. This git repo does **not** store `sebbycorp/ceosimage`
and does not add Docker credentials.

Default image: `sebbycorp/ceosimage:latest`.

Docker Hub tags inspected 2026-08-18:

| Tag | Notes |
|-----|--------|
| `latest` | Default in [clab/topology.yml](clab/topology.yml) |
| `4.33.4M` | Newer published tag; set `CEOS_IMAGE` to use it |

Both published tags were **arm64**. If Viper cannot run arm64 images,
stop and use a host/image pair that matches. Do not retag a foreign
image in this repo.

Override (any one is enough):

```bash
# A. environment (preferred)
export CEOS_IMAGE=sebbycorp/ceosimage:4.33.4M

# B. .env (gitignored)
cp arista-ceos-sandbox-agent/.env.example arista-ceos-sandbox-agent/.env
# edit CEOS_IMAGE=

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
`secret/platform/arista-ceos` (key **names** only in git: `host` /
`username` / `password` or equivalent). Do not copy `.env` into a
cluster Secret manifest.

---

## 3. Prerequisites

On Viper, from this folder:

```bash
cd arista-ceos-sandbox-agent
./scripts/00-prereqs.sh
```

You want `docker`, `python3`, and `containerlab` (or `clab`). The
script prints the image **name**, not a digest dump of the tarball.
Missing image is a warning; deploy will `docker pull` if you are
allowed to.

cEOS boot is heavy. Plan on the order of **2 GB RAM per node** and a
few minutes after `containerlab deploy` before eAPI answers.

---

## 4. Deploy

```bash
./scripts/01-deploy.sh
```

What that does, in order:

1. Renders `clab/generated/{spine1,leaf1,leaf2}.cfg` from
   `clab/configs/*.cfg.tmpl` (AAA from `.env` or Containerlab
   defaults; password not printed).
2. Writes `clab/generated/topology.yml` with `CEOS_IMAGE` applied.
3. `containerlab deploy -t clab/generated/topology.yml --reconfigure`
   so an old lab directory cannot shadow the rendered startup-config.
4. Waits up to five minutes for HTTP eAPI `show hostname` on each
   node’s Docker IPv4.

`--reconfigure` destroys an existing lab of the same name. That is
intentional for a disposable fabric.

Management IPs come from Docker. Do not add `ip address` under
`Management0` unless you have measured that Containerlab will not
assign one.

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

Until that run exists, REPORT.md stays **NOT YET RUN**.

Intended later chat (do not pretend it works today):

> Which BGP sessions are up, and can leaf1 reach leaf2’s loopback?

Skills for that future agent: [skills/SKILL.md](skills/SKILL.md).
Read-only. Never invent a neighbor.

---

## Secrets

| Where | What is allowed in git |
|-------|------------------------|
| `.env.example` | Image name; lab-only placeholder user/password **example** |
| `.env` | Local only (gitignored) |
| Vault (later) | Path `secret/platform/arista-ceos` — **path and key names** only |
| Screenshots | No password, no `Authorization` header, no `vault kv put` values |

---

## What this journey does not do

- No kagent / Substrate version bump
- No `SandboxAgent` apply
- No MCP image build
- No EVPN, VXLAN, or MPLS
- No Linux clients
- No claim that verify has passed on Viper
