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

## GCP console (reserved — do not wire today)

Project **viper-kagent** and bucket **viper-kagent-ate-snapshots**
**already exist**. They are reserved for a later cluster-wide atelet
cutover. Do not click **New project** or **Create** bucket. Do **not**
set that URI on the SandboxAgent while atelet still uses rustfs.

Today snapshots stay on rustfs (`gs://ate-snapshots/kagent/aws-budget`
prefix). Path A (native GCS) and Path B (HMAC +
`https://storage.googleapis.com`) are future work — see
[snapshots-gcs.md](snapshots-gcs.md).

Optional look-only:

1. Open [https://console.cloud.google.com/](https://console.cloud.google.com/).
2. Project picker → **viper-kagent** (89434469276, org **maniak.io**).
3. Cloud Storage → **Buckets** → **viper-kagent-ate-snapshots**
   (`us-east1`, public access prevented).

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

1. **CLI**: prereqs, optional `01-gcp-snapshot-bucket.sh` (reserved
   GCS, skip-create, do not wire), Vault `kv put` with the secret
   redacted, `docker build` + `ctr import`, host `kubectl kustomize`
   piped into `docker exec -i k3s-viper kubectl apply -f -`,
   `get sandboxagent` until Ready (`gs://ate-snapshots/kagent/aws-budget`).
2. **UI**: kagent Agents list → `aws-budget` Ready → the spend/capacity
   question → tool calls → answer.
3. **Do not** record Vault tokens, AWS secret keys, or GCP HMAC secrets.
