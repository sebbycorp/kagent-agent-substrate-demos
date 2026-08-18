#!/usr/bin/env bash
# Host tools for the Arista cEOS Containerlab lab.
# Does not print secret values. Does not pull or inspect image layers.
set -euo pipefail

# shellcheck source=lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
load_env

ok=0
warn=0

echo "== host tools =="
if require_cmd docker; then
  echo "ok   docker  $(docker --version 2>/dev/null | head -n1)"
else
  ok=1
fi
if require_cmd python3; then
  echo "ok   python3  $(python3 --version 2>/dev/null)"
else
  ok=1
fi
if clab="$(clab_bin 2>/dev/null)"; then
  echo "ok   ${clab}  $(${clab} version 2>/dev/null | head -n1 || ${clab} version short 2>/dev/null || true)"
else
  echo "MISS containerlab (not installed on Viper yet — install from https://containerlab.dev before deploy)"
  ok=1
fi

echo
echo "== image pin (local import only; not in git; no Hub pull) =="
echo "info CEOS_IMAGE=${CEOS_IMAGE}"
echo "info official import: docker import cEOS64-lab-4.33.9M.tar.xz ceos:4.33.9M"
echo "info host target: Viper 172.16.10.135 Ubuntu 24.04 Docker 29.4.0 amd64"
if require_local_ceos_image; then
  arch="$(docker image inspect -f '{{.Architecture}}' "${CEOS_IMAGE}" 2>/dev/null || true)"
  echo "ok   local image present (architecture ${arch:-unknown})"
else
  ok=1
fi

echo
echo "== lab AAA (names only) =="
if [[ -f "${DEMO_ROOT}/.env" ]]; then
  echo "ok   .env present (values not printed)"
else
  echo "info no .env — scripts use Containerlab/cEOS lab defaults (see .env.example)"
  echo "info future kagent deployment reads Vault secret/platform/arista-ceos keys username, password, hosts_json"
  warn=1
fi
echo "info CEOS_LAB_USER is set (value not printed)"

echo
echo "== Viper k3s (optional; kagent not in this v1) =="
if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx k3s-viper; then
  echo "ok   container k3s-viper is running"
  echo "info kagent SandboxAgent for this fabric is not deployed yet"
else
  echo "info k3s-viper not visible from this host (ok for Containerlab-only v1)"
fi

echo
if [[ "$ok" -ne 0 ]]; then
  echo "prereqs: missing required tools"
  exit 1
fi
if [[ "$warn" -ne 0 ]]; then
  echo "prereqs: ok with warnings"
  exit 0
fi
echo "prereqs: ok"
