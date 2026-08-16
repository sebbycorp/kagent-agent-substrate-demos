# UI runbook

Clicks only. Commands live in [cli-runbook.md](cli-runbook.md).
Story + why: [../JOURNEY.md](../JOURNEY.md).

## kagent UI (Viper)

1. Publish Docker NodePort **30500** on the k3s container (already done on Viper).
2. Open [http://172.16.10.135:30500/](http://172.16.10.135:30500/).
3. You should see the kagent Agents list. `hello-substrate` and `fortigate`
   are the existing lab agents — leave them alone.
4. After apply, pick **kagent/aws-budget**.
5. If the agent is grey / not Ready, wait. First **golden snapshot** is
   often 60–90 seconds. Refresh. Ready means `ActorTemplate` exists and
   `status.goldenSnapshot` is set.
6. Ask:

   > What's our us-east-2 spend this month and are we over capacity?

7. You should see tool calls (`aws_cost_month`, `aws_ec2_capacity`, …)
   and a short exec-style answer. If you see invented `$0` with no tool
   call, the model ignored the system message — say “use the tools.”
8. Do not paste AWS keys into the chat box.

## GCP console (new project + bucket)

1. Open [https://console.cloud.google.com/](https://console.cloud.google.com/).
2. Project picker (top bar) → **New project**.
   - Name: something like `ate-snapshots-lab`.
   - Note the **project ID** (not just the name).
3. Billing → link a billing account (GCS needs it).
4. APIs & Services → Enable **Cloud Storage**.
5. Cloud Storage → **Buckets** → **Create**.
   - Name: globally unique, e.g. `ate-snapshots-<project-id>`.
   - Location: a single region you accept (lab often `us-east1`).
   - Prevent public access: keep the default (public access prevented).
6. Copy the bucket name. The kagent field will be
   `gs://<bucket>/kagent/aws-budget/` — see [snapshots-gcs.md](snapshots-gcs.md).

### Optional: HMAC for S3-compatible XML API

Only if you confirmed atelet is using the **S3** client (rustfs path),
not native GCS:

1. IAM → Service accounts → **Create** (`ate-snapshots` is a fine name).
2. Grant **Storage Object Admin** on that bucket only (not the whole org).
3. Cloud Storage → Settings → **Interoperability**.
4. Create an HMAC key **for that service account**.
5. Copy Access ID + Secret **once**. Put them in Vault, not git.
6. Endpoint to document: `https://storage.googleapis.com`
   ([GCS interoperability](https://cloud.google.com/storage/docs/interoperability)).

## AWS console (IAM user for the agent)

1. Open the AWS console in **us-east-2**
   ([https://us-east-2.console.aws.amazon.com/](https://us-east-2.console.aws.amazon.com/)).
2. IAM → Users → **Create user** → `aws-budget-agent`.
   - No console password.
3. Create a customer managed policy from [security.md](security.md)
   (ce:Get*, budgets:View*, describe-only compute). Attach it.
4. Security credentials → **Create access key** → Application running
   outside AWS. Download/copy once.
5. Billing / Cost Explorer: confirm CE is enabled for the account
   (first-time accounts must enable it; otherwise `aws_cost_*` fails honestly).
6. Optional: Cost Explorer → Rightsizing, Compute Optimizer enrollment.
   If not enrolled, the agent must say so.

## Vault UI (optional vs CLI)

1. Open [http://172.16.10.135:30200/](http://172.16.10.135:30200/).
2. Unseal if needed ([k8s-viper vault-eso-setup](https://github.com/sebbycorp/k8s-viper/blob/main/docs/vault-eso-setup.md)).
3. KV → `secret/platform/aws-budget`.
4. Keys (names only in docs): `access_key_id`, `secret_access_key`, `region`.
5. Paste values locally. Never screenshot the secret key.

## What to record on video

1. **CLI**: prereqs, `gcloud` project/bucket (or the script dry-run),
   Vault `kv put` with the secret redacted, `docker build` + `ctr import`,
   `kubectl apply -k`, `get sandboxagent` until Ready.
2. **UI**: kagent Agents list → `aws-budget` Ready → the spend/capacity
   question → tool calls → answer.
3. **Do not** record Vault tokens, AWS secret keys, or GCP HMAC secrets.
