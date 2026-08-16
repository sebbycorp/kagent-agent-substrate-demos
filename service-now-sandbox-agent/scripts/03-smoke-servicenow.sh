#!/usr/bin/env bash
# ServiceNow smoke: cluster objects (no Secret yaml) and optional Table API.
# Uses caller env for username/password. Does not print secrets.
# Do not run with `set -x` — that would echo the password.
set -euo pipefail

K3S_CONTAINER="${K3S_CONTAINER:-k3s-viper}"

echo "== cluster objects (no secret values) =="
if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "${K3S_CONTAINER}"; then
  docker exec "${K3S_CONTAINER}" kubectl -n kagent get \
    sandboxagent servicenow \
    remotemcpserver servicenow-mcp \
    externalsecret servicenow-mcp \
    deploy servicenow-mcp \
    2>/dev/null || echo "warn servicenow objects not applied yet"
  echo
  echo "info skipping kubectl get secret -o yaml (would print the password)"
else
  echo "info ${K3S_CONTAINER} not visible; skip cluster checks"
fi

if [[ -z "${SERVICENOW_USERNAME:-}" || -z "${SERVICENOW_PASSWORD:-}" ]]; then
  echo
  echo "info SERVICENOW_USERNAME / SERVICENOW_PASSWORD not set; skip Table API smoke"
  echo "smoke ok (cluster checks only; no secrets printed)"
  exit 0
fi

HOST="${SERVICENOW_HOST:-https://dev203166.service-now.com}"
export SERVICENOW_HOST="${HOST}"
export SERVICENOW_USERNAME
export SERVICENOW_PASSWORD

echo
echo "== Table API (host only: ${HOST%%@*}; password not printed) =="
python3 - <<'PY'
import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse

host = os.environ.get("SERVICENOW_HOST", "").strip().rstrip("/")
if host and not host.startswith(("https://", "http://")):
    host = "https://" + host
user = os.environ.get("SERVICENOW_USERNAME", "")
password = os.environ.get("SERVICENOW_PASSWORD", "")
if not host or not user or not password:
    print("missing host or credentials", file=sys.stderr)
    sys.exit(1)

parsed = urlparse(host)
public = parsed.hostname or host
print(f"host {public}")

password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
password_mgr.add_password(None, host, user, password)
opener = urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(password_mgr))

url = (
    host
    + "/api/now/table/incident"
    + "?sysparm_limit=5"
    + "&sysparm_fields=number,state,priority,short_description,active"
    + "&sysparm_query=active=true^ORDERBYDESCsys_updated_on"
    + "&sysparm_display_value=true"
)
req = urllib.request.Request(url, headers={"Accept": "application/json"})
try:
    with opener.open(req, timeout=25) as resp:
        payload = json.loads(resp.read().decode())
except urllib.error.HTTPError as exc:
    print(f"HTTP {exc.code} (auth or ACL denied)" if exc.code in (401, 403) else f"HTTP {exc.code}")
    sys.exit(1)
except Exception as exc:  # noqa: BLE001
    print(type(exc).__name__)
    sys.exit(1)

rows = payload.get("result") or []
print(f"active incidents returned: {len(rows)}")
for row in rows:
    number = row.get("number")
    state = row.get("state")
    priority = row.get("priority")
    print(f"  {number}  state={state}  priority={priority}")
PY

echo
echo "smoke ok (numbers above are ground truth for the kagent chat)"
