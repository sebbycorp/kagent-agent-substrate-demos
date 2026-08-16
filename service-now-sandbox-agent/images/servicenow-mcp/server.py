#!/usr/bin/env python3
"""ServiceNow ticket MCP tools (STREAMABLE_HTTP :8084 /mcp).

Read-mostly Table API wrappers for a ServiceNow personal developer
instance. Credentials come from env (Vault via ExternalSecret).
Never log or return the password. No generic shell.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

MAX_ITEMS = 40
TIMEOUT = 25.0
DEFAULT_LIST_LIMIT = 25

# Compact columns for list/search. sys_id is required for later writes.
INCIDENT_LIST_FIELDS = (
    "sys_id,number,short_description,state,priority,"
    "assigned_to,assignment_group,caller_id,sys_updated_on,active"
)
INCIDENT_GET_FIELDS = (
    INCIDENT_LIST_FIELDS
    + ",description,urgency,impact,category,opened_at,close_notes"
)
RITM_LIST_FIELDS = (
    "sys_id,number,short_description,state,stage,priority,"
    "assigned_to,assignment_group,cat_item,sys_updated_on,active"
)

READ_TOOLS = (
    "sn_whoami",
    "sn_list_incidents",
    "sn_get_incident",
    "sn_search_incidents",
    "sn_incident_summary",
    "sn_list_requested_items",
)
WRITE_TOOLS = (
    "sn_add_work_note",
    "sn_assign_incident",
)
ALL_TOOLS = READ_TOOLS + WRITE_TOOLS


def dumps(payload: Any) -> str:
    return json.dumps(payload, separators=(",", ":"), default=str)


def _err(message: str, **extra: Any) -> dict[str, Any]:
    out = {"error": True, "message": message}
    host = _public_host()
    if host:
        out["host"] = host
    out.update(extra)
    return out


def _tls_verify() -> bool:
    raw = os.environ.get("SERVICENOW_TLS_VERIFY", "true").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _raw_host() -> str:
    return os.environ.get("SERVICENOW_HOST", "").strip().rstrip("/")


def _base_url() -> str:
    raw = _raw_host()
    if not raw:
        return ""
    if raw.startswith("https://") or raw.startswith("http://"):
        return raw
    return f"https://{raw}"


def _public_host() -> str:
    """Hostname only — never userinfo, never password."""
    raw = _raw_host()
    if not raw:
        return ""
    parsed = urlparse(_base_url())
    return parsed.hostname or raw.split("@")[-1].split("/")[0]


def _username() -> str:
    return os.environ.get("SERVICENOW_USERNAME", "").strip()


def _password() -> str:
    return os.environ.get("SERVICENOW_PASSWORD", "")


def _has_creds() -> bool:
    return bool(_base_url() and _username() and _password())


def _escape_query(text: str) -> str:
    """Strip encoded-query operators so user text cannot widen a filter."""
    return (
        text.replace("^", " ")
        .replace("=", " ")
        .replace(">", " ")
        .replace("<", " ")
        .strip()
    )


def _cell(value: Any) -> Any:
    if isinstance(value, dict):
        display = value.get("display_value")
        raw = value.get("value")
        if display not in (None, "") and str(display) != str(raw):
            return {"value": raw, "display": display}
        if display not in (None, ""):
            return display
        return raw
    return value


def _compact_row(row: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in keys:
        if key in row:
            out[key] = _cell(row.get(key))
    return out


def _field_tuple(csv: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in csv.split(",") if part.strip())


def _truncate(items: list[Any]) -> dict[str, Any]:
    total = len(items)
    out: dict[str, Any] = {"count": total, "results": items[:MAX_ITEMS]}
    if total > MAX_ITEMS:
        out["truncated"] = True
        out["returned"] = MAX_ITEMS
    return out


def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not _has_creds():
        return _err("ServiceNow credentials are not set")
    import httpx

    url = f"{_base_url()}{path}"
    headers = {"Accept": "application/json"}
    try:
        with httpx.Client(
            timeout=TIMEOUT,
            verify=_tls_verify(),
            auth=(_username(), _password()),
            headers=headers,
        ) as client:
            response = client.request(method, url, params=params, json=json_body)
    except Exception as exc:  # noqa: BLE001 — surface class, never secrets
        return _err(f"{type(exc).__name__}", api=path, method=method)

    if response.status_code in (401, 403):
        return _err(
            f"HTTP {response.status_code} (auth or ACL denied)",
            api=path,
            method=method,
            status=response.status_code,
        )
    if response.status_code >= 400:
        return _err(
            f"HTTP {response.status_code}",
            api=path,
            method=method,
            status=response.status_code,
        )
    try:
        payload = response.json()
    except Exception:  # noqa: BLE001
        return _err("non-json ServiceNow response", api=path, status=response.status_code)
    if not isinstance(payload, dict):
        return _err("unexpected ServiceNow payload", api=path)
    return payload


def _table_get(table: str, params: dict[str, Any]) -> dict[str, Any]:
    query = {
        "sysparm_display_value": "all",
        "sysparm_exclude_reference_link": "true",
        **params,
    }
    return _request("GET", f"/api/now/table/{table}", params=query)


def _table_patch(table: str, sys_id: str, body: dict[str, Any]) -> dict[str, Any]:
    return _request(
        "PATCH",
        f"/api/now/table/{table}/{sys_id}",
        params={
            "sysparm_display_value": "all",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": INCIDENT_LIST_FIELDS,
        },
        json_body=body,
    )


def _looks_like_sys_id(value: str) -> bool:
    token = value.strip().lower()
    return len(token) == 32 and all(ch in "0123456789abcdef" for ch in token)


def _resolve_incident(number_or_sys_id: str) -> dict[str, Any]:
    token = (number_or_sys_id or "").strip()
    if not token:
        return _err("incident number or sys_id is required")
    if _looks_like_sys_id(token):
        query = f"sys_id={token}"
    else:
        query = f"number={_escape_query(token)}"
    payload = _table_get(
        "incident",
        {
            "sysparm_query": query,
            "sysparm_limit": "2",
            "sysparm_fields": INCIDENT_GET_FIELDS,
        },
    )
    if payload.get("error"):
        return payload
    rows = payload.get("result") or []
    if not rows:
        return _err("incident not found", query=token)
    if len(rows) > 1:
        return _err("incident query matched more than one row", query=token)
    return {"result": rows[0]}


def _sys_id_of(row: dict[str, Any]) -> str:
    cell = _cell(row.get("sys_id"))
    if isinstance(cell, dict):
        return str(cell.get("value") or "")
    return str(cell or "")


def sn_whoami() -> str:
    """Return the ServiceNow instance host and the mounted user's identity. Never the password."""
    if not _has_creds():
        return dumps(_err("ServiceNow credentials are not set"))
    user = _username()
    payload = _table_get(
        "sys_user",
        {
            "sysparm_query": f"user_name={_escape_query(user)}",
            "sysparm_limit": "1",
            "sysparm_fields": "sys_id,user_name,name,email,title,active,department",
        },
    )
    if payload.get("error"):
        return dumps(payload)
    rows = payload.get("result") or []
    identity: dict[str, Any]
    if not rows:
        identity = {"user_name": user, "note": "sys_user row not readable"}
    else:
        identity = _compact_row(
            rows[0],
            ("sys_id", "user_name", "name", "email", "title", "active", "department"),
        )
    return dumps(
        {
            "host": _public_host(),
            "tls_verify": _tls_verify(),
            "user": identity,
        }
    )


def sn_list_incidents(limit: int = DEFAULT_LIST_LIMIT) -> str:
    """List open/active incidents, compact (number, state, priority, assignee)."""
    try:
        cap = max(1, min(int(limit), MAX_ITEMS))
    except (TypeError, ValueError):
        cap = DEFAULT_LIST_LIMIT
    payload = _table_get(
        "incident",
        {
            "sysparm_query": "active=true^ORDERBYDESCsys_updated_on",
            "sysparm_limit": str(cap),
            "sysparm_fields": INCIDENT_LIST_FIELDS,
        },
    )
    if payload.get("error"):
        return dumps(payload)
    keys = _field_tuple(INCIDENT_LIST_FIELDS)
    rows = [_compact_row(row, keys) for row in (payload.get("result") or [])]
    return dumps({"host": _public_host(), "filter": "active=true", **_truncate(rows)})


def sn_get_incident(number_or_sys_id: str) -> str:
    """Get one incident by number (INC…) or sys_id."""
    payload = _resolve_incident(number_or_sys_id)
    if payload.get("error"):
        return dumps(payload)
    keys = _field_tuple(INCIDENT_GET_FIELDS)
    return dumps(
        {
            "host": _public_host(),
            "incident": _compact_row(payload["result"], keys),
        }
    )


def sn_search_incidents(query: str, limit: int = DEFAULT_LIST_LIMIT) -> str:
    """Search incidents by number or short description (active first)."""
    text = _escape_query(query or "")
    if not text:
        return dumps(_err("search query is required"))
    try:
        cap = max(1, min(int(limit), MAX_ITEMS))
    except (TypeError, ValueError):
        cap = DEFAULT_LIST_LIMIT
    encoded = (
        f"numberLIKE{text}^ORshort_descriptionLIKE{text}"
        f"^ORdescriptionLIKE{text}^ORDERBYDESCsys_updated_on"
    )
    payload = _table_get(
        "incident",
        {
            "sysparm_query": encoded,
            "sysparm_limit": str(cap),
            "sysparm_fields": INCIDENT_LIST_FIELDS,
        },
    )
    if payload.get("error"):
        return dumps(payload)
    keys = _field_tuple(INCIDENT_LIST_FIELDS)
    rows = [_compact_row(row, keys) for row in (payload.get("result") or [])]
    return dumps({"host": _public_host(), "query": text, **_truncate(rows)})


def _stats_groups(field: str) -> dict[str, Any]:
    payload = _request(
        "GET",
        "/api/now/stats/incident",
        params={
            "sysparm_query": "active=true",
            "sysparm_count": "true",
            "sysparm_group_by": field,
        },
    )
    if payload.get("error"):
        return payload
    result = payload.get("result") or {}
    groups_out = []
    for group in result.get("groups") or []:
        labels = []
        for item in group.get("groupby_fields") or []:
            labels.append(
                {
                    "field": item.get("field") or field,
                    "value": item.get("value"),
                    "display": item.get("display_value") or item.get("value"),
                }
            )
        stats = group.get("stats") or {}
        try:
            count = int(stats.get("count") or 0)
        except (TypeError, ValueError):
            count = stats.get("count")
        groups_out.append({"by": labels, "count": count})
    total = (result.get("stats") or {}).get("count")
    try:
        total_n = int(total) if total is not None else sum(
            int(g["count"]) for g in groups_out if isinstance(g.get("count"), int)
        )
    except (TypeError, ValueError):
        total_n = total
    return {"total": total_n, "groups": groups_out}


def sn_incident_summary() -> str:
    """Count active incidents by state and by priority. Never invent counts."""
    by_state = _stats_groups("state")
    by_priority = _stats_groups("priority")
    errors = {}
    if by_state.get("error"):
        errors["state"] = by_state.get("message")
    if by_priority.get("error"):
        errors["priority"] = by_priority.get("message")
    return dumps(
        {
            "host": _public_host(),
            "filter": "active=true",
            "as_of_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "by_state": by_state if not by_state.get("error") else {"unavailable": by_state.get("message")},
            "by_priority": by_priority
            if not by_priority.get("error")
            else {"unavailable": by_priority.get("message")},
            "errors": errors,
        }
    )


def sn_list_requested_items(limit: int = DEFAULT_LIST_LIMIT) -> str:
    """List active catalog requested items (sc_req_item), compact."""
    try:
        cap = max(1, min(int(limit), MAX_ITEMS))
    except (TypeError, ValueError):
        cap = DEFAULT_LIST_LIMIT
    payload = _table_get(
        "sc_req_item",
        {
            "sysparm_query": "active=true^ORDERBYDESCsys_updated_on",
            "sysparm_limit": str(cap),
            "sysparm_fields": RITM_LIST_FIELDS,
        },
    )
    if payload.get("error"):
        return dumps(payload)
    keys = _field_tuple(RITM_LIST_FIELDS)
    rows = [_compact_row(row, keys) for row in (payload.get("result") or [])]
    return dumps({"host": _public_host(), "table": "sc_req_item", "filter": "active=true", **_truncate(rows)})


def sn_add_work_note(number_or_sys_id: str, note: str) -> str:
    """Add a work note on an incident (write). Ask the human before calling."""
    text = (note or "").strip()
    if not text:
        return dumps(_err("work note text is required"))
    found = _resolve_incident(number_or_sys_id)
    if found.get("error"):
        return dumps(found)
    sys_id = _sys_id_of(found["result"])
    if not sys_id:
        return dumps(_err("incident sys_id missing"))
    payload = _table_patch("incident", sys_id, {"work_notes": text})
    if payload.get("error"):
        return dumps(payload)
    row = payload.get("result") or {}
    return dumps(
        {
            "host": _public_host(),
            "updated": True,
            "action": "work_note",
            "incident": _compact_row(row, _field_tuple(INCIDENT_LIST_FIELDS)) if row else {"sys_id": sys_id},
        }
    )


def sn_assign_incident(number_or_sys_id: str, assignee: str) -> str:
    """Assign an incident to a user name or sys_id (write). Ask the human before calling."""
    who = (assignee or "").strip()
    if not who:
        return dumps(_err("assignee user_name or sys_id is required"))
    found = _resolve_incident(number_or_sys_id)
    if found.get("error"):
        return dumps(found)
    sys_id = _sys_id_of(found["result"])
    if not sys_id:
        return dumps(_err("incident sys_id missing"))
    payload = _table_patch("incident", sys_id, {"assigned_to": who})
    if payload.get("error"):
        return dumps(payload)
    row = payload.get("result") or {}
    return dumps(
        {
            "host": _public_host(),
            "updated": True,
            "action": "assign",
            "incident": _compact_row(row, _field_tuple(INCIDENT_LIST_FIELDS)) if row else {"sys_id": sys_id},
        }
    )


TOOL_FUNCS = {
    "sn_whoami": sn_whoami,
    "sn_list_incidents": sn_list_incidents,
    "sn_get_incident": sn_get_incident,
    "sn_search_incidents": sn_search_incidents,
    "sn_incident_summary": sn_incident_summary,
    "sn_list_requested_items": sn_list_requested_items,
    "sn_add_work_note": sn_add_work_note,
    "sn_assign_incident": sn_assign_incident,
}


def _self_check() -> None:
    if set(TOOL_FUNCS) != set(ALL_TOOLS):
        missing = set(ALL_TOOLS) - set(TOOL_FUNCS)
        extra = set(TOOL_FUNCS) - set(ALL_TOOLS)
        raise SystemExit(f"tool set mismatch missing={missing} extra={extra}")
    source = open(__file__, encoding="utf-8").read()
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("SERVICENOW_PASSWORD = \"") or stripped.startswith(
            "SERVICENOW_PASSWORD = '"
        ):
            raise SystemExit("literal password assignment in source")
        if stripped.startswith("password = \"") and "os.environ" not in stripped:
            raise SystemExit("literal password assignment in source")
    # No generic CLI / shell wrapper.
    if "import sub" + "process" in source:
        raise SystemExit("generic command execution is not allowed")
    if "os.sys" + "tem(" in source:
        raise SystemExit("generic command execution is not allowed")
    lowered = source.lower()
    if "authorization" in lowered and "never" not in lowered:
        # Header is set via httpx auth=; do not build raw Basic strings in tools.
        pass
    if "print(_pass" + "word" in source or "print(os.environ.get(\"SERVICENOW_PASS" + "WORD\"" in source:
        raise SystemExit("password must never be printed")


def build_mcp():
    from fastmcp import FastMCP
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    mcp = FastMCP(name="servicenow")

    @mcp.custom_route("/health", methods=["GET"])
    async def health(_request: Request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "host": _public_host(),
                "tls_verify": _tls_verify(),
            }
        )

    for name, func in TOOL_FUNCS.items():
        mcp.tool(name=name)(func)
    return mcp


def main() -> None:
    _self_check()
    if not _has_creds():
        print(
            "ServiceNow credentials are not set; tools will return an error until the Secret exists",
            file=sys.stderr,
        )
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8084"))
    mcp = build_mcp()
    mcp.run(transport="http", host=host, port=port, path="/mcp")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-check":
        _self_check()
        print("servicenow-mcp self-check ok")
        sys.exit(0)
    main()
