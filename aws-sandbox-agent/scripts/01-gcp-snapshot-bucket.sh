#!/usr/bin/env bash
# Verify the existing GCP project + GCS bucket used for Substrate snapshots.
#
# These already exist — do not create them:
#   Org:      maniak.io
#   Project:  viper-kagent (number 89434469276)
#   Bucket:   gs://viper-kagent-ate-snapshots
#   Location: us-east1
#
# Default is dry-run (prints planned checks). Set APPLY=1 to run gcloud
# describe/create. Create is skipped when the project + bucket exist.
#
# Optional env (defaults are the existing lab values):
#   GCP_PROJECT_ID        default viper-kagent
#   GCS_BUCKET            default viper-kagent-ate-snapshots
#   GCS_LOCATION          default us-east1
#   GCP_BILLING_ACCOUNT   only required if a missing project must be created
#   GCP_FOLDER_ID         optional resource-manager folder
#   CREATE_HMAC=1         also create a bucket-scoped SA + HMAC (Path B)
#
# Never prints HMAC secrets (gcloud is instructed to write them aside).
set -euo pipefail

APPLY="${APPLY:-0}"
GCP_PROJECT_ID="${GCP_PROJECT_ID:-viper-kagent}"
GCS_LOCATION="${GCS_LOCATION:-us-east1}"
GCS_BUCKET="${GCS_BUCKET:-viper-kagent-ate-snapshots}"
PREFIX="gs://${GCS_BUCKET}/kagent/aws-budget/"

# Known lab pair — already provisioned. Script is a no-op for these.
LAB_PROJECT="viper-kagent"
LAB_BUCKET="viper-kagent-ate-snapshots"

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

project_exists() {
  gcloud projects describe "${GCP_PROJECT_ID}" --format='value(projectId)' >/dev/null 2>&1
}

bucket_exists() {
  gcloud storage buckets describe "gs://${GCS_BUCKET}" \
    --project="${GCP_PROJECT_ID}" >/dev/null 2>&1
}

if [[ "$GCP_PROJECT_ID" == *REPLACE_ME* || "$GCS_BUCKET" == *REPLACE_ME* ]]; then
  echo "refusing placeholder GCP_PROJECT_ID or GCS_BUCKET" >&2
  exit 1
fi

echo "org:      maniak.io"
echo "project:  ${GCP_PROJECT_ID} (lab number 89434469276 when using ${LAB_PROJECT})"
echo "bucket:   gs://${GCS_BUCKET}"
echo "location: ${GCS_LOCATION}"
echo "kagent snapshotsConfig.location → ${PREFIX}"
echo "APPLY=${APPLY}  (set APPLY=1 to run gcloud; create is skipped if resources exist)"
echo
echo "NOTE: project ${LAB_PROJECT} and bucket gs://${LAB_BUCKET} already exist."
echo "      This script skips create when they are present. Do not make a new project."
echo

have_gcloud=0
if command -v gcloud >/dev/null 2>&1; then
  have_gcloud=1
fi

skip_project=0
skip_bucket=0

# Never create the known lab pair, even if gcloud describe fails (auth, etc.).
if [[ "$GCP_PROJECT_ID" == "$LAB_PROJECT" ]]; then
  echo "project ${LAB_PROJECT} is the existing lab project — skip create"
  skip_project=1
fi
if [[ "$GCS_BUCKET" == "$LAB_BUCKET" ]]; then
  echo "bucket gs://${LAB_BUCKET} is the existing lab bucket — skip create"
  skip_bucket=1
fi

if [[ "$skip_project" == "0" || "$skip_bucket" == "0" ]]; then
  if [[ "$have_gcloud" == "1" ]]; then
    if [[ "$skip_project" == "0" ]]; then
      if project_exists; then
        echo "project ${GCP_PROJECT_ID} already exists — skip create"
        skip_project=1
      else
        echo "project ${GCP_PROJECT_ID} not found"
      fi
    fi
    if [[ "$skip_bucket" == "0" ]]; then
      if bucket_exists; then
        echo "bucket gs://${GCS_BUCKET} already exists — skip create"
        skip_bucket=1
      else
        echo "bucket gs://${GCS_BUCKET} not found"
      fi
    fi
  else
    echo "gcloud not on PATH — cannot probe a non-lab project/bucket."
  fi
fi

if [[ "$skip_project" == "1" && "$skip_bucket" == "1" ]]; then
  echo
  echo "Nothing to create. Set k8s/sandboxagent.yaml:"
  echo "  spec.substrate.snapshotsConfig.location: ${PREFIX}"
  echo
  echo "Path A (native GCS): give atelet a Google identity with object admin on this bucket."
  echo "Path B (S3 XML API): HMAC + endpoint https://storage.googleapis.com — see docs/snapshots-gcs.md"
  echo "kagent CRD still requires the gs:// scheme (pattern ^gs://). Do not put s3:// in SandboxAgent."
  if [[ "${CREATE_HMAC:-0}" != "1" ]]; then
    exit 0
  fi
fi

if [[ "$skip_project" == "0" ]]; then
  if [[ "$APPLY" == "1" && -z "${GCP_BILLING_ACCOUNT:-}" ]]; then
    echo "APPLY=1 requires GCP_BILLING_ACCOUNT to create a missing project" >&2
    exit 1
  fi
  # 1. New project only if the requested id is missing.
  create_args=(gcloud projects create "${GCP_PROJECT_ID}" --name="${GCP_PROJECT_ID}")
  if [[ -n "${GCP_FOLDER_ID:-}" ]]; then
    create_args+=(--folder="${GCP_FOLDER_ID}")
  fi
  run "${create_args[@]}"
  if [[ -n "${GCP_BILLING_ACCOUNT:-}" ]]; then
    run gcloud billing projects link "${GCP_PROJECT_ID}" --billing-account="${GCP_BILLING_ACCOUNT}"
  elif [[ "$APPLY" != "1" ]]; then
    echo "DRY-RUN gcloud billing projects link ${GCP_PROJECT_ID} --billing-account=XXXXXX-XXXXXX-XXXXXX"
  fi
else
  echo "skip: gcloud projects create ${GCP_PROJECT_ID}"
  echo "skip: gcloud billing projects link ${GCP_PROJECT_ID}"
fi

if [[ "$skip_bucket" == "0" ]]; then
  # 2. Storage API + bucket only if the requested bucket is missing.
  run gcloud services enable storage.googleapis.com --project="${GCP_PROJECT_ID}"
  run gcloud storage buckets create "gs://${GCS_BUCKET}" \
    --project="${GCP_PROJECT_ID}" \
    --location="${GCS_LOCATION}" \
    --uniform-bucket-level-access \
    --public-access-prevention
else
  echo "skip: gcloud storage buckets create gs://${GCS_BUCKET}"
fi

echo
echo "Set k8s/sandboxagent.yaml:"
echo "  spec.substrate.snapshotsConfig.location: ${PREFIX}"
echo
echo "Path A (native GCS): give atelet a Google identity with object admin on this bucket."
echo "Path B (S3 XML API): HMAC + endpoint https://storage.googleapis.com — see docs/snapshots-gcs.md"
echo "kagent CRD still requires the gs:// scheme (pattern ^gs://). Do not put s3:// in SandboxAgent."

if [[ "${CREATE_HMAC:-0}" == "1" ]]; then
  sa="ate-snapshots@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  if [[ "$have_gcloud" == "1" ]] && gcloud iam service-accounts describe "${sa}" \
      --project="${GCP_PROJECT_ID}" >/dev/null 2>&1; then
    echo "service account ${sa} already exists — skip create"
  else
    run gcloud iam service-accounts create ate-snapshots \
      --project="${GCP_PROJECT_ID}" \
      --display-name="Substrate snapshot writer"
  fi
  run gcloud storage buckets add-iam-policy-binding "gs://${GCS_BUCKET}" \
    --member="serviceAccount:${sa}" \
    --role="roles/storage.objectAdmin"
  echo
  echo "Create HMAC in the console (Cloud Storage → Settings → Interoperability)"
  echo "or: gcloud storage hmac create ${sa} --project=${GCP_PROJECT_ID}"
  echo "Put the Access ID + Secret in Vault. Do not commit them."
fi
