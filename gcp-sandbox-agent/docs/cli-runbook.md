# CLI runbook

Copy-paste only. For *why*, use [../JOURNEY.md](../JOURNEY.md).
On Viper, kubectl is inside the k3s container.

```bash
# optional: from this demo folder
export DEMO="$(git rev-parse --show-toplevel)/gcp-sandbox-agent"
K() { docker exec k3s-viper kubectl "$@"; }
```

## Prereqs

```bash
"$DEMO/scripts/00-prereqs.sh"
```

## Snapshots today (rustfs)

Today atelet writes to rustfs (`ATE_STORAGE_BACKEND=s3`, bucket
`ate-snapshots`). `sandboxagent.yaml` **omits** `snapshotsConfig`.
Expected ActorTemplate location: `gs://ate-snapshots/kagent/gcp-budget`.

```bash
# after the SandboxAgent exists
K -n kagent get actortemplate gcp-budget \
  -o jsonpath='{.spec.snapshotsConfig.location}{"\n"}{.status.goldenSnapshot}{"\n"}'
K -n ate-system get pods,svc
```

## Vault (Viper)

SA JSON stays **outside this repo**. Billing account id (docs only):
`011C38-867461-BE95B1`.

```bash
# Paste the SA JSON once. Do not keep the file in this repo.
docker exec -it k3s-viper kubectl -n vault exec -i vault-0 -- \
  vault kv put secret/platform/gcp-budget \
    credentials_json='<paste SA JSON>' \
    billing_account='011C38-867461-BE95B1' \
    project='viper-kagent' \
    region='us-east1'
```

Do not `kubectl get secret gcp-budget-mcp -o yaml`.

## Build + import MCP image

```bash
# on Viper, from the demos repo root
"$DEMO/scripts/02-build-import-mcp.sh"
```

Equivalent:

```bash
docker build -t gcp-budget-mcp:dev gcp-sandbox-agent/images/gcp-budget-mcp
docker save gcp-budget-mcp:dev | docker exec -i k3s-viper ctr images import -
```

## Apply agent

Host kustomize piped into the node. The k3s container cannot see host
paths — do **not** `docker exec … kubectl apply -k <host-path>`.

```bash
kubectl kustomize gcp-sandbox-agent/k8s | docker exec -i k3s-viper kubectl apply -f -
```

## Wait / chat checks

```bash
K -n kagent get sandboxagents,remotemcpservers,externalsecrets
K -n kagent get deploy,pods,svc -l app.kubernetes.io/name=gcp-budget-mcp
K -n kagent get actortemplates
K -n kagent get sandboxagent gcp-budget -o jsonpath='{.status.conditions}' ; echo
```

Wait until `SandboxAgent/gcp-budget` Ready. First golden snapshot is often 60–90s.

## Smoke (no secrets printed)

```bash
# cluster objects only unless GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_CREDENTIALS is set
"$DEMO/scripts/03-smoke-gcp.sh"
```

Do not run smoke under `set -x` / `bash -x` (that would echo the JSON).

## Teardown (optional)

```bash
kubectl kustomize gcp-sandbox-agent/k8s | docker exec -i k3s-viper kubectl delete -f - --ignore-not-found
# do not delete Vault `secret/platform/gcp-budget` unless you intend to
```
