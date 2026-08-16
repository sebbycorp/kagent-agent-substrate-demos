# CLI runbook

Copy-paste only. For *why*, use [../JOURNEY.md](../JOURNEY.md).
On Viper, kubectl is inside the k3s container.

```bash
# optional: from this demo folder
export DEMO="$(git rev-parse --show-toplevel)/aws-sandbox-agent"
K() { docker exec k3s-viper kubectl "$@"; }
```

## Prereqs

```bash
"$DEMO/scripts/00-prereqs.sh"
```

## GCP project + snapshot bucket

```bash
# prints gcloud commands by default. APPLY=1 actually creates.
export GCP_PROJECT_ID="ate-snapshots-$(whoami)-$(date +%Y%m%d)"
export GCP_BILLING_ACCOUNT="XXXXXX-XXXXXX-XXXXXX"   # from: gcloud billing accounts list
export GCS_BUCKET="ate-snapshots-${GCP_PROJECT_ID}"
export GCS_LOCATION="us-east1"
"$DEMO/scripts/01-gcp-snapshot-bucket.sh"
# APPLY=1 "$DEMO/scripts/01-gcp-snapshot-bucket.sh"
```

Inspect what kagent will write (must stay `gs://`):

```bash
# after the SandboxAgent exists
K -n kagent get sandboxagent aws-budget -o yaml | sed -n '/snapshotsConfig/,+6p'
K -n kagent get actortemplate aws-budget -o jsonpath='{.spec.snapshotsConfig.location}{"\n"}{.status.goldenSnapshot}{"\n"}'
K -n ate-system get pods
# look for rustfs vs only atelet/ate-api/valkey
```

## AWS IAM (keys never echo)

```bash
export AWS_REGION=us-east-2
# create user + attach the policy in docs/security.md, then:
aws iam create-access-key --user-name aws-budget-agent
# paste AccessKeyId / SecretAccessKey into Vault only — not into a file in this repo
```

Smoke (uses your local AWS profile, not the cluster):

```bash
AWS_REGION=us-east-2 "$DEMO/scripts/03-smoke-aws.sh"
```

## Vault (Viper)

```bash
docker exec -it k3s-viper kubectl -n vault exec -i vault-0 -- \
  vault kv put secret/platform/aws-budget \
    access_key_id='<paste>' \
    secret_access_key='<paste>' \
    region='us-east-2'
```

## Build + import MCP image

```bash
# on Viper, from the demos repo root
"$DEMO/scripts/02-build-import-mcp.sh"
```

Equivalent:

```bash
docker build -t aws-budget-mcp:dev aws-sandbox-agent/images/aws-budget-mcp
docker save aws-budget-mcp:dev | docker exec -i k3s-viper ctr images import -
```

## Apply agent

```bash
K apply -k "$DEMO/k8s"
# if kustomize is only on the host, render then apply:
kubectl kustomize "$DEMO/k8s" | docker exec -i k3s-viper kubectl apply -f -
```

## Wait / chat checks

```bash
K -n kagent get sandboxagents,remotemcpservers,externalsecrets
K -n kagent get deploy,pods,svc -l app.kubernetes.io/name=aws-budget-mcp
K -n kagent get actortemplates
K -n kagent get sandboxagent aws-budget -o jsonpath='{.status.conditions}' ; echo
```

Wait until `SandboxAgent/aws-budget` Ready. First golden snapshot is often 60–90s.

## Teardown (optional)

```bash
kubectl kustomize "$DEMO/k8s" | docker exec -i k3s-viper kubectl delete -f - --ignore-not-found
# do not delete the GCP project or AWS user unless you intend to
```
