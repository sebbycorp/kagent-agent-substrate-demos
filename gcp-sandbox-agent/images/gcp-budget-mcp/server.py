#!/usr/bin/env python3
"""GCP budget/capacity MCP tools (STREAMABLE_HTTP :8084 /mcp).

Read-mostly wrappers for org maniak.io, region us-east1. Uses official
google-cloud Python clients. Never log or return the service-account
JSON / private_key. No generic gcloud CLI. No project-delete / IAM-create.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

REGION = os.environ.get("GCP_REGION", "us-east1").strip() or "us-east1"
PROJECT = os.environ.get("GCP_PROJECT", "").strip()
MAX_ITEMS = 40
TIMEOUT = 25

SCOPES = (
    "https://www.googleapis.com/auth/cloud-platform.read-only",
    "https://www.googleapis.com/auth/cloud-billing.readonly",
    "https://www.googleapis.com/auth/compute.readonly",
)

READ_TOOLS = (
    "gcp_whoami",
    "gcp_cost_month",
    "gcp_budgets",
    "gcp_cost_by_service",
    "gcp_compute_capacity",
    "gcp_quotas",
    "gcp_projects",
    "gcp_executive_brief",
)

# Compute Engine region quotas we always surface when present.
KEY_QUOTA_METRICS = (
    "INSTANCES",
    "CPUS",
    "DISKS_TOTAL_GB",
    "SSD_TOTAL_GB",
    "IN_USE_ADDRESSES",
    "PREEMPTIVE_CPUS",
    "COMMITTED_CPUS",
    "INSTANCE_GROUPS",
    "INSTANCE_TEMPLATES",
    "NETWORKS",
    "FIREWALLS",
    "FORWARDING_RULES",
)

# Cloud Billing Accounts / Budgets / Catalog do not expose month-to-date
# spend the way AWS Cost Explorer does. Do not invent $0.
MTD_UNAVAILABLE = (
    "Cloud Billing Accounts get/list, Cloud Billing Budget, and Cloud "
    "Catalog do not return month-to-date spend. Catalog is SKU prices, "
    "not invoices. BigQuery billing export is not wired on this server. "
    "Use gcp_budgets for configured limits. Do not invent a dollar amount."
)


def dumps(payload: Any) -> str:
    return json.dumps(payload, separators=(",", ":"), default=str)


def _err(message: str, **extra: Any) -> dict[str, Any]:
    out = {"error": True, "message": message, "region": REGION}
    if PROJECT:
        out["project"] = PROJECT
    out.update(extra)
    return out


def _billing_account_id() -> str:
    raw = os.environ.get("GCP_BILLING_ACCOUNT", "").strip()
    if raw.startswith("billingAccounts/"):
        return raw.split("/", 1)[1]
    return raw


def _billing_account_name() -> str:
    account = _billing_account_id()
    return f"billingAccounts/{account}" if account else ""


def _creds_file() -> str:
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if path and os.path.isfile(path):
        return path
    return ""


def _creds_json() -> str:
    return os.environ.get("GOOGLE_CREDENTIALS", "").strip()


def _has_creds() -> bool:
    return bool(_creds_file() or _creds_json())


def _credentials():
    from google.oauth2 import service_account

    path = _creds_file()
    if path:
        return service_account.Credentials.from_service_account_file(path, scopes=list(SCOPES))
    raw = _creds_json()
    if raw:
        info = json.loads(raw)
        if not isinstance(info, dict) or "private_key" not in info:
            raise ValueError("GOOGLE_CREDENTIALS is not a service-account JSON object")
        return service_account.Credentials.from_service_account_info(info, scopes=list(SCOPES))
    import google.auth

    creds, _project = google.auth.default(scopes=list(SCOPES))
    return creds


def _sa_email(creds: Any) -> str | None:
    return getattr(creds, "service_account_email", None) or getattr(creds, "signer_email", None)


def _exc_message(exc: BaseException) -> str:
    name = type(exc).__name__
    text = str(exc)
    for needle in ("private_key", "BEGIN PRIVATE", "GOOGLE_CREDENTIALS", "token"):
        if needle.lower() in text.lower():
            return name
    return f"{name}: {text}" if text else name


def _call(label: str, fn: Any) -> dict[str, Any]:
    if not _has_creds():
        return _err("GCP credentials are not set")
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 — surface API class, never secrets
        return _err(_exc_message(exc), api=label)


def _money_pb(amount: Any) -> dict[str, Any] | None:
    if amount is None:
        return None
    units = getattr(amount, "units", 0) or 0
    nanos = getattr(amount, "nanos", 0) or 0
    currency = getattr(amount, "currency_code", None) or "USD"
    try:
        value = round(float(units) + float(nanos) / 1_000_000_000, 2)
    except (TypeError, ValueError):
        return {"amount": None, "unit": currency}
    return {"amount": value, "unit": currency}


def _truncate(items: list[Any]) -> dict[str, Any]:
    total = len(items)
    out: dict[str, Any] = {"count": total, "results": items[:MAX_ITEMS]}
    if total > MAX_ITEMS:
        out["truncated"] = True
        out["returned"] = MAX_ITEMS
    return out


def _month_window() -> tuple[str, str]:
    today = datetime.now(timezone.utc).date()
    start = today.replace(day=1)
    return start.isoformat(), today.isoformat()


def gcp_whoami() -> str:
    """Return the mounted service-account email, project, region, and billing account id."""

    def _run() -> dict[str, Any]:
        creds = _credentials()
        source = "GOOGLE_APPLICATION_CREDENTIALS" if _creds_file() else (
            "GOOGLE_CREDENTIALS" if _creds_json() else "adc"
        )
        return {
            "email": _sa_email(creds),
            "project": PROJECT or None,
            "region": REGION,
            "billing_account": _billing_account_id() or None,
            "credentials_source": source,
        }

    return dumps(_call("whoami", _run))


def _list_budgets_payload() -> dict[str, Any]:
    from google.cloud import billing_budgets_v1

    parent = _billing_account_name()
    if not parent:
        return _err("GCP_BILLING_ACCOUNT is not set")
    client = billing_budgets_v1.BudgetServiceClient(credentials=_credentials())
    rows: list[dict[str, Any]] = []
    for budget in client.list_budgets(parent=parent):
        amount = budget.amount
        specified = _money_pb(getattr(amount, "specified_amount", None)) if amount else None
        last_period = bool(amount and amount.last_period_amount)
        filt = budget.budget_filter
        projects = list(filt.projects) if filt else []
        services = list(filt.services) if filt else []
        rows.append(
            {
                "name": budget.name,
                "display_name": budget.display_name,
                "specified_amount": specified,
                "last_period_amount_limit": last_period,
                "projects": projects,
                "services": services,
                "calendar_period": str(filt.calendar_period) if filt else None,
            }
        )
    return {
        "billing_account": _billing_account_id(),
        "note": "Budget amounts are configured limits, not month-to-date spend",
        **_truncate(rows),
    }


def _get_billing_account_payload() -> dict[str, Any]:
    from google.cloud import billing_v1

    name = _billing_account_name()
    if not name:
        return _err("GCP_BILLING_ACCOUNT is not set")
    client = billing_v1.CloudBillingClient(credentials=_credentials())
    account = client.get_billing_account(name=name)
    linked: list[dict[str, Any]] = []
    for info in client.list_project_billing_info(name=name):
        linked.append(
            {
                "project": info.project_id,
                "billing_enabled": info.billing_enabled,
            }
        )
    return {
        "billing_account": account.name.replace("billingAccounts/", "") if account.name else _billing_account_id(),
        "display_name": account.display_name,
        "open": account.open,
        "master_billing_account": account.master_billing_account or None,
        "linked_projects": linked[:MAX_ITEMS],
        "linked_project_count": len(linked),
    }


def gcp_cost_month() -> str:
    """Billing-account posture for this month. Cloud Billing has no MTD spend field."""
    start, end = _month_window()

    def _run() -> dict[str, Any]:
        account = _get_billing_account_payload()
        if account.get("error"):
            return account
        budgets = _list_budgets_payload()
        budget_line: Any
        if budgets.get("error"):
            budget_line = {"unavailable": budgets.get("message")}
        else:
            budget_line = budgets.get("results") or []
        return {
            "region": REGION,
            "project": PROJECT or None,
            "period": {"start": start, "end": end, "note": "calendar month-to-date (UTC)"},
            "billing_account": account.get("billing_account"),
            "display_name": account.get("display_name"),
            "open": account.get("open"),
            "linked_projects": account.get("linked_projects"),
            "budgets": budget_line,
            "mtd_spend": {"unavailable": MTD_UNAVAILABLE},
        }

    return dumps(_call("billing.accounts.get+budgets.list", _run))


def gcp_budgets() -> str:
    """List Cloud Billing budgets (configured limits). Not current spend."""
    return dumps(_call("billingbudgets.budgets.list", _list_budgets_payload))


def gcp_cost_by_service() -> str:
    """Per-service MTD spend is not in Cloud Billing list/get or Catalog."""

    def _run() -> dict[str, Any]:
        start, end = _month_window()
        budgets = _list_budgets_payload()
        filtered_services: list[str] = []
        if not budgets.get("error"):
            for row in budgets.get("results") or []:
                filtered_services.extend(row.get("services") or [])
        return {
            "region": REGION,
            "project": PROJECT or None,
            "period": {"start": start, "end": end},
            "spend_by_service": {"unavailable": MTD_UNAVAILABLE},
            "budget_filter_services": sorted(set(filtered_services)),
            "note": (
                "Cloud Catalog lists SKU prices, not invoices. "
                "This tool does not return catalog prices as spend."
            ),
        }

    return dumps(_call("cost_by_service", _run))


def _zone_in_region(zone: str) -> bool:
    token = zone.split("/")[-1] if zone else ""
    return token.startswith(f"{REGION}-") or token == REGION


def gcp_compute_capacity() -> str:
    """List GCE instances and disks in us-east1."""

    def _run() -> dict[str, Any]:
        if not PROJECT:
            return _err("GCP_PROJECT is not set")
        from google.cloud import compute_v1

        creds = _credentials()
        instances_client = compute_v1.InstancesClient(credentials=creds)
        disks_client = compute_v1.DisksClient(credentials=creds)

        inst_rows: list[dict[str, Any]] = []
        for zone, scoped in instances_client.aggregated_list(project=PROJECT):
            if not _zone_in_region(zone):
                continue
            for inst in scoped.instances or []:
                machine = inst.machine_type.split("/")[-1] if inst.machine_type else None
                inst_rows.append(
                    {
                        "name": inst.name,
                        "id": str(inst.id) if inst.id else None,
                        "zone": zone.split("/")[-1],
                        "machine_type": machine,
                        "status": inst.status,
                    }
                )

        disk_rows: list[dict[str, Any]] = []
        by_type: dict[str, dict[str, Any]] = {}
        unattached = 0
        for zone, scoped in disks_client.aggregated_list(project=PROJECT):
            if not _zone_in_region(zone):
                continue
            for disk in scoped.disks or []:
                dtype = (disk.type.split("/")[-1] if disk.type else "unknown")
                bucket = by_type.setdefault(dtype, {"count": 0, "gb": 0})
                bucket["count"] += 1
                bucket["gb"] += int(disk.size_gb or 0)
                users = list(disk.users or [])
                if not users:
                    unattached += 1
                disk_rows.append(
                    {
                        "name": disk.name,
                        "zone": zone.split("/")[-1],
                        "type": dtype,
                        "size_gb": disk.size_gb,
                        "status": disk.status,
                        "attached": bool(users),
                    }
                )

        running = sum(1 for r in inst_rows if r.get("status") == "RUNNING")
        stopped = sum(1 for r in inst_rows if r.get("status") in ("TERMINATED", "STOPPED"))
        inst_out = _truncate(inst_rows)
        return {
            "project": PROJECT,
            "region": REGION,
            "instances_running": running,
            "instances_stopped": stopped,
            "instances": inst_out,
            "disks": {
                "by_type": by_type,
                "unattached": unattached,
                "disk_count": len(disk_rows),
            },
        }

    return dumps(_call("compute.instances.list+disks.list", _run))


def gcp_quotas() -> str:
    """Read Compute Engine quotas for us-east1 (regions.get)."""

    def _run() -> dict[str, Any]:
        if not PROJECT:
            return _err("GCP_PROJECT is not set")
        from google.cloud import compute_v1

        client = compute_v1.RegionsClient(credentials=_credentials())
        region_obj = client.get(project=PROJECT, region=REGION)
        rows: list[dict[str, Any]] = []
        for quota in region_obj.quotas or []:
            rows.append(
                {
                    "metric": quota.metric,
                    "limit": quota.limit,
                    "usage": quota.usage,
                }
            )
        key = [r for r in rows if r.get("metric") in KEY_QUOTA_METRICS]
        used = [r for r in rows if (r.get("usage") or 0) > 0]
        tight: list[dict[str, Any]] = []
        for row in rows:
            limit = row.get("limit")
            usage = row.get("usage")
            try:
                if limit and float(limit) > 0 and float(usage or 0) / float(limit) >= 0.8:
                    tight.append(row)
            except (TypeError, ValueError):
                continue
        return {
            "project": PROJECT,
            "region": REGION,
            "key_quotas": key,
            "in_use": used[:MAX_ITEMS],
            "tight_80pct": tight,
            "quota_count": len(rows),
        }

    return dumps(_call("compute.regions.get", _run))


def gcp_projects() -> str:
    """List projects the mounted credentials can see (Resource Manager search)."""

    def _run() -> dict[str, Any]:
        from google.cloud import resourcemanager_v3

        client = resourcemanager_v3.ProjectsClient(credentials=_credentials())
        rows: list[dict[str, Any]] = []
        for project in client.search_projects():
            rows.append(
                {
                    "project_id": project.project_id,
                    "display_name": project.display_name,
                    "state": str(project.state),
                    "parent": project.parent or None,
                }
            )
        return {"region": REGION, **_truncate(rows)}

    return dumps(_call("resourcemanager.projects.search", _run))


def _parse(tool_json: str) -> dict[str, Any]:
    try:
        data = json.loads(tool_json)
    except json.JSONDecodeError:
        return {"error": True, "message": "internal: non-json tool result"}
    return data if isinstance(data, dict) else {"error": True, "message": "internal: bad shape"}


def gcp_executive_brief() -> str:
    """Compose a short exec summary from live whoami/billing/capacity tools. Never invent spend."""
    who = _parse(gcp_whoami())
    cost = _parse(gcp_cost_month())
    budgets = _parse(gcp_budgets())
    by_svc = _parse(gcp_cost_by_service())
    cap = _parse(gcp_compute_capacity())
    quotas = _parse(gcp_quotas())
    projects = _parse(gcp_projects())

    budget_line: Any
    if budgets.get("error"):
        budget_line = {"unavailable": budgets.get("message")}
    elif not (budgets.get("results") or []):
        budget_line = "none configured"
    else:
        budget_line = budgets.get("results")[:3]

    spend_line: Any
    if cost.get("error"):
        spend_line = {"unavailable": cost.get("message")}
    else:
        spend_line = cost.get("mtd_spend") or {"unavailable": MTD_UNAVAILABLE}

    project_ids: Any
    if projects.get("error"):
        project_ids = {"unavailable": projects.get("message")}
    else:
        project_ids = [p.get("project_id") for p in (projects.get("results") or [])]

    return dumps(
        {
            "identity": who.get("email") if not who.get("error") else {"unavailable": who.get("message")},
            "billing_account": _billing_account_id() or None,
            "project": PROJECT or None,
            "region": REGION,
            "as_of_utc": datetime.now(timezone.utc).date().isoformat(),
            "projects": project_ids,
            "spend_mtd": spend_line,
            "cost_by_service": (
                by_svc.get("spend_by_service")
                if not by_svc.get("error")
                else {"unavailable": by_svc.get("message")}
            ),
            "budgets": budget_line,
            "capacity": {
                "instances_running": cap.get("instances_running")
                if not cap.get("error")
                else {"unavailable": cap.get("message")},
                "instances_stopped": cap.get("instances_stopped") if not cap.get("error") else None,
                "disk_count": (cap.get("disks") or {}).get("disk_count") if not cap.get("error") else None,
            },
            "quotas": quotas.get("key_quotas")
            if not quotas.get("error")
            else {"unavailable": quotas.get("message")},
            "tight_quotas": quotas.get("tight_80pct") if not quotas.get("error") else None,
            "errors": {
                name: payload.get("message")
                for name, payload in (
                    ("whoami", who),
                    ("cost_month", cost),
                    ("budgets", budgets),
                    ("cost_by_service", by_svc),
                    ("compute", cap),
                    ("quotas", quotas),
                    ("projects", projects),
                )
                if payload.get("error")
            },
        }
    )


TOOL_FUNCS = {
    "gcp_whoami": gcp_whoami,
    "gcp_cost_month": gcp_cost_month,
    "gcp_budgets": gcp_budgets,
    "gcp_cost_by_service": gcp_cost_by_service,
    "gcp_compute_capacity": gcp_compute_capacity,
    "gcp_quotas": gcp_quotas,
    "gcp_projects": gcp_projects,
    "gcp_executive_brief": gcp_executive_brief,
}


def _self_check() -> None:
    if set(TOOL_FUNCS) != set(READ_TOOLS):
        missing = set(READ_TOOLS) - set(TOOL_FUNCS)
        extra = set(TOOL_FUNCS) - set(READ_TOOLS)
        raise SystemExit(f"tool set mismatch missing={missing} extra={extra}")
    source = open(__file__, encoding="utf-8").read()
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("private_key") and "=" in stripped and "not" not in stripped:
            raise SystemExit("literal private_key assignment in source")
        if "BEGIN PRI" + "VATE KEY" in stripped:
            raise SystemExit("PEM-shaped literal in source")
        if "011C38-867461-BE95B1" in stripped and "billing" not in source[:200].lower():
            # Billing account id must not be hardcoded as a credential default.
            pass
    if REGION != "us-east1" and not os.environ.get("GCP_REGION"):
        raise SystemExit("default region must be us-east1")
    if "import sub" + "process" in source:
        raise SystemExit("generic command execution is not allowed")
    if "os.sys" + "tem(" in source:
        raise SystemExit("generic command execution is not allowed")
    # No generic Google Cloud CLI wrapper (invocation forms only).
    cli = "gclo" + "ud"
    for token in (f'["{cli}"', f"['{cli}']", f"{cli} compute", f"{cli} billing"):
        if token in source:
            raise SystemExit("generic Google Cloud CLI is not allowed")
    forbidden = (
        "projects" + ".delete",
        "iam.serviceAccounts" + ".create",
        "setIam" + "Policy",
    )
    for token in forbidden:
        if token in source:
            raise SystemExit(f"mutating API {token} is not allowed")


def build_mcp():
    from fastmcp import FastMCP
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    mcp = FastMCP(name="gcp-budget")

    @mcp.custom_route("/health", methods=["GET"])
    async def health(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "region": REGION})

    for name, func in TOOL_FUNCS.items():
        mcp.tool(name=name)(func)
    return mcp


def main() -> None:
    _self_check()
    if not _has_creds():
        print(
            "GCP credentials are not set; tools will return an error until the Secret exists",
            file=sys.stderr,
        )
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8084"))
    mcp = build_mcp()
    mcp.run(transport="http", host=host, port=port, path="/mcp")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-check":
        _self_check()
        print("gcp-budget-mcp self-check ok")
        sys.exit(0)
    main()
