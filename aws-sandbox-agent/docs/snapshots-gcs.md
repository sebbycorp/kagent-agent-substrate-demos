# Substrate snapshots → GCS (existing viper-kagent project)

The Viper lab already has a GCS bucket in GCP project **viper-kagent**,
usable the way people use S3. **Do not create a new project or bucket.**

| | |
|--|--|
| Org | **maniak.io** |
| Project | **viper-kagent** (number **89434469276**) |
| Bucket | **gs://viper-kagent-ate-snapshots** |
| Location | **us-east1** |

This file records what the **published** kagent 0.10.0-rc2 / Substrate
0.0.9 docs actually say. Nothing here is inferred from a later chart.

## What I verified (do not invent past this)

### 1. kagent writes `gs://` and validates `^gs://`

From the kagent API reference
([AgentHarnessSubstrateSnapshotsConfig](https://kagent.dev/docs/kagent/resources/api-ref/)):

- *“Substrate currently expects a gs:// location (see Agent Substrate SnapshotsConfig).”*
- `location` is *“the GCS URI prefix for golden and incremental snapshots.”*
- Example: `gs://ate-snapshots/kagent/my-namespace/my-harness/`
- Validation **pattern: `^gs://`**
- When unset, default is `gs://ate-snapshots/<namespace>/<name>/`

`SandboxAgent.spec.substrate.snapshotsConfig` uses **that same type**
(`SandboxSubstrateSpec` in the same API ref). So a SandboxAgent on
0.10.0-rc2 **cannot** set `s3://…` on this field — admission will reject it.

This demo therefore sets:

```yaml
spec:
  substrate:
    workerPoolRef:
      name: kagent-default
    snapshotsConfig:
      location: gs://viper-kagent-ate-snapshots/kagent/aws-budget/
```

The `gs://` scheme is required. The bucket already exists; do not
substitute a placeholder or create a second one.

### 2. Substrate 0.0.9 ActorTemplate uses the same prefix shape

From [ActorTemplate](https://learn.agentsubstrate.dev/concepts/actortemplate/):

- `spec.snapshotsConfig.location` is **required** — *“the object-store prefix snapshots are written to.”*
- Official example: `gs://ate-snapshots/kagent/hello-substrate`
- Ready status shows `goldenSnapshot: gs://ate-snapshots/kagent/hello-substrate/<actorId>/<timestamp>-<rand>`

From [Storage](https://learn.agentsubstrate.dev/components/storage):

```text
<ActorTemplate.spec.snapshotsConfig.location>/<actorName>/<RFC3339-timestamp>-<random>/
  <snapshot-file>.zstd
  manifest.json
```

*“`spec.snapshotsConfig.location` is whatever the template provides
(e.g. `gs://my-bucket/some/prefix`); ateapi appends `/<actorName>/<timestamp>-<random>/`.”*

Also: *“Both back-ends implement the same internal object interface.
The choice is environmental — GCS in GCP, S3 in AWS — **selected at
atelet startup, not per snapshot**.”*

So: **location string** (kagent CRD) and **atelet client** (GCS vs S3)
are two different knobs.

### 3. Stock substrate Helm often includes rustfs (in-cluster S3)

I could not pull `oci://ghcr.io/kagent-dev/substrate/helm/substrate:0.0.9`
in this environment (no Helm; CNCF GHCR blocked the GitHub token).

What **is** published:

- kagent blog *[Deploy kagent with Agent Substrate](https://kagent.dev/blog/deploy-kagent-with-agent-substrate)*
  (chart pin in that post: **0.0.8**) lists an `ate-system` pod
  **`rustfs` — “In-cluster S3 for snapshots.”**
- Sebastian's kind write-up
  ([maniak.io, Substrate 0.0.6](https://maniak.io/articles/2026-06-25-kagent-agent-substrate-suspend-resume-kind/))
  lists the same `rustfs` role.

What **k8s-viper** (0.0.9, the lab this demo targets) does **not** do:

- `platform/substrate-app/values.yaml` only sets `valkey.replicas: 6`.
  It does **not** override snapshot storage, rustfs, or a GCS endpoint.
- `platform/kagent/values.yaml` does **not** set `snapshotsConfig`.

So on Viper today, kagent will default the ActorTemplate location to
`gs://ate-snapshots/kagent/<name>/` unless we set it. Whether **bytes**
leave the cluster depends on whether 0.0.9 still runs rustfs and whether
atelet is in S3 or GCS mode. **Confirm on the live cluster** — do not
assume from the 0.0.6/0.0.8 blog posts:

```bash
docker exec k3s-viper kubectl -n ate-system get pods,svc
docker exec k3s-viper kubectl -n ate-system get deploy,sts -o name
docker exec k3s-viper kubectl -n kagent get actortemplate hello-substrate \
  -o jsonpath='{.spec.snapshotsConfig.location}{"\n"}{.status.goldenSnapshot}{"\n"}'
```

If you see a `rustfs` Service and `goldenSnapshot` still `gs://ate-snapshots/...`,
that is the split-brain the two layers allow: **URI says GCS, client may be S3**.

## Path A — native `gs://` (what the kagent CRD wants)

Use this when atelet is (or will be) the **GCS** client.

1. Confirm the existing project + bucket ([ui-runbook.md](ui-runbook.md)
   or `scripts/01-gcp-snapshot-bucket.sh` — it skips create when they
   already exist).
2. Give atelet a Google identity that can `storage.objects.create/get/delete`
   on `gs://viper-kagent-ate-snapshots` (Workload Identity, or a SA JSON
   in a Secret — **not git**).
3. `k8s/sandboxagent.yaml` already sets
   `snapshotsConfig.location: gs://viper-kagent-ate-snapshots/kagent/aws-budget/`.
4. Ready looks like:

   `status.goldenSnapshot: gs://viper-kagent-ate-snapshots/kagent/aws-budget/<id>/<time>-<rand>`

I did **not** find a published 0.0.9 Helm values key that switches atelet
from rustfs to GCS. Do not invent `objectStorage.type=gcs` in a values
file. Change only what you can see on the live Deployment/DaemonSet
(`atelet` env / volume mounts) after you inspect it.

## Path B — GCS S3-compatible XML API (HMAC)

Official GCS docs:

- Interop endpoint: **`https://storage.googleapis.com`**
  ([Interoperability](https://cloud.google.com/storage/docs/interoperability))
- Auth: **HMAC keys** (Access ID + Secret), XML API only
  ([HMAC keys](https://cloud.google.com/storage/docs/authentication/hmackeys))

Use this when you have confirmed atelet is the **S3** client (rustfs-style
env: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_ENDPOINT` /
`AWS_ENDPOINTS` or similar — **read the live atelet pod**, do not guess
the key names from Longhorn blogs).

Then:

1. Same existing project + bucket as Path A (`viper-kagent` /
   `gs://viper-kagent-ate-snapshots`). Do not create another.
2. Service account with object admin on **that bucket only**.
3. Cloud Storage → Settings → Interoperability → HMAC key for that SA.
4. Point atelet’s S3 endpoint at `https://storage.googleapis.com`.
5. Put HMAC id/secret in Vault. **Never git.**
6. **Keep** `snapshotsConfig.location` as
   `gs://viper-kagent-ate-snapshots/kagent/aws-budget/`.
   The kagent CRD will not accept `s3://`.

If atelet requires `s3://` in the *template* location, that would be a
Substrate-side field, not the kagent SandboxAgent field. On 0.10.0-rc2
kagent owns the ActorTemplate; do not hand-edit it to paper over a
mismatch (same rule as `valueFrom` vs 0.0.12).

## Wire-in checklist

| Step | Where |
|------|--------|
| Confirm existing project + bucket | `scripts/01-gcp-snapshot-bucket.sh` (skips create) or GCP console |
| Set location on the agent | `k8s/sandboxagent.yaml` → `spec.substrate.snapshotsConfig.location` |
| Confirm scheme | must start with `gs://` |
| Confirm backend | `kubectl -n ate-system get pods` + atelet env |
| Confirm Ready | `ActorTemplate` `status.goldenSnapshot` prefix matches your bucket |
| HMAC only if S3 client | Vault, not `k8s/*.yaml` |

## What this demo will not do

- Bump Substrate past **0.0.9**.
- Commit HMAC secrets, SA JSON, or AWS keys.
- Claim rustfs is definitely in the 0.0.9 chart without a live `get pods`.
- Invent Helm values for atelet that are not in the published 0.0.9 docs.
