#!/usr/bin/env bash
# Deploy the 3-node cEOS lab with Containerlab.
# Renders lab-only AAA locally. Does not print secret values.
set -euo pipefail

# shellcheck source=lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
load_env

clab="$(clab_bin)"

echo "== render startup-configs =="
render_lab

echo
echo "== image =="
echo "info using ${CEOS_IMAGE} (not stored in this git repo)"
if ! docker image inspect "${CEOS_IMAGE}" >/dev/null 2>&1; then
  echo "info pulling ${CEOS_IMAGE} (Arista-licensed cEOS — pull only if permitted)"
  docker pull "${CEOS_IMAGE}"
fi

echo
echo "== containerlab deploy =="
echo "info topology ${TOPO_RUN}"
echo "info nodes: ${NODES[*]}  (no Linux clients in v1)"
# --reconfigure so a previous lab directory cannot shadow rendered startup-configs
"${clab}" deploy -t "${TOPO_RUN}" --reconfigure

echo
echo "== wait for eAPI (cEOS boot is slow; no invented success) =="
deadline=$((SECONDS + 300))
pending=("${NODES[@]}")
while ((SECONDS < deadline)) && ((${#pending[@]} > 0)); do
  still=()
  for node in "${pending[@]}"; do
    cname="$(node_container "$node")"
    if ! container_running "$cname"; then
      still+=("$node")
      continue
    fi
    ip="$(node_mgmt_ip "$cname" || true)"
    if [[ -z "${ip}" ]]; then
      still+=("$node")
      continue
    fi
    if eapi_run "$ip" "show hostname" >/dev/null 2>&1; then
      echo "ok   ${node} eAPI via ${ip}"
    else
      still+=("$node")
    fi
  done
  pending=("${still[@]+"${still[@]}"}")
  if ((${#pending[@]} > 0)); then
    echo "info waiting on: ${pending[*]}"
    sleep 5
  fi
done

if ((${#pending[@]} > 0)); then
  echo "deploy: containers may be up but eAPI not ready yet: ${pending[*]}" >&2
  echo "deploy: run ./scripts/02-verify.sh after cEOS finishes booting" >&2
  exit 2
fi

echo
echo "deploy: all 3 nodes answered eAPI. Next: ./scripts/02-verify.sh"
