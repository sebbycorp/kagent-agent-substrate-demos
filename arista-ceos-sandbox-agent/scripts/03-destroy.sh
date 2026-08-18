#!/usr/bin/env bash
# Destroy the 3-node cEOS lab. Does not print secret values.
set -euo pipefail

# shellcheck source=lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
load_env

clab="$(clab_bin)"

if [[ -f "${TOPO_RUN}" ]]; then
  topo="${TOPO_RUN}"
elif [[ -f "${TOPO_SRC}" ]]; then
  topo="${TOPO_SRC}"
else
  echo "destroy: no topology file found" >&2
  exit 1
fi

echo "== containerlab destroy =="
echo "info topology ${topo}"
"${clab}" destroy -t "${topo}" --cleanup

echo
echo "destroy: done. generated startup-configs left in ${GEN_DIR} (gitignored; contain lab AAA)"
echo "destroy: remove them with: rm -f ${GEN_DIR}/*.cfg ${GEN_DIR}/topology.yml"
