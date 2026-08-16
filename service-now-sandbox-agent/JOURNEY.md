# Journey: ServiceNow SandboxAgent on Viper

**Visual start:** [README.md](README.md) (architecture + shot
placeholders). This file is the how-to. Copy-paste without the story
is [docs/cli-runbook.md](docs/cli-runbook.md).

You are building a **gVisor-sandboxed** manager assistant that can
answer *“what IT tickets are open, and how should we organize them?”*
without holding a ServiceNow password in git and without a generic
shell.

Lab: Sebastian’s Viper, `172.16.10.135`, dockerized k3s (`k3s-viper`).
kubectl is `docker exec k3s-viper kubectl …`.

---

## 1. Why Substrate (isolated sandboxes, not a plain Agent)

A normal kagent `Agent` is a Kubernetes Deployment: always on, same
isolation as any other pod. Fine for a cluster helper.

This `servicenow` agent talks to a ServiceNow instance. The model gets
a filesystem, memory, and a network for the whole chat. Substrate puts
that session in a **gVisor actor** (`SandboxAgent`) on WorkerPool
`kagent-default`:

- **Isolated sandbox:** gVisor is the wall between the model session
  and the Viper/k3s host. Tools still call ServiceNow through the MCP
  pod; username/password stay in Vault, not in the actor.
- Idle chats **snapshot** (zstd) and free the worker. The next
  message restores the same session instead of booting a new
  container.
- No always-on pod per manager conversation.
- A **golden snapshot** you can resume.

**Tradeoff on this lab (honest):** nested gVisor on dockerized k3s,
and snapshots are in-cluster rustfs today (`gs://` is a URI prefix
only), not GCS.

These are isolated sandboxes, not plain Agents. The kagent UI shows a
**Sandbox: Agent Substrate** badge. Classic `/api/a2a/<ns>/<name>`
**404s** because there is no `Agent` CR; the UI uses
`/api/a2a-sandboxes/kagent/servicenow`.

If you only needed a Python container with `httpx` and no snapshot
lifecycle, a Deployment would be enough. That is **not** this demo.

**What you should already see on Viper** (proof the runtime exists):

```bash
docker exec k3s-viper kubectl -n kagent get sandboxagents,workerpool
docker exec k3s-viper kubectl -n ate-system get pods
```

`hello-substrate` / `fortigate` / `aws-budget` Ready means the pairing
below works. If they are not Ready, fix the lab first — do not add
another agent on a broken control plane.

---

## 2. Why 0.10.0-rc2 + 0.0.9 (and not 0.0.12)

Official published pairing:

| kagent | Substrate |
|--------|-----------|
| Helm/CRDs **0.10.0-rc2** | Helm/CRDs **0.0.9** |
| `go.mod` replace `substrate v0.0.9` | Worker `ateom-gvisor:v0.0.9` |

kagent rc2 **always** writes `ActorTemplate` with:

- `spec.pauseImage`
- `env[].valueFrom.secretKeyRef` (`KAGENT_CONFIG_JSON`,
  `KAGENT_AGENT_CARD_JSON`, `KAGENT_SRT_SETTINGS_JSON`, `OPENAI_API_KEY`)

Substrate **0.0.9** CRDs accept that. **0.0.12** removed `valueFrom`
and moved pause image to `SandboxConfig`. The apiserver then rejects
rc2’s object (`Ready=False`, `ActorTemplateNotFound`, or
`spec.containers[0].env[…].value: Required value`).

**Do not bump** either version to “fix” Ready. **Do not** edit the
SandboxAgent YAML to flatten env into literals. Pin mismatch is a
CRD problem.

Why this matters: the first time `servicenow` is not Ready, you will
be tempted to upgrade. That is how Viper already burned time. Stay on
0.0.9.

---

## 3. Snapshots today: rustfs (omit snapshotsConfig)

Substrate checkpoints actor RAM/filesystem to **object storage**.
On live Viper that storage is **in-cluster rustfs**, not Google Cloud.

| | Today on Viper |
|--|--|
| atelet 0.0.9 | `ATE_STORAGE_BACKEND=s3` → `http://rustfs.ate-system.svc:9000` |
| rustfs bucket | `ate-snapshots` (1Gi PVC) |
| hello-substrate / fortigate / aws-budget | **omit** `snapshotsConfig` |
| kagent default | ActorTemplate location `gs://ate-snapshots/kagent/<name>` |
| Where bytes live | rustfs. The `gs://` scheme is a **prefix only**. |

`k8s/sandboxagent.yaml` therefore **omits** `snapshotsConfig`, same as
the live agents. Expected default:

`gs://ate-snapshots/kagent/servicenow`

**Do not** set `gs://viper-kagent-ate-snapshots/...` on this agent.
atelet would look for that bucket **on rustfs**, it does not exist, and
the golden snapshot would fail. **No `ignoreDifferences`.**

**What you should see after apply:**

```bash
docker exec k3s-viper kubectl -n kagent get actortemplate servicenow \
  -o jsonpath='{.spec.snapshotsConfig.location}{"\n"}{.status.goldenSnapshot}{"\n"}'
docker exec k3s-viper kubectl -n ate-system get pods,svc
```

Location is `gs://ate-snapshots/kagent/servicenow`. `goldenSnapshot` is
that prefix plus `/<actorId>/<timestamp>-<rand>` when Ready. rustfs is
up in `ate-system`.

---

## 4. ServiceNow personal developer instance (host only in git)

The instance host name (not a secret) is:

`https://dev203166.service-now.com`

Username and password live in Vault only. Git has the host name and
the Vault **key names** (`host`, `username`, `password`).

**Click path:** open the PDI → confirm you can list **Incidents**.
Prefer a dedicated integration user if you can create one (read
`incident` / `sc_req_item`, write work notes + assign). Do not put
that password in this repo.

**Why a dedicated identity:** the agent is read-mostly. It must not
share an unrelated admin session. The MCP tools cannot create, close,
or delete incidents. Writes are work note and assign only, and the
prompt says **ask first**.

---

## 5. Put credentials in Vault, never git

On Viper, Vault UI is [http://172.16.10.135:30200/](http://172.16.10.135:30200/)
(unseal first if the pod restarted).

```bash
docker exec -it k3s-viper kubectl -n vault exec -i vault-0 -- \
  vault kv put secret/platform/servicenow \
    host='https://dev203166.service-now.com' \
    username='<paste>' \
    password='<paste>'
```

**What you should see:** `created` / a new version of
`secret/data/platform/servicenow`. Then:

```bash
docker exec k3s-viper kubectl -n kagent get externalsecret servicenow-mcp
```

After `kubectl apply`, `STATUS` should become `SecretSynced`. The
Kubernetes Secret `servicenow-mcp` appears. **Do not** `kubectl get
secret -o yaml` and paste it into Slack.

**Why Vault:** ESO already exists on Viper
(`ClusterSecretStore/vault-backend`). FortiGate and aws-budget use the
same pattern. Git only has the ExternalSecret *mapping*.

---

## 6. Build and import the MCP image on k3s

Same local-import pattern as `aws-budget-mcp:dev` / `fortigate-mcp:dev`.
There is no registry pull for `servicenow-mcp:dev`.

On Viper, from this repo root:

```bash
./service-now-sandbox-agent/scripts/02-build-import-mcp.sh
```

**What you should see:** a docker build, then `ctr images import`
listing `servicenow-mcp:dev`. If the pod is `ImagePullBackOff`, the
import did not land or the tag does not match.

**Why import:** dockerized k3s does not see host Docker images until
you `ctr images import`. `imagePullPolicy: IfNotPresent` is
intentional.

---

## 7. Apply SandboxAgent + RemoteMCPServer

```bash
kubectl kustomize service-now-sandbox-agent/k8s | docker exec -i k3s-viper kubectl apply -f -
```

**What you should see:**

```text
externalsecret.external-secrets.io/servicenow-mcp created
deployment.apps/servicenow-mcp created
service/servicenow-mcp created
configmap/servicenow-skills created
remotemcpserver.kagent.dev/servicenow-mcp created
sandboxagent.kagent.dev/servicenow created
```

Then:

```bash
docker exec k3s-viper kubectl -n kagent get sandboxagents,remotemcpservers
docker exec k3s-viper kubectl -n kagent get deploy,pods -l app.kubernetes.io/name=servicenow-mcp
```

MCP pod `1/1 Ready`. `RemoteMCPServer` Accepted. `SandboxAgent`
may sit NotReady for a minute.

---

## 8. Chat in the kagent UI

1. Open [http://172.16.10.135:30500/](http://172.16.10.135:30500/).
2. Pick **kagent/servicenow** (not hello-substrate, not fortigate, not
   aws-budget).
3. Ask:

   > What IT tickets are open, and how should we organize them?

**What you should see:** tool calls — at least `sn_whoami`,
`sn_incident_summary`, `sn_list_incidents`. Incident numbers and
counts that match `scripts/03-smoke-servicenow.sh` when that script
has credentials in the caller env.

**If the model invents tickets:** the tools did not run or the Table
API is denied. Say “call the tools; do not estimate.” Check MCP logs:

```bash
docker exec k3s-viper kubectl -n kagent logs deploy/servicenow-mcp
```

The process must never print the password.

---

## 9. What “Ready / ActorTemplate golden snapshot” means

kagent does not run your Go agent by starting a Deployment of the
LLM runtime. It creates an `ActorTemplate` (owned by the SandboxAgent).
Substrate boots a **golden** actor once, checkpoints it, and stores
that checkpoint as `status.goldenSnapshot`.

| You see | Meaning |
|---------|---------|
| `ActorTemplate` missing | CRD pin wrong (0.0.12) or controller not reconciling |
| Template exists, no `goldenSnapshot` | First checkpoint still running (60–90s is normal) or gVisor/atelet cannot write storage |
| `Ready=True` + `goldenSnapshot: gs://…` | New chats restore from that image; you can talk |

```bash
docker exec k3s-viper kubectl -n kagent get actortemplates
docker exec k3s-viper kubectl -n kagent get sandboxagent servicenow
```

Nested gVisor on dockerized k3s can still fail (`runsc`). That is a
known Viper risk. It does not mean you should convert this to a plain
Agent.

---

## 10. How we will record the video (UI + CLI)

Record two panes. **Redact** Vault tokens and the ServiceNow password.

**CLI reel:**

1. `scripts/00-prereqs.sh` — tools present, cluster reachable.
2. Vault `kv put` with the password **off screen** or `***`.
3. `scripts/02-build-import-mcp.sh`.
4. `kubectl apply` + `get sandboxagent -w` until Ready.
5. `scripts/03-smoke-servicenow.sh` so the UI numbers have a ground
   truth (only if credentials are in the caller env; never `bash -x`).

**UI reel:**

1. ServiceNow PDI incident list (no password on camera).
2. kagent `:30500` → Agents → `servicenow` Ready.
3. The open-tickets question → tool calls → manager-shaped answer.

Clicks-only checklist: [docs/ui-runbook.md](docs/ui-runbook.md).

---

## Skills (in this repo)

All agent skills live under [skills/](skills/SKILL.md). kagent
**0.10.0-rc2** rejects `spec.skills` on `SandboxAgent` (same as
`fortigate` / `hello-substrate` / `aws-budget` — those agents inline
instructions in `systemMessage`). There is no skill-mount into the
gVisor session. ConfigMap `servicenow-skills` holds the same text;
`declarative.promptTemplate` includes it in `systemMessage` so the
model actually sees it. Keep `skills/` in sync with
`k8s/skills-configmap.yaml`. Do not add a second skill pack in
another repository for this demo.
