# Security

Least privilege, no passwords in git, gVisor isolation, read-mostly tools.

## What must never land in git

- ServiceNow **password** values
- Vault root / unseal tokens
- Screenshot of a `vault kv put` line that still has the password
- `kubectl get secret servicenow-mcp -o yaml` output

Git may contain: Vault **paths**, ExternalSecret **key names**, the
ServiceNow **host name** (`https://dev203166.service-now.com`), and
tool / table names.

Username lives in Vault with the password. Do not commit it either.

## ServiceNow identity (PDI, read-mostly)

Use a dedicated integration user on the personal developer instance
when you can (ITIL or a custom role that can read `incident` /
`sc_req_item` and write `work_notes` + `assigned_to`). Do not share a
human admin password with other demos.

The MCP server only calls:

| Allowed | Denied in code |
|---------|----------------|
| Table GET on `incident`, `sys_user`, `sc_req_item` | Generic shell, `os.system`, `subprocess` |
| Stats GET on `incident` | Incident create / close / delete / resolve |
| PATCH `work_notes` and `assigned_to` (named write tools) | Printing `SERVICENOW_PASSWORD` or Authorization headers |
| Compact JSON (truncated lists) | Invented ticket counts |

Writes must be **asked first** in the agent prompt. The tools exist;
the skills tell the model not to call them until the human says yes.

TLS: prefer normal verification (`SERVICENOW_TLS_VERIFY=true`). Set
`false` only if the lab path cannot verify the instance cert.

## Vault + External Secrets Operator

| Where | What |
|-------|------|
| Vault KV | `secret/platform/servicenow` |
| Keys in Vault | `host`, `username`, `password` |
| ExternalSecret | `k8s/external-secret.yaml` |
| Target Secret | `servicenow-mcp` in `kagent` |
| Pod env | `SERVICENOW_HOST`, `SERVICENOW_USERNAME`, `SERVICENOW_PASSWORD` |

Write on Viper after Vault login (placeholders are not real values):

```bash
docker exec -it k3s-viper kubectl -n vault exec -i vault-0 -- \
  vault kv put secret/platform/servicenow \
    host='https://dev203166.service-now.com' \
    username='<paste>' \
    password='<paste>'
```

ClusterSecretStore `vault-backend` is already the Viper day-1 path
([k8s-viper vault-eso-setup](https://github.com/sebbycorp/k8s-viper/blob/main/docs/vault-eso-setup.md)).
Do not add a second store for this demo.

## gVisor / Substrate

- The LLM and tool-calling runtime run in a **gVisor actor**
  (`ateom-gvisor:v0.0.9`), not as a privileged sidecar on the MCP pod.
- The MCP Deployment is non-root (uid **1000**), read-only rootfs,
  dropped caps, `automountServiceAccountToken: false`. It only needs
  egress to the ServiceNow host.
- Known lab risk (from k8s-viper): nested gVisor on dockerized k3s
  can fail (`runsc`, seccomp, `/dev/kvm`). That is a worker problem,
  not a reason to switch this agent to a plain `Agent` Deployment.

## Snapshot storage

- **Today:** rustfs in `ate-system` (bucket `ate-snapshots`). The
  SandboxAgent omits `snapshotsConfig`. Expected location:
  `gs://ate-snapshots/kagent/servicenow`. Bytes do not leave the cluster.
- Do not set `ignoreDifferences` on this agent.
