# CLI runbook

Copy-paste only. For *why*, use [../JOURNEY.md](../JOURNEY.md).
On Viper, kubectl is inside the k3s container.

```bash
# optional: from this demo folder
export DEMO="$(git rev-parse --show-toplevel)/service-now-sandbox-agent"
K() { docker exec k3s-viper kubectl "$@"; }
```

## Prereqs

```bash
"$DEMO/scripts/00-prereqs.sh"
```

## Snapshots today (rustfs)

Today atelet writes to rustfs (`ATE_STORAGE_BACKEND=s3`, bucket
`ate-snapshots`). `sandboxagent.yaml` **omits** `snapshotsConfig`.
Expected ActorTemplate location: `gs://ate-snapshots/kagent/servicenow`.

```bash
# after the SandboxAgent exists
K -n kagent get actortemplate servicenow \
  -o jsonpath='{.spec.snapshotsConfig.location}{"\n"}{.status.goldenSnapshot}{"\n"}'
K -n ate-system get pods,svc
```

## Vault (Viper)

```bash
docker exec -it k3s-viper kubectl -n vault exec -i vault-0 -- \
  vault kv put secret/platform/servicenow \
    host='https://dev203166.service-now.com' \
    username='<paste>' \
    password='<paste>'
```

Do not `kubectl get secret servicenow-mcp -o yaml`.

## Build + import MCP image

```bash
# on Viper, from the demos repo root
"$DEMO/scripts/02-build-import-mcp.sh"
```

Equivalent:

```bash
docker build -t servicenow-mcp:dev service-now-sandbox-agent/images/servicenow-mcp
docker save servicenow-mcp:dev | docker exec -i k3s-viper ctr images import -
```

## Apply agent

Host kustomize piped into the node. The k3s container cannot see host
paths — do **not** `docker exec … kubectl apply -k <host-path>`.

```bash
kubectl kustomize service-now-sandbox-agent/k8s | docker exec -i k3s-viper kubectl apply -f -
```

## Wait / chat checks

```bash
K -n kagent get sandboxagents,remotemcpservers,externalsecrets
K -n kagent get deploy,pods,svc -l app.kubernetes.io/name=servicenow-mcp
K -n kagent get actortemplates
K -n kagent get sandboxagent servicenow -o jsonpath='{.status.conditions}' ; echo
```

Wait until `SandboxAgent/servicenow` Ready. First golden snapshot is often 60–90s.

## Smoke (no secrets printed)

```bash
# cluster objects only unless SERVICENOW_USERNAME + SERVICENOW_PASSWORD are set
"$DEMO/scripts/03-smoke-servicenow.sh"
```

Do not run smoke under `set -x` / `bash -x` (that would echo the password).

## Teardown (optional)

```bash
kubectl kustomize service-now-sandbox-agent/k8s | docker exec -i k3s-viper kubectl delete -f - --ignore-not-found
# do not delete Vault `secret/platform/servicenow` unless you intend to
```
