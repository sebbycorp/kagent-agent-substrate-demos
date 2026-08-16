# Security

Least privilege, no keys in git, gVisor isolation, read-mostly tools.

## What must never land in git

- GCP service-account **JSON** (`private_key`, `private_key_id` values)
- Vault root / unseal tokens
- Screenshot of a `vault kv put` line that still has the JSON
- `kubectl get secret gcp-budget-mcp -o yaml` output

Git may contain: Vault **paths**, ExternalSecret **key names**, IAM
**permission lists**, project **names**, the billing account **id**
(`011C38-867461-BE95B1`).

## GCP identity (us-east1, read-mostly)

Create a dedicated service account (suggested name
`gcp-budget-agent`) in a project the operator already has — typically
**viper-kagent**. Do not share a human owner key. Do not grant
`roles/owner`, project-delete, or IAM-admin.

Enable APIs on the projects the SA will read:

- `cloudbilling.googleapis.com`
- `billingbudgets.googleapis.com`
- `compute.googleapis.com`
- `cloudresourcemanager.googleapis.com`

Attach **only** these permissions (custom role preferred). Predefined
`roles/billing.viewer` + `roles/compute.viewer` + `roles/browser` cover
most of this; Cloud Billing **Budget** list/get often needs
`billing.budgets.get` / `billing.budgets.list` (included in
`roles/billing.costsManager` — broader than we want; prefer the custom
role).

```json
{
  "title": "GcpBudgetAgentReadOnly",
  "description": "Read-mostly billing + us-east1 compute for gcp-budget",
  "stage": "GA",
  "includedPermissions": [
    "billing.accounts.get",
    "billing.accounts.list",
    "billing.resourceAssociations.list",
    "billing.budgets.get",
    "billing.budgets.list",
    "compute.instances.list",
    "compute.disks.list",
    "compute.regions.get",
    "compute.zones.list",
    "resourcemanager.projects.get",
    "resourcemanager.projects.list"
  ]
}
```

Notes:

- Billing APIs are **account-scoped**. Grant the custom role (or
  `roles/billing.viewer` + budget get/list) on billing account
  `011C38-867461-BE95B1`. Compute / Resource Manager go on the
  projects the SA should see (names only: **viper-kagent**,
  **maniak-io**, **qr-maniak-io**).
- There is **no** `resourcemanager.projects.delete`,
  `iam.serviceAccounts.create`, `resourcemanager.projects.setIamPolicy`,
  or `billing.budgets.delete` / `create`.
- Cloud Billing Accounts / Budgets / Catalog do **not** return
  month-to-date spend. The MCP tools say unavailable. Do not add
  BigQuery keys to this demo unless you later choose to.

Download the SA JSON **once**. Put it in Vault. Do not commit
`*-sa.json`.

## Vault + External Secrets Operator

| Where | What |
|-------|------|
| Vault KV | `secret/platform/gcp-budget` |
| Keys in Vault | `credentials_json`, `billing_account`, `project`, `region` |
| ExternalSecret | `k8s/external-secret.yaml` |
| Target Secret | `gcp-budget-mcp` in `kagent` |
| Pod | `GOOGLE_APPLICATION_CREDENTIALS` file from `credentials.json`, or `GOOGLE_CREDENTIALS`; plus `GCP_BILLING_ACCOUNT`, `GCP_PROJECT`, `GCP_REGION=us-east1` |

Write on Viper after Vault login (placeholders are not real values).
Keep the JSON **outside this repo**:

```bash
docker exec -it k3s-viper kubectl -n vault exec -i vault-0 -- \
  vault kv put secret/platform/gcp-budget \
    credentials_json='<paste SA JSON>' \
    billing_account='011C38-867461-BE95B1' \
    project='viper-kagent' \
    region='us-east1'
```

Paste the JSON once in that interactive shell. The file stays outside
this repo. Never screenshot it. Never `kubectl get secret -o yaml`.

ClusterSecretStore `vault-backend` is already the Viper day-1 path
([k8s-viper vault-eso-setup](https://github.com/sebbycorp/k8s-viper/blob/main/docs/vault-eso-setup.md)).
Do not add a second store for this demo.

## gVisor / Substrate

- The LLM and tool-calling runtime run in a **gVisor actor**
  (`ateom-gvisor:v0.0.9`), not as a privileged sidecar on the MCP pod.
- The MCP Deployment is non-root (uid **1000**), read-only rootfs,
  dropped caps, `automountServiceAccountToken: false`. It only needs
  egress to Google APIs.
- Known lab risk (from k8s-viper): nested gVisor on dockerized k3s
  can fail (`runsc`, seccomp, `/dev/kvm`). That is a worker problem,
  not a reason to switch this agent to a plain `Agent` Deployment.

## MCP threat model

| Allowed | Denied in code |
|---------|----------------|
| Billing get/list, Budget list, Compute list/get, Resource Manager search | Generic `gcloud` CLI, project-delete, IAM-create, `setIamPolicy` |
| Compact JSON (truncated lists) | Printing `private_key`, SA JSON, or Vault tokens |
| Honest API errors / `unavailable` for MTD spend | Fake $0 spend to “be helpful” |

## Snapshot storage

- **Today:** rustfs in `ate-system` (bucket `ate-snapshots`). The
  SandboxAgent omits `snapshotsConfig`. Expected location:
  `gs://ate-snapshots/kagent/gcp-budget`. Bytes do not leave the cluster.
- Do not set `ignoreDifferences` on this agent.
