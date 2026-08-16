# Substrate snapshots: rustfs today, GCS later

**Today on Viper (read-only, confirmed):** stay on in-cluster **rustfs**.
Do **not** set `snapshotsConfig.location` on `SandboxAgent/aws-budget`.

| | Today |
|--|--|
| atelet 0.0.9 | `ATE_STORAGE_BACKEND=s3` → `http://rustfs.ate-system.svc:9000` |
| rustfs bucket | `ate-snapshots` (1Gi PVC) |
| hello-substrate / fortigate | omit `snapshotsConfig` |
| kagent default | `gs://ate-snapshots/kagent/<name>` |
| Where bytes live | rustfs. `gs://` is a **prefix only**, not Google Cloud. |

Setting `gs://viper-kagent-ate-snapshots/...` on this agent would make
atelet talk to a **rustfs** bucket that does not exist. Golden snapshot
would fail.

## Reserved GCS (do not create, do not wire yet)

These already exist. They are reserved for a **later cluster-wide
atelet cutover** off rustfs. Do not create another project or bucket.
Do not put this URI on the SandboxAgent until atelet is no longer
pointed at rustfs.

| | |
|--|--|
| Org | **maniak.io** |
| Project | **viper-kagent** (number **89434469276**) |
| Bucket | **gs://viper-kagent-ate-snapshots** |
| Location | **us-east1** |

`scripts/01-gcp-snapshot-bucket.sh` verifies that pair and **skips
create**. It does not change the agent YAML.

## What the published docs say (do not invent past this)

### 1. kagent writes `gs://` and validates `^gs://`

From the kagent API reference
([AgentHarnessSubstrateSnapshotsConfig](https://kagent.dev/docs/kagent/resources/api-ref/)):

- *“Substrate currently expects a gs:// location (see Agent Substrate SnapshotsConfig).”*
- `location` is *“the GCS URI prefix for golden and incremental snapshots.”*
- Example: `gs://ate-snapshots/kagent/my-namespace/my-harness/`
- Validation **pattern: `^gs://`**
- When unset, default is `gs://ate-snapshots/<namespace>/<name>/`

`SandboxAgent.spec.substrate.snapshotsConfig` uses **that same type**.
A SandboxAgent on 0.10.0-rc2 **cannot** set `s3://…` — admission will
reject it. This demo therefore **omits** the field (same as
hello-substrate / fortigate) so kagent fills:

```text
gs://ate-snapshots/kagent/aws-budget
```

### 2. Substrate 0.0.9 ActorTemplate uses the same prefix shape

From [ActorTemplate](https://learn.agentsubstrate.dev/concepts/actortemplate/):

- `spec.snapshotsConfig.location` is **required** — *“the object-store prefix snapshots are written to.”*
- Official example: `gs://ate-snapshots/kagent/hello-substrate`
- Ready status shows `goldenSnapshot: gs://ate-snapshots/kagent/hello-substrate/<actorId>/<timestamp>-<rand>`

From [Storage](https://learn.agentsubstrate.dev/components/storage/):

```text
<ActorTemplate.spec.snapshotsConfig.location>/<actorName>/<RFC3339-timestamp>-<random>/
  <snapshot-file>.zstd
  manifest.json
```

*“Both back-ends implement the same internal object interface.
The choice is environmental — GCS in GCP, S3 in AWS — **selected at
atelet startup, not per snapshot**.”*

So: **location string** (kagent CRD) and **atelet client** (GCS vs S3)
are two different knobs. On Viper today the client is S3/rustfs.

### 3. Confirm rustfs (already true on this lab)

```bash
docker exec k3s-viper kubectl -n ate-system get pods,svc
docker exec k3s-viper kubectl -n kagent get actortemplate hello-substrate \
  -o jsonpath='{.spec.snapshotsConfig.location}{"\n"}{.status.goldenSnapshot}{"\n"}'
```

`goldenSnapshot` starting `gs://ate-snapshots/...` while atelet speaks
S3 to rustfs is expected, not a bug.

## Future work only — Path A (native GCS ADC)

Do **not** do this until atelet is switched cluster-wide off rustfs.

1. Confirm the reserved project + bucket
   (`scripts/01-gcp-snapshot-bucket.sh` — skips create).
2. Give atelet a Google identity that can
   `storage.objects.create/get/delete` on
   `gs://viper-kagent-ate-snapshots` (Workload Identity, or a SA JSON
   in a Secret — **not git**).
3. Only then set `snapshotsConfig.location` on agents (or change the
   controller default) to `gs://viper-kagent-ate-snapshots/kagent/<name>/`.
4. Ready would look like:

   `status.goldenSnapshot: gs://viper-kagent-ate-snapshots/kagent/<name>/<id>/<time>-<rand>`

I did **not** find a published 0.0.9 Helm values key that switches atelet
from rustfs to GCS. Do not invent `objectStorage.type=gcs` in a values
file. Change only what you can see on the live Deployment/DaemonSet
(`atelet` env / volume mounts) after you inspect it.

## Future work only — Path B (HMAC + storage.googleapis.com)

Official GCS docs:

- Interop endpoint: **`https://storage.googleapis.com`**
  ([Interoperability](https://cloud.google.com/storage/docs/interoperability))
- Auth: **HMAC keys** (Access ID + Secret), XML API only
  ([HMAC keys](https://cloud.google.com/storage/docs/authentication/hmackeys))

Same reserved project + bucket. Do not create another. Point atelet’s
S3 endpoint at `https://storage.googleapis.com`. Put HMAC in Vault.
**Never git.** The kagent CRD still will not accept `s3://` on
`snapshotsConfig.location`.

This is a **cluster-wide** atelet change, not a per-SandboxAgent
override. Do not set the GCS URI on `aws-budget` while atelet still
targets rustfs.

## Wire-in checklist (today)

| Step | Where |
|------|--------|
| Omit `snapshotsConfig` on the agent | `k8s/sandboxagent.yaml` (match hello-substrate / fortigate) |
| Confirm rustfs | `kubectl -n ate-system get pods,svc` + atelet `ATE_STORAGE_BACKEND=s3` |
| Confirm Ready | `ActorTemplate` `status.goldenSnapshot` starts `gs://ate-snapshots/kagent/aws-budget` |
| Reserved GCS | exists; do not create; do not wire yet |
| Path A / Path B | future cluster-wide cutover only |

## What this demo will not do

- Bump Substrate past **0.0.9**.
- Set `gs://viper-kagent-ate-snapshots` on this SandboxAgent.
- Create a second GCP project or bucket.
- Commit HMAC secrets, SA JSON, or AWS keys.
- Invent Helm values for atelet that are not in the published 0.0.9 docs.
