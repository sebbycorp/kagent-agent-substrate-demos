#!/usr/bin/env bash
# Check local tools and (if present) the Viper k3s pairing.
# Does not print secret values.
set -euo pipefail

ok=0
warn=0

need() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "ok   $1  $($1 --version 2>/dev/null | head -n1 || true)"
  else
    echo "MISS $1"
    ok=1
  fi
}

echo "== host tools =="
need docker
need git
if command -v kubectl >/dev/null 2>&1; then
  echo "ok   kubectl  $(kubectl version --client --short 2>/dev/null || kubectl version --client 2>/dev/null | head -n1)"
else
  echo "info kubectl not on PATH (Viper uses: docker exec k3s-viper kubectl)"
fi
if command -v python3 >/dev/null 2>&1; then
  echo "ok   python3  $(python3 --version 2>/dev/null)"
else
  echo "warn python3 missing (needed for scripts/03-smoke-servicenow.sh Table API path)"
  warn=1
fi

echo
echo "== Viper k3s (optional) =="
if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx k3s-viper; then
  echo "ok   container k3s-viper is running"
  docker exec k3s-viper kubectl -n kagent get sandboxagents,workerpool 2>/dev/null || {
    echo "warn could not list SandboxAgents in kagent"
    warn=1
  }
  docker exec k3s-viper kubectl -n ate-system get pods 2>/dev/null || {
    echo "warn could not list ate-system pods"
    warn=1
  }
  echo
  echo "Pins to confirm (do not bump): kagent 0.10.0-rc2 + substrate 0.0.9 + ateom-gvisor:v0.0.9"
else
  echo "info k3s-viper container not visible from this host"
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
