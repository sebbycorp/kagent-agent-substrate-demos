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

## Snapshots today (rustfs) + reserved GCS (do not wire)

Today atelet writes to rustfs (`ATE_STORAGE_BACKEND=s3`, bucket
`ate-snapshots`). `sandboxagent.yaml` **omits** `snapshotsConfig`.
Expected ActorTemplate location: `gs://ate-snapshots/kagent/aws-budget`.

Project **viper-kagent** (89434469276) and
**gs://viper-kagent-ate-snapshots** already exist and are reserved for
a later cluster-wide atelet cutover. Do not create another. Do not set
that URI on this SandboxAgent yet.

```bash
# verify reserved GCS; create is skipped. Does not change the agent YAML.
"$DEMO/scripts/01-gcp-snapshot-bucket.sh"
```

```bash
# after the SandboxAgent exists — expect gs://ate-snapshots/kagent/aws-budget
K -n kagent get actortemplate aws-budget -o jsonpath='{.spec.snapshotsConfig.location}{"\n"}{.status.goldenSnapshot}{"\n"}'
K -n ate-system get pods,svc
# rustfs should be present; atelet env ATE_STORAGE_BACKEND=s3
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

Host kustomize piped into the node. The k3s container cannot see host
paths — do **not** `docker exec … kubectl apply -k <host-path>`.

```bash
kubectl kustomize aws-sandbox-agent/k8s | docker exec -i k3s-viper kubectl apply -f -
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
kubectl kustomize aws-sandbox-agent/k8s | docker exec -i k3s-viper kubectl delete -f - --ignore-not-found
# do not delete the existing GCP project (viper-kagent) or AWS user unless you intend to
```
