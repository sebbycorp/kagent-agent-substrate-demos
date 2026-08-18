#!/usr/bin/env bash
# Shared helpers for the Arista cEOS Containerlab lab.
# Do not enable `set -x` in callers — generated configs carry lab AAA.
# This file never prints CEOS_LAB_PASSWORD or eAPI Authorization headers.

if [[ -n "${ARISTA_CEOS_LIB_LOADED:-}" ]]; then
  return 0
fi
ARISTA_CEOS_LIB_LOADED=1

set -euo pipefail

DEMO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAB_DIR="${DEMO_ROOT}/clab"
GEN_DIR="${CLAB_DIR}/generated"
TOPO_SRC="${CLAB_DIR}/topology.yml"
TOPO_RUN="${GEN_DIR}/topology.yml"
LAB_NAME="arista-ceos"
NODES=(spine1 leaf1 leaf2)
DEFAULT_CEOS_IMAGE="sebbycorp/ceosimage:latest"

# Containerlab/cEOS published defaults (https://containerlab.dev/manual/kinds/ceos/).
# Used only when .env does not set CEOS_LAB_USER / CEOS_LAB_PASSWORD.
# Not a production secret. Future kagent reads Vault secret/platform/arista-ceos.
_CLAB_DEFAULT_USER="admin"
_CLAB_DEFAULT_PASSWORD="admin"

load_env() {
  # Disable xtrace while sourcing so `bash -x` cannot leak .env values.
  set +x
  if [[ -f "${DEMO_ROOT}/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${DEMO_ROOT}/.env"
    set +a
  fi
  CEOS_IMAGE="${CEOS_IMAGE:-${DEFAULT_CEOS_IMAGE}}"
  if [[ -z "${CEOS_LAB_USER:-}" ]]; then
    CEOS_LAB_USER="${_CLAB_DEFAULT_USER}"
  fi
  if [[ -z "${CEOS_LAB_PASSWORD:-}" ]]; then
    CEOS_LAB_PASSWORD="${_CLAB_DEFAULT_PASSWORD}"
  fi
}

require_cmd() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "MISS $name" >&2
    return 1
  fi
}

clab_bin() {
  if command -v containerlab >/dev/null 2>&1; then
    echo containerlab
    return 0
  fi
  if command -v clab >/dev/null 2>&1; then
    echo clab
    return 0
  fi
  echo "MISS containerlab (or clab)" >&2
  return 1
}

node_container() {
  local node="$1"
  echo "clab-${LAB_NAME}-${node}"
}

# First IPv4 on the container's Docker networks (mgmt). No hardcoded Ma0.
node_mgmt_ip() {
  local cname="$1"
  docker inspect -f '{{range .NetworkSettings.Networks}}{{if .IPAddress}}{{.IPAddress}}{{println}}{{end}}{{end}}' "$cname" \
    | awk 'NF { print; exit }'
}

container_running() {
  local cname="$1"
  [[ "$(docker inspect -f '{{.State.Running}}' "$cname" 2>/dev/null || true)" == "true" ]]
}

# Render startup-configs + a deployable topology into clab/generated/.
# AAA is injected from the environment; the password is not written to stdout.
render_lab() {
  load_env
  umask 077
  mkdir -p "${GEN_DIR}"

  local node tmpl dest
  for node in "${NODES[@]}"; do
    tmpl="${CLAB_DIR}/configs/${node}.cfg.tmpl"
    dest="${GEN_DIR}/${node}.cfg"
    if [[ ! -f "$tmpl" ]]; then
      echo "missing template $tmpl" >&2
      return 1
    fi
    set +x
    CEOS_LAB_USER="$CEOS_LAB_USER" CEOS_LAB_PASSWORD="$CEOS_LAB_PASSWORD" \
      python3 - "$tmpl" "$dest" <<'PY'
import os
import sys

src, dest = sys.argv[1], sys.argv[2]
user = os.environ["CEOS_LAB_USER"]
password = os.environ["CEOS_LAB_PASSWORD"]
if any(ch in user for ch in " \t\n") or any(ch in password for ch in " \t\n"):
    raise SystemExit("CEOS_LAB_USER / CEOS_LAB_PASSWORD must not contain whitespace")
aaa = (
    "username %s privilege 15 role network-admin secret %s"
    % (user, password)
)
text = open(src, encoding="utf-8").read()
marker = "! __LAB_AAA__"
if marker not in text:
    raise SystemExit("template %s missing %s marker" % (src, marker))
open(dest, "w", encoding="utf-8").write(text.replace(marker, aaa, 1))
PY
  done

  CEOS_IMAGE="$CEOS_IMAGE" TOPO_SRC="$TOPO_SRC" TOPO_RUN="$TOPO_RUN" \
    python3 - <<'PY'
import os
import re

src = os.environ["TOPO_SRC"]
dest = os.environ["TOPO_RUN"]
image = os.environ["CEOS_IMAGE"]
text = open(src, encoding="utf-8").read()
text = re.sub(
    r"^(?P<indent>\s*)image:\s+\S+",
    lambda m: "%simage: %s" % (m.group("indent"), image),
    text,
    count=1,
    flags=re.M,
)
text = text.replace("startup-config: generated/", "startup-config: ")
open(dest, "w", encoding="utf-8").write(text)
PY

  echo "rendered ${GEN_DIR} (image ${CEOS_IMAGE}; AAA from env, not printed)"
}

# POST /command-api. Prints response body to stdout. Never logs user/password.
eapi_run() {
  local ip="$1"
  shift
  local cmds_json
  cmds_json="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "$@")"
  set +x
  CEOS_LAB_USER="$CEOS_LAB_USER" CEOS_LAB_PASSWORD="$CEOS_LAB_PASSWORD" \
    EAPI_IP="$ip" EAPI_CMDS="$cmds_json" python3 - <<'PY'
import base64
import json
import os
import sys
import urllib.error
import urllib.request

ip = os.environ["EAPI_IP"]
user = os.environ["CEOS_LAB_USER"]
password = os.environ["CEOS_LAB_PASSWORD"]
cmds = json.loads(os.environ["EAPI_CMDS"])
payload = json.dumps({
    "jsonrpc": "2.0",
    "method": "runCmds",
    "params": {"version": 1, "cmds": cmds, "format": "json"},
    "id": "verify",
}).encode()
token = base64.b64encode(("%s:%s" % (user, password)).encode()).decode()
req = urllib.request.Request(
    "http://%s/command-api" % ip,
    data=payload,
    method="POST",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Basic %s" % token,
    },
)
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read()
        sys.stdout.buffer.write(body)
except urllib.error.HTTPError as exc:
    sys.stderr.write("eAPI HTTP %s on %s (auth values not printed)\n" % (exc.code, ip))
    sys.exit(2)
except Exception as exc:
    sys.stderr.write("eAPI error on %s: %s\n" % (ip, type(exc).__name__))
    sys.exit(3)
PY
}
