#!/usr/bin/env bash
# docker build + k3s ctr import (Viper / aws-budget-mcp pattern).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CTX="${ROOT}/gcp-sandbox-agent/images/gcp-budget-mcp"
TAG="${TAG:-gcp-budget-mcp:dev}"
K3S_CONTAINER="${K3S_CONTAINER:-k3s-viper}"

echo "building ${TAG} from ${CTX}"
docker build -t "${TAG}" "${CTX}"

if docker ps --format '{{.Names}}' | grep -qx "${K3S_CONTAINER}"; then
  echo "importing ${TAG} into ${K3S_CONTAINER}"
  docker save "${TAG}" | docker exec -i "${K3S_CONTAINER}" ctr images import -
else
  echo "info ${K3S_CONTAINER} not running; image built locally only"
fi

echo "done. Deployment uses imagePullPolicy: IfNotPresent"
