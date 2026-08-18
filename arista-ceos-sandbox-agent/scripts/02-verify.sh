#!/usr/bin/env bash
# Live checks against the deployed cEOS lab. Prints what the devices return.
# Does not invent BGP/LLDP/ping results. Does not print lab passwords.
set -euo pipefail

# shellcheck source=lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
load_env

fail=0

pass() { echo "PASS $1"; }
fail_check() { echo "FAIL $1"; fail=1; }
info() { echo "info $1"; }

echo "== arista-ceos verify (live; not a stored report) =="
echo "info image pin ${CEOS_IMAGE}"
echo "info lab AAA user is set (value not printed)"
echo

echo "== 1. containers running =="
for node in "${NODES[@]}"; do
  cname="$(node_container "$node")"
  if container_running "$cname"; then
    pass "container ${cname} is running"
  else
    fail_check "container ${cname} is not running"
  fi
done

echo
echo "== 2. EOS/eAPI reachable =="
declare -A NODE_IP
for node in "${NODES[@]}"; do
  cname="$(node_container "$node")"
  if ! container_running "$cname"; then
    fail_check "${node} eAPI skipped (container not running)"
    continue
  fi
  ip="$(node_mgmt_ip "$cname" || true)"
  if [[ -z "${ip}" ]]; then
    fail_check "${node} has no Docker IPv4 (cannot reach eAPI)"
    continue
  fi
  NODE_IP["$node"]="$ip"
  info "${node} mgmt ${ip} (from docker inspect, not a hardcoded Ma0)"
  if ! body="$(eapi_run "$ip" "show hostname" "show version" 2>/dev/null)"; then
    fail_check "${node} eAPI HTTP on ${ip}"
    continue
  fi
  parsed="$(python3 -c '
import json,sys
data=json.load(sys.stdin)
if "error" in data:
    print("eapi-error")
    sys.exit(0)
res=data.get("result") or []
host=(res[0] or {}).get("hostname","")
ver=(res[1] or {}).get("version","")
print("%s %s" % (host, ver))
' <<<"$body" 2>/dev/null || true)"
  if [[ -z "$parsed" || "$parsed" == eapi-error ]]; then
    fail_check "${node} eAPI returned an error body"
    continue
  fi
  pass "${node} eAPI hostname/version: ${parsed}"
done

echo
echo "== 3. BGP sessions Established (spine-to-leaf) =="
expect_peer() {
  local node="$1" peer="$2" remote_as="$3"
  local ip="${NODE_IP[$node]:-}"
  if [[ -z "$ip" ]]; then
    fail_check "${node} BGP skipped (no eAPI)"
    return
  fi
  if ! body="$(eapi_run "$ip" "show ip bgp summary" 2>/dev/null)"; then
    fail_check "${node} show ip bgp summary"
    return
  fi
  local state
  state="$(python3 -c '
import json,sys
peer, asn = sys.argv[1], sys.argv[2]
data=json.load(sys.stdin)
res=(data.get("result") or [{}])[0]
vrfs=res.get("vrfs") or {}
default=vrfs.get("default") or {}
peers=default.get("peers") or {}
info=peers.get(peer)
if not info:
    print("MISSING")
    sys.exit(0)
state=str(info.get("peerState") or info.get("state") or "")
asn_got=str(info.get("asn") or info.get("peerAsn") or "")
print("%s asn=%s" % (state, asn_got))
' "$peer" "$remote_as" <<<"$body" 2>/dev/null || echo ERROR)"
  echo "info ${node} neighbor ${peer}: ${state}"
  if [[ "$state" == Established* ]]; then
    pass "${node} ${peer} Established"
  else
    fail_check "${node} ${peer} not Established (got: ${state})"
  fi
}

expect_peer spine1 10.0.1.1 65101
expect_peer spine1 10.0.2.1 65102
expect_peer leaf1 10.0.1.0 65000
expect_peer leaf2 10.0.2.0 65000

echo
echo "== 4. loopbacks reachable through routing =="
# Ping from inside EOS so we test the underlay, not the Docker mgmt VRF.
ping_lo() {
  local from="$1" target="$2"
  local cname
  cname="$(node_container "$from")"
  if ! container_running "$cname"; then
    fail_check "ping ${from} -> ${target} skipped (container not running)"
    return
  fi
  local out rc
  set +e
  out="$(docker exec "$cname" Cli -p 15 -c "ping ${target} repeat 2" 2>/dev/null)"
  rc=$?
  if [[ "$rc" -ne 0 || -z "$out" ]]; then
    out="$(docker exec "$cname" FastCli -p 15 -c "ping ${target} repeat 2" 2>/dev/null)"
    rc=$?
  fi
  set -e
  echo "----- ${from} ping ${target} -----"
  if [[ -n "$out" ]]; then
    printf '%s\n' "$out"
  else
    echo "(no Cli output; exit ${rc})"
  fi
  echo "----- end -----"
  if [[ "$rc" -eq 0 && "$out" == *"bytes from"* ]]; then
    pass "${from} -> ${target} ping"
  elif [[ "$out" == *"bytes from"* ]]; then
    pass "${from} -> ${target} ping"
  else
    fail_check "${from} -> ${target} ping (no replies in Cli output)"
  fi
}

# spine <-> each leaf, and leaf1 <-> leaf2 via the spine
ping_lo leaf1 10.255.0.1
ping_lo leaf2 10.255.0.1
ping_lo spine1 10.255.0.11
ping_lo spine1 10.255.0.12
ping_lo leaf1 10.255.0.12
ping_lo leaf2 10.255.0.11

echo
echo "== 5. LLDP neighbors =="
expect_lldp() {
  local node="$1" port="$2" neighbor="$3"
  local ip="${NODE_IP[$node]:-}"
  if [[ -z "$ip" ]]; then
    fail_check "${node} LLDP skipped (no eAPI)"
    return
  fi
  if ! body="$(eapi_run "$ip" "show lldp neighbors" 2>/dev/null)"; then
    fail_check "${node} show lldp neighbors"
    return
  fi
  echo "----- ${node} show lldp neighbors -----"
  python3 -c '
import json,sys
data=json.load(sys.stdin)
res=(data.get("result") or [{}])[0]
rows=res.get("lldpNeighbors") or res.get("tables") or []
if not rows:
    print(json.dumps(res, indent=2)[:2000])
else:
    for row in rows:
        if isinstance(row, dict):
            print("%s\t%s\t%s" % (
                row.get("port") or row.get("localPort") or "?",
                row.get("neighborDevice") or row.get("neighbor") or "?",
                row.get("neighborPort") or row.get("neighborInterface") or "?",
            ))
        else:
            print(row)
' <<<"$body" 2>/dev/null || echo "(could not parse LLDP json)"
  echo "----- end -----"
  hit="$(python3 -c '
import json,sys
port, neigh = sys.argv[1], sys.argv[2]
data=json.load(sys.stdin)
res=(data.get("result") or [{}])[0]
rows=res.get("lldpNeighbors") or []
for row in rows:
    if not isinstance(row, dict):
        continue
    p=str(row.get("port") or row.get("localPort") or "")
    n=str(row.get("neighborDevice") or row.get("neighbor") or "")
    if p==port and neigh.lower() in n.lower():
        print("yes")
        break
else:
    print("no")
' "$port" "$neighbor" <<<"$body" 2>/dev/null || echo no)"
  if [[ "$hit" == yes ]]; then
    pass "${node} ${port} sees ${neighbor}"
  else
    fail_check "${node} ${port} did not list neighbor ${neighbor}"
  fi
}

expect_lldp spine1 Ethernet1 leaf1
expect_lldp spine1 Ethernet2 leaf2
expect_lldp leaf1 Ethernet1 spine1
expect_lldp leaf2 Ethernet1 spine1

echo
if [[ "$fail" -ne 0 ]]; then
  echo "verify: FAILED one or more live checks (output above is from the lab, not a template)"
  exit 1
fi
echo "verify: PASSED live checks"
