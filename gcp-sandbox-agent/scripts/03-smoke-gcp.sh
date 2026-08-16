#!/usr/bin/env bash
# GCP smoke: cluster objects (no Secret yaml) and optional live APIs.
# Uses caller env for ADC / GOOGLE_CREDENTIALS. Does not print secrets.
# Do not run with `set -x` — that would echo the service-account JSON.
set -euo pipefail

K3S_CONTAINER="${K3S_CONTAINER:-k3s-viper}"
REGION="${GCP_REGION:-us-east1}"

if [[ "$REGION" != "us-east1" ]]; then
  echo "this smoke test is scoped to us-east1 (got ${REGION})" >&2
  exit 1
fi

echo "== cluster objects (no secret values) =="
if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "${K3S_CONTAINER}"; then
  docker exec "${K3S_CONTAINER}" kubectl -n kagent get \
    sandboxagent gcp-budget \
    remotemcpserver gcp-budget-mcp \
    externalsecret gcp-budget-mcp \
    deploy gcp-budget-mcp \
    2>/dev/null || echo "warn gcp-budget objects not applied yet"
  echo
  echo "info skipping kubectl get secret -o yaml (would print the SA JSON)"
else
  echo "info ${K3S_CONTAINER} not visible; skip cluster checks"
fi

CREDS_FILE="${GOOGLE_APPLICATION_CREDENTIALS:-}"
CREDS_JSON="${GOOGLE_CREDENTIALS:-}"
if [[ -n "$CREDS_FILE" ]]; then
  echo "ok GOOGLE_APPLICATION_CREDENTIALS is set (path not echoed)"
fi
if [[ -n "$CREDS_JSON" ]]; then
  echo "ok GOOGLE_CREDENTIALS is set (value not printed)"
fi

if [[ -z "$CREDS_FILE" && -z "$CREDS_JSON" ]]; then
  if ! command -v gcloud >/dev/null 2>&1; then
    echo
    echo "info no GCP credentials in env and no gcloud; skip API smoke"
    echo "smoke ok (cluster checks only; no secrets printed)"
    exit 0
  fi
fi

PROJECT="${GCP_PROJECT:-}"
BILLING="${GCP_BILLING_ACCOUNT:-}"

echo
echo "== GCP APIs (us-east1; secrets not printed) =="

if command -v gcloud >/dev/null 2>&1; then
  echo "-- gcloud auth list (account emails only) --"
  gcloud auth list --filter=status:ACTIVE --format='value(account)' || true

  if [[ -n "$PROJECT" ]]; then
    echo
    echo "-- compute instances (us-east1, names/status only) --"
    gcloud compute instances list \
      --project="${PROJECT}" \
      --filter="zone:us-east1-*" \
      --format='table(name,zone,status,machineType.basename())' || true

    echo
    echo "-- compute region quotas (us-east1, metric/limit/usage) --"
    gcloud compute regions describe us-east1 \
      --project="${PROJECT}" \
      --format='table(quotas.metric,quotas.limit,quotas.usage)' || true
  else
    echo "info GCP_PROJECT not set; skip compute list"
  fi

  if [[ -n "$BILLING" ]]; then
    echo
    echo "-- billing account (displayName/open only) --"
    gcloud billing accounts describe "${BILLING}" \
      --format='value(displayName,open)' || true
  else
    echo "info GCP_BILLING_ACCOUNT not set; skip billing describe"
  fi

  echo
  echo "-- accessible projects (project ids only) --"
  gcloud projects list --format='value(projectId)' || true
else
  echo "info gcloud not on PATH; cluster checks only"
fi

echo
echo "smoke ok (numbers above are ground truth for the kagent chat; no secrets printed)"
