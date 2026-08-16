# Journey: AWS budget SandboxAgent on Viper

This is the human path. Do it in order. Each step says **what you type
or click**, **what you should see**, and **why it matters**. Copy-paste
without the story is [docs/cli-runbook.md](docs/cli-runbook.md).

You are building a **gVisor-sandboxed** executive assistant that can
answer *“what’s our us-east-2 spend this month and are we over
capacity?”* without holding AWS keys in git and without a generic
shell to the AWS CLI.

Lab: Sebastian’s Viper, `172.16.10.135`, dockerized k3s (`k3s-viper`).
kubectl is `docker exec k3s-viper kubectl …`.

---

## 1. Why Substrate (gVisor sandbox) vs a plain Agent Deployment

A normal kagent `Agent` is a Kubernetes Deployment: one pod, always
on, same isolation as any other container. That is fine for a cluster
helper that only talks to the API server.

This agent talks to **your AWS bill**. The model will call tools. Tools
are code we wrote, but the session still has memory, a filesystem, and
a network. Substrate puts that session in a **gVisor actor** on
WorkerPool `kagent-default`:

- Idle chats **snapshot** (zstd) and free the worker. You are not
  paying a pod per executive conversation.
- Resume is restore, not “boot a new container and hope the prompt is
  the same.”
- gVisor is the isolation boundary between the actor and the k3s host.

If you only needed a Python container with boto3 and no snapshot
lifecycle, a Deployment would be enough. That is **not** this demo.

**What you should already see on Viper** (proof the runtime exists):

```bash
docker exec k3s-viper kubectl -n kagent get sandboxagents,workerpool
docker exec k3s-viper kubectl -n ate-system get pods
```

`hello-substrate` and `fortigate` Ready means the pairing below works.
If they are not Ready, fix the lab first — do not add a third agent on
a broken control plane.

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

Why this matters: the first time `aws-budget` is not Ready, you will
be tempted to upgrade. That is how Viper already burned time. Stay on
0.0.9.

---

## 3. Use the existing GCP project + GCS bucket for snapshots

Substrate checkpoints actor RAM/filesystem to **object storage**.
The Viper lab already has that storage in GCP — **do not create a new
project or bucket**.

| | |
|--|--|
| Org | **maniak.io** |
| Project | **viper-kagent** (number **89434469276**) |
| Bucket | **gs://viper-kagent-ate-snapshots** |
| Location | **us-east1** |

**Click path** (also in [docs/ui-runbook.md](docs/ui-runbook.md)):

1. [Google Cloud console](https://console.cloud.google.com/) → project
   picker → select **viper-kagent** (not **New project**).
2. Cloud Storage → Buckets → confirm **viper-kagent-ate-snapshots**
   in **us-east1**, public access prevented.
3. The kagent URI is already set in `k8s/sandboxagent.yaml`:
   `gs://viper-kagent-ate-snapshots/kagent/aws-budget/`.

**CLI path** (defaults to the existing project + bucket; skips create):

```bash
./scripts/01-gcp-snapshot-bucket.sh
```

**What you should see:** project `viper-kagent`, bucket
`gs://viper-kagent-ate-snapshots`, and `existing lab … — skip create`.

**Why this project:** blast radius. Snapshot objects are sandbox
memory. They stay in the dedicated `viper-kagent` project, and this
agent’s AWS IAM must not include `s3:*` on customer buckets.

---

## 4. Point Substrate snapshots at that bucket

There are **two layers**. Read [docs/snapshots-gcs.md](docs/snapshots-gcs.md)
before you invent Helm values.

### Layer 1 — the string kagent writes (this we set)

kagent 0.10.0-rc2 `SandboxAgent.spec.substrate.snapshotsConfig.location`
is documented as a **GCS URI**, validation `^gs://`, default
`gs://ate-snapshots/<namespace>/<name>/`.

`k8s/sandboxagent.yaml` already points at the lab bucket:

```yaml
snapshotsConfig:
  location: gs://viper-kagent-ate-snapshots/kagent/aws-budget/
```

**What you should see after apply:**

```bash
docker exec k3s-viper kubectl -n kagent get actortemplate aws-budget \
  -o jsonpath='{.spec.snapshotsConfig.location}{"\n"}{.status.goldenSnapshot}{"\n"}'
```

Location is your prefix. `goldenSnapshot` is that prefix plus
`/<actorId>/<timestamp>-<rand>` when Ready.

### Layer 2 — what atelet actually speaks (inspect, don’t guess)

Published Substrate docs: atelet picks **GCS or S3 at process start**,
not per snapshot. Older kagent blog posts (0.0.6 / 0.0.8) show an
in-cluster **rustfs** pod as “S3 for snapshots.” Viper’s 0.0.9
`values.yaml` does **not** mention rustfs. Confirm:

```bash
docker exec k3s-viper kubectl -n ate-system get pods,svc
```

| If you see… | Then… |
|-------------|--------|
| No rustfs; atelet has GCS/ADC credentials | Path A: native `gs://` to `gs://viper-kagent-ate-snapshots` |
| rustfs (or atelet env is AWS/S3) | Path B: GCS **XML/S3 interop** — HMAC keys, endpoint `https://storage.googleapis.com`. **Still** set location to `gs://…` because the kagent CRD rejects `s3://`. |

**Why this split exists:** kagent’s CRD and atelet’s client were not
the same document. We document both so you do not force `s3://` into
a field that cannot hold it.

---

## 5. Create the AWS IAM user / role for the agent

**Click path:** AWS console, region **us-east-2** → IAM → create user
`aws-budget-agent` (no console password) → attach the customer-managed
policy in [docs/security.md](docs/security.md) → create an access key
(use case: “Application running outside AWS”).

**What you should see:** Access key id starting with `AKIA…` and a
secret shown **once**.

**Why a dedicated identity:** the agent is read-mostly. It must not
share a human admin key. The policy is `ce:Get*`, `budgets:View*`,
`ec2:Describe*` (and siblings) **conditioned to us-east-2** where
IAM allows it. No terminate, no IAM create, no `s3:*` on your data.

Enable **Cost Explorer** in the billing console if the account has
never used it. Otherwise `aws_cost_*` will fail honestly — that is
success, not a reason to fake $0.

Optional: enroll Compute Optimizer / CE rightsizing. If you skip it,
`aws_rightsizing_hints` must say “not available.”

---

## 6. Put keys in Vault, never git

On Viper, Vault UI is [http://172.16.10.135:30200/](http://172.16.10.135:30200/)
(unseal first if the pod restarted).

```bash
docker exec -it k3s-viper kubectl -n vault exec -i vault-0 -- \
  vault kv put secret/platform/aws-budget \
    access_key_id='<paste>' \
    secret_access_key='<paste>' \
    region='us-east-2'
```

**What you should see:** `created` / a new version of
`secret/data/platform/aws-budget`. Then:

```bash
docker exec k3s-viper kubectl -n kagent get externalsecret aws-budget-mcp
```

After `kubectl apply`, `STATUS` should become `SecretSynced`. The
Kubernetes Secret `aws-budget-mcp` appears. **Do not** `kubectl get
secret -o yaml` and paste it into Slack.

**Why Vault:** ESO already exists on Viper
(`ClusterSecretStore/vault-backend`). FortiGate uses the same pattern
(`secret/platform/fortigate`). Git only has the ExternalSecret
*mapping*.

---

## 7. Build and import the MCP image on k3s

Same local-import pattern as `fortigate-mcp:dev`. There is no registry
pull for `aws-budget-mcp:dev`.

On Viper, from this repo root:

```bash
./aws-sandbox-agent/scripts/02-build-import-mcp.sh
```

**What you should see:** a docker build, then `ctr images import`
listing `aws-budget-mcp:dev`. If the pod is `ImagePullBackOff`, the
import did not land or the tag does not match.

**Why import:** dockerized k3s does not see host Docker images until
you `ctr images import`. `imagePullPolicy: IfNotPresent` is
intentional.

---

## 8. Apply SandboxAgent + RemoteMCPServer

```bash
kubectl kustomize aws-sandbox-agent/k8s | docker exec -i k3s-viper kubectl apply -f -
```

**What you should see:**

```text
externalsecret.external-secrets.io/aws-budget-mcp created
deployment.apps/aws-budget-mcp created
service/aws-budget-mcp created
remotemcpserver.kagent.dev/aws-budget-mcp created
sandboxagent.kagent.dev/aws-budget created
```

Then:

```bash
docker exec k3s-viper kubectl -n kagent get sandboxagents,remotemcpservers
docker exec k3s-viper kubectl -n kagent get deploy,pods -l app.kubernetes.io/name=aws-budget-mcp
```

MCP pod `1/1 Ready`. `RemoteMCPServer` Accepted. `SandboxAgent`
may sit NotReady for a minute.

---

## 9. Chat in the kagent UI

1. Open [http://172.16.10.135:30500/](http://172.16.10.135:30500/).
2. Pick **kagent/aws-budget** (not hello-substrate, not fortigate).
3. Ask:

   > What's our us-east-2 spend this month and are we over capacity?

**What you should see:** tool calls — at least `aws_whoami`,
`aws_cost_month`, `aws_ec2_capacity` (or the composed
`aws_executive_brief`). Dollars and instance counts that match
`scripts/03-smoke-aws.sh` on your laptop.

**If the model invents spend:** the tools did not run or CE is denied.
Say “call the tools; do not estimate.” Check MCP logs:

```bash
docker exec k3s-viper kubectl -n kagent logs deploy/aws-budget-mcp
```

The process must never print the secret key.

---

## 10. What “Ready / ActorTemplate golden snapshot” means

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
docker exec k3s-viper kubectl -n kagent get sandboxagent aws-budget
```

Nested gVisor on dockerized k3s can still fail (`runsc`). That is a
known Viper risk. It does not mean you should convert this to a plain
Agent.

---

## 11. How we will record the video (UI + CLI)

Record two panes. **Redact** Vault tokens, AWS secrets, HMAC secrets.

**CLI reel (about two minutes):**

1. `scripts/00-prereqs.sh` — tools present, cluster reachable.
2. `scripts/01-gcp-snapshot-bucket.sh` — show the existing
   `gs://viper-kagent-ate-snapshots/kagent/aws-budget/` URI
   (create is skipped; the project and bucket already exist).
3. Vault `kv put` with the secret **off screen** or `***`.
4. `scripts/02-build-import-mcp.sh`.
5. `kubectl apply` + `get sandboxagent -w` until Ready.
6. `scripts/03-smoke-aws.sh` so the UI numbers have a ground truth.

**UI reel:**

1. GCP console: project **viper-kagent** + bucket
   **viper-kagent-ate-snapshots** (already exist — do not create).
2. AWS IAM policy attach (no key download on camera).
3. kagent `:30500` → Agents → `aws-budget` Ready.
4. The spend/capacity question → tool calls → executive-shaped answer.

Clicks-only checklist: [docs/ui-runbook.md](docs/ui-runbook.md).

---

## Skills (in this repo)

All agent skills live under [skills/](skills/SKILL.md). The system
message points at them. Do not add a second skill pack in another
repository for this demo.
