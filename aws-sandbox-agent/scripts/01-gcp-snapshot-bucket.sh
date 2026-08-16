#!/usr/bin/env bash
# Create a NEW GCP project + GCS bucket for Substrate snapshots.
# Default is dry-run (prints commands). Set APPLY=1 to execute.
#
# Required env when APPLY=1:
#   GCP_PROJECT_ID        globally unique project id
#   GCP_BILLING_ACCOUNT   from: gcloud billing accounts list
# Optional:
#   GCS_BUCKET            default ate-snapshots-${GCP_PROJECT_ID}
#   GCS_LOCATION          default us-east1
#   GCP_FOLDER_ID         optional resource-manager folder
#   CREATE_HMAC=1         also create a bucket-scoped SA + HMAC (Path B)
#
# Never prints HMAC secrets (gcloud is instructed to write them aside).
set -euo pipefail

APPLY="${APPLY:-0}"
GCP_PROJECT_ID="${GCP_PROJECT_ID:-ate-snapshots-REPLACE_ME}"
GCS_LOCATION="${GCS_LOCATION:-us-east1}"
GCS_BUCKET="${GCS_BUCKET:-ate-snapshots-${GCP_PROJECT_ID}}"
PREFIX="gs://${GCS_BUCKET}/kagent/aws-budget/"

run() {
  if [[ "$APPLY" == "1" ]]; then
    echo "+ $*"
    "$@"
  else
    printf 'DRY-RUN '
    printf '%q ' "$@"
    echo
  fi
}

echo "project:  ${GCP_PROJECT_ID}"
echo "bucket:   ${GCS_BUCKET}"
echo "location: ${GCS_LOCATION}"
echo "kagent snapshotsConfig.location → ${PREFIX}"
echo "APPLY=${APPLY}  (set APPLY=1 to create)"
echo

if [[ "$APPLY" == "1" && "$GCP_PROJECT_ID" == "ate-snapshots-REPLACE_ME" ]]; then
  echo "refusing APPLY=1 with placeholder GCP_PROJECT_ID" >&2
  exit 1
fi
if [[ "$APPLY" == "1" && -z "${GCP_BILLING_ACCOUNT:-}" ]]; then
  echo "APPLY=1 requires GCP_BILLING_ACCOUNT" >&2
  exit 1
fi

# 1. New project (isolated from other GCP workloads).
create_args=(gcloud projects create "${GCP_PROJECT_ID}" --name="${GCP_PROJECT_ID}")
if [[ -n "${GCP_FOLDER_ID:-}" ]]; then
  create_args+=(--folder="${GCP_FOLDER_ID}")
fi
run "${create_args[@]}"

# 2. Billing — GCS will not create objects without it.
if [[ -n "${GCP_BILLING_ACCOUNT:-}" ]]; then
  run gcloud billing projects link "${GCP_PROJECT_ID}" --billing-account="${GCP_BILLING_ACCOUNT}"
else
  echo "DRY-RUN gcloud billing projects link ${GCP_PROJECT_ID} --billing-account=XXXXXX-XXXXXX-XXXXXX"
fi

# 3. Storage API + bucket (public access prevented is the gsutil default for new buckets).
run gcloud services enable storage.googleapis.com --project="${GCP_PROJECT_ID}"
run gcloud storage buckets create "gs://${GCS_BUCKET}" \
  --project="${GCP_PROJECT_ID}" \
  --location="${GCS_LOCATION}" \
  --uniform-bucket-level-access \
  --public-access-prevention

echo
echo "Set k8s/sandboxagent.yaml:"
echo "  spec.substrate.snapshotsConfig.location: ${PREFIX}"
echo
echo "Path A (native GCS): give atelet a Google identity with object admin on this bucket."
echo "Path B (S3 XML API): HMAC + endpoint https://storage.googleapis.com — see docs/snapshots-gcs.md"
echo "kagent CRD still requires the gs:// scheme (pattern ^gs://). Do not put s3:// in SandboxAgent."

if [[ "${CREATE_HMAC:-0}" == "1" ]]; then
  sa="ate-snapshots@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  run gcloud iam service-accounts create ate-snapshots \
    --project="${GCP_PROJECT_ID}" \
    --display-name="Substrate snapshot writer"
  run gcloud storage buckets add-iam-policy-binding "gs://${GCS_BUCKET}" \
    --member="serviceAccount:${sa}" \
    --role="roles/storage.objectAdmin"
  echo
  echo "Create HMAC in the console (Cloud Storage → Settings → Interoperability)"
  echo "or: gcloud storage hmac create ${sa} --project=${GCP_PROJECT_ID}"
  echo "Put the Access ID + Secret in Vault. Do not commit them."
fi
