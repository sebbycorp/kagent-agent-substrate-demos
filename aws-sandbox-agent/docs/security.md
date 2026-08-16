# Security

Least privilege, no keys in git, gVisor isolation, read-mostly tools.

## What must never land in git

- AWS access key id **values** and secret access keys
- GCP HMAC secrets, service-account JSON, refresh tokens
- Vault root / unseal tokens
- Screenshot of a `vault kv put` line that still has the secret

Git may contain: Vault **paths**, ExternalSecret **key names**, IAM
**policy documents**, GCS **bucket names**, AWS **account-id** if you
choose to document it.

## AWS IAM (us-east-2, read-mostly)

Create a dedicated user or role `aws-budget-agent`. Attach **only** this
customer-managed policy. No `s3:*` on customer buckets (snapshots are
GCP; the agent does not list your data lakes).

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CallerIdentity",
      "Effect": "Allow",
      "Action": ["sts:GetCallerIdentity"],
      "Resource": "*"
    },
    {
      "Sid": "CostExplorerRead",
      "Effect": "Allow",
      "Action": ["ce:Get*"],
      "Resource": "*"
    },
    {
      "Sid": "BudgetsView",
      "Effect": "Allow",
      "Action": ["budgets:View*"],
      "Resource": "*"
    },
    {
      "Sid": "ComputeDescribeUsEast2",
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "autoscaling:Describe*",
        "rds:Describe*",
        "elasticache:Describe*"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-2"
        }
      }
    },
    {
      "Sid": "ServiceQuotasRead",
      "Effect": "Allow",
      "Action": [
        "servicequotas:Get*",
        "servicequotas:List*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ComputeOptimizerOptional",
      "Effect": "Allow",
      "Action": ["compute-optimizer:Get*"],
      "Resource": "*"
    }
  ]
}
```

Notes:

- Cost Explorer and Budgets are **account-global** APIs (endpoint
  us-east-1). The `ce:Get*` / `budgets:View*` statements are not
  region-conditioned; the **tools** still pass a us-east-2 filter
  where CE supports `REGION`.
- `ec2:Describe*` with `aws:RequestedRegion=us-east-2` blocks casual
  use of the same key against other regions.
- There is **no** `iam:Create*`, `ec2:Terminate*`, `ec2:Stop*`,
  `budgets:Delete*`, `budgets:Modify*`, or `s3:*`.
- If Compute Optimizer is not enrolled, `Get*` returns an API error;
  the MCP tool degrades and does not retry with broader IAM.

## Vault + External Secrets Operator

| Where | What |
|-------|------|
| Vault KV | `secret/platform/aws-budget` |
| Keys in Vault | `access_key_id`, `secret_access_key`, `region` |
| ExternalSecret | `k8s/external-secret.yaml` |
| Target Secret | `aws-budget-mcp` in `kagent` |
| Pod env | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` |

Write on Viper after Vault login (placeholders are not real values):

```bash
docker exec -it k3s-viper kubectl -n vault exec -i vault-0 -- \
  vault kv put secret/platform/aws-budget \
    access_key_id='<AKIA…>' \
    secret_access_key='<secret>' \
    region='us-east-2'
```

ClusterSecretStore `vault-backend` is already the Viper day-1 path
([k8s-viper vault-eso-setup](https://github.com/sebbycorp/k8s-viper/blob/main/docs/vault-eso-setup.md)).
Do not add a second store for this demo.

## gVisor / Substrate

- The LLM and tool-calling runtime run in a **gVisor actor**
  (`ateom-gvisor:v0.0.9`), not as a privileged sidecar on the MCP pod.
- The MCP Deployment is non-root, read-only rootfs, dropped caps,
  `automountServiceAccountToken: false`. It only needs AWS egress.
- Known lab risk (from k8s-viper): nested gVisor on dockerized k3s
  can fail (`runsc`, seccomp, `/dev/kvm`). That is a worker problem,
  not a reason to switch this agent to a plain `Agent` Deployment.

## MCP threat model

| Allowed | Denied in code |
|---------|----------------|
| Describe / Get / View / List used by the named tools | Generic `aws` CLI, `iam:Create*`, terminate, budget delete |
| Compact JSON (truncated lists) | Printing `AWS_SECRET_ACCESS_KEY` or Authorization headers |
| Honest API errors | Fake $0 spend to “be helpful” |

## GCP snapshot bucket

- New project so this lab cannot see other GCP workloads.
- Bucket: public access prevented.
- Path A (native GCS): atelet identity gets object admin on **this
  bucket only**.
- Path B (HMAC): interoperability key for a bucket-scoped SA; store
  HMAC in Vault, not in `k8s/`.
- Details: [snapshots-gcs.md](snapshots-gcs.md).
