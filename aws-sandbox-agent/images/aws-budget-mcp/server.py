#!/usr/bin/env python3
"""AWS budget/capacity MCP tools (STREAMABLE_HTTP :8084 /mcp).

Read-mostly wrappers for us-east-2. Cost Explorer and Budgets use the
us-east-1 endpoint (AWS global services) but filter to us-east-2 where
the API allows it. Never log or return credentials.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone
from typing import Any

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-2").strip() or "us-east-2"
COST_REGION = os.environ.get("AWS_COST_REGION", REGION).strip() or REGION
CE_ENDPOINT_REGION = "us-east-1"
BUDGETS_ENDPOINT_REGION = "us-east-1"
MAX_ITEMS = 40
TIMEOUT = 25

READ_TOOLS = (
    "aws_whoami",
    "aws_cost_month",
    "aws_cost_by_service",
    "aws_budgets",
    "aws_ec2_capacity",
    "aws_asg",
    "aws_rds",
    "aws_ebs_summary",
    "aws_service_quotas",
    "aws_rightsizing_hints",
    "aws_executive_brief",
)

# Key compute quotas (service code, quota code, label).
# Codes are AWS-published identifiers; if GetServiceQuota fails we say so.
QUOTAS = (
    ("ec2", "L-1216C47A", "Running On-Demand Standard (A,C,D,H,I,M,R,T,Z) vCPU"),
    ("ec2", "L-34B43A08", "All Standard (A,C,D,H,I,M,R,T,Z) Spot Instance Requests"),
    ("ec2", "L-0263D0A3", "EC2-VPC Elastic IPs"),
    ("rds", "L-7E414307", "DB instances"),
    ("ebs", "L-D18FCD1D", "Storage for General Purpose SSD (gp3), TiB"),
)


def dumps(payload: Any) -> str:
    return json.dumps(payload, separators=(",", ":"), default=str)


def _err(message: str, **extra: Any) -> dict[str, Any]:
    out = {"error": True, "message": message, "region": REGION}
    out.update(extra)
    return out


def _has_creds() -> bool:
    return bool(os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"))


def _client(service: str, region: str):
    import boto3
    from botocore.config import Config

    return boto3.client(
        service,
        region_name=region,
        config=Config(connect_timeout=TIMEOUT, read_timeout=TIMEOUT, retries={"max_attempts": 2}),
    )


def _call(service: str, region: str, method: str, **kwargs: Any) -> dict[str, Any]:
    if not _has_creds():
        return _err("AWS credentials are not set")
    try:
        client = _client(service, region)
        result = getattr(client, method)(**kwargs)
    except Exception as exc:  # noqa: BLE001 — surface API class, never secrets
        name = type(exc).__name__
        code = ""
        if hasattr(exc, "response") and isinstance(exc.response, dict):
            code = str(exc.response.get("Error", {}).get("Code", ""))
        msg = f"{name}" + (f":{code}" if code else "")
        return _err(msg, service=service, api=method, api_region=region)
    if isinstance(result, dict):
        result.pop("ResponseMetadata", None)
        return result
    return {"results": result}


def _month_window() -> tuple[str, str]:
    today = datetime.now(timezone.utc).date()
    start = today.replace(day=1)
    # CE End is exclusive; tomorrow covers "through today".
    end = date.fromordinal(today.toordinal() + 1)
    return start.isoformat(), end.isoformat()


def _money(amount: Any, unit: str | None = None) -> dict[str, Any]:
    try:
        value = round(float(amount), 2)
    except (TypeError, ValueError):
        value = amount
    out: dict[str, Any] = {"amount": value}
    if unit:
        out["unit"] = unit
    return out


def _truncate(items: list[Any]) -> dict[str, Any]:
    total = len(items)
    out: dict[str, Any] = {"count": total, "results": items[:MAX_ITEMS]}
    if total > MAX_ITEMS:
        out["truncated"] = True
        out["returned"] = MAX_ITEMS
    return out


def aws_whoami() -> str:
    """Return the AWS account, ARN, and user id for the mounted credentials."""
    payload = _call("sts", REGION, "get_caller_identity")
    if payload.get("error"):
        return dumps(payload)
    arn = str(payload.get("Arn", ""))
    # Never return access-key-shaped material; STS UserId is fine.
    return dumps(
        {
            "account": payload.get("Account"),
            "arn": arn,
            "user_id": payload.get("UserId"),
            "region": REGION,
            "cost_filter_region": COST_REGION,
        }
    )


def _ce_filter() -> dict[str, Any]:
    return {"Dimensions": {"Key": "REGION", "Values": [COST_REGION]}}


def aws_cost_month() -> str:
    """Month-to-date unblended cost for us-east-2 (Cost Explorer, us-east-1 endpoint)."""
    start, end = _month_window()
    payload = _call(
        "ce",
        CE_ENDPOINT_REGION,
        "get_cost_and_usage",
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        Filter=_ce_filter(),
    )
    if payload.get("error"):
        return dumps(payload)
    results = payload.get("ResultsByTime") or []
    total = {"amount": 0.0, "unit": "USD"}
    if results:
        cost = (results[0].get("Total") or {}).get("UnblendedCost") or {}
        total = _money(cost.get("Amount"), cost.get("Unit") or "USD")
    return dumps(
        {
            "region_filter": COST_REGION,
            "period": {"start": start, "end": end, "note": "CE End is exclusive"},
            "unblended_cost": total,
            "estimated": bool(results and results[0].get("Estimated")),
        }
    )


def aws_cost_by_service() -> str:
    """Month-to-date unblended cost by SERVICE for us-east-2."""
    start, end = _month_window()
    payload = _call(
        "ce",
        CE_ENDPOINT_REGION,
        "get_cost_and_usage",
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        Filter=_ce_filter(),
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    if payload.get("error"):
        return dumps(payload)
    rows: list[dict[str, Any]] = []
    for block in payload.get("ResultsByTime") or []:
        for group in block.get("Groups") or []:
            keys = group.get("Keys") or ["unknown"]
            cost = (group.get("Metrics") or {}).get("UnblendedCost") or {}
            rows.append(
                {
                    "service": keys[0],
                    **_money(cost.get("Amount"), cost.get("Unit") or "USD"),
                }
            )
    rows.sort(key=lambda r: float(r.get("amount") or 0), reverse=True)
    return dumps(
        {
            "region_filter": COST_REGION,
            "period": {"start": start, "end": end},
            **_truncate(rows),
        }
    )


def aws_budgets() -> str:
    """List AWS Budgets (View-only). Budgets API is us-east-1; spend is account-wide."""
    ident = _call("sts", REGION, "get_caller_identity")
    if ident.get("error"):
        return dumps(ident)
    account = ident.get("Account")
    payload = _call(
        "budgets",
        BUDGETS_ENDPOINT_REGION,
        "describe_budgets",
        AccountId=account,
    )
    if payload.get("error"):
        return dumps(payload)
    rows = []
    for budget in payload.get("Budgets") or []:
        limit = budget.get("BudgetLimit") or {}
        actual = (budget.get("CalculatedSpend") or {}).get("ActualSpend") or {}
        forecast = (budget.get("CalculatedSpend") or {}).get("ForecastedSpend") or {}
        rows.append(
            {
                "name": budget.get("BudgetName"),
                "type": budget.get("BudgetType"),
                "time_unit": budget.get("TimeUnit"),
                "limit": _money(limit.get("Amount"), limit.get("Unit")),
                "actual": _money(actual.get("Amount"), actual.get("Unit")),
                "forecast": _money(forecast.get("Amount"), forecast.get("Unit")),
                "cost_filters": budget.get("CostFilters") or {},
            }
        )
    return dumps({"account": account, "note": "Budgets are account-scoped", **_truncate(rows)})


def aws_ec2_capacity() -> str:
    """List EC2 instances in us-east-2 (id, type, AZ, state)."""
    payload = _call("ec2", REGION, "describe_instances")
    if payload.get("error"):
        return dumps(payload)
    rows = []
    for reservation in payload.get("Reservations") or []:
        for inst in reservation.get("Instances") or []:
            rows.append(
                {
                    "id": inst.get("InstanceId"),
                    "type": inst.get("InstanceType"),
                    "az": (inst.get("Placement") or {}).get("AvailabilityZone"),
                    "state": (inst.get("State") or {}).get("Name"),
                    "lifecycle": inst.get("InstanceLifecycle") or "on-demand",
                }
            )
    running = sum(1 for r in rows if r.get("state") == "running")
    stopped = sum(1 for r in rows if r.get("state") == "stopped")
    return dumps({"region": REGION, "running": running, "stopped": stopped, **_truncate(rows)})


def aws_asg() -> str:
    """List Auto Scaling groups in us-east-2 (desired/min/max vs in-service)."""
    payload = _call("autoscaling", REGION, "describe_auto_scaling_groups")
    if payload.get("error"):
        return dumps(payload)
    rows = []
    at_max = 0
    for group in payload.get("AutoScalingGroups") or []:
        desired = group.get("DesiredCapacity")
        minimum = group.get("MinSize")
        maximum = group.get("MaxSize")
        in_service = sum(
            1
            for inst in group.get("Instances") or []
            if inst.get("LifecycleState") == "InService"
        )
        if maximum is not None and desired == maximum:
            at_max += 1
        rows.append(
            {
                "name": group.get("AutoScalingGroupName"),
                "desired": desired,
                "min": minimum,
                "max": maximum,
                "in_service": in_service,
                "azs": group.get("AvailabilityZones") or [],
            }
        )
    return dumps({"region": REGION, "at_max": at_max, **_truncate(rows)})


def aws_rds() -> str:
    """List RDS DB instances in us-east-2."""
    payload = _call("rds", REGION, "describe_db_instances")
    if payload.get("error"):
        return dumps(payload)
    rows = []
    for db in payload.get("DBInstances") or []:
        rows.append(
            {
                "id": db.get("DBInstanceIdentifier"),
                "engine": db.get("Engine"),
                "class": db.get("DBInstanceClass"),
                "status": db.get("DBInstanceStatus"),
                "multi_az": db.get("MultiAZ"),
                "az": db.get("AvailabilityZone"),
                "storage_gib": db.get("AllocatedStorage"),
            }
        )
    return dumps({"region": REGION, **_truncate(rows)})


def aws_ebs_summary() -> str:
    """Summarize EBS volumes in us-east-2 by type, size, and attachment."""
    payload = _call("ec2", REGION, "describe_volumes")
    if payload.get("error"):
        return dumps(payload)
    by_type: dict[str, dict[str, Any]] = {}
    unattached = 0
    for vol in payload.get("Volumes") or []:
        vtype = vol.get("VolumeType") or "unknown"
        bucket = by_type.setdefault(vtype, {"count": 0, "gib": 0})
        bucket["count"] += 1
        bucket["gib"] += int(vol.get("Size") or 0)
        if not vol.get("Attachments"):
            unattached += 1
    return dumps(
        {
            "region": REGION,
            "by_type": by_type,
            "unattached": unattached,
            "volume_count": sum(v["count"] for v in by_type.values()),
        }
    )


def aws_service_quotas() -> str:
    """Read key compute service quotas in us-east-2. Degrades per-quota on error."""
    rows = []
    for service, code, label in QUOTAS:
        payload = _call(
            "service-quotas",
            REGION,
            "get_service_quota",
            ServiceCode=service,
            QuotaCode=code,
        )
        if payload.get("error"):
            rows.append({"quota_code": code, "label": label, "unavailable": payload.get("message")})
            continue
        quota = payload.get("Quota") or {}
        rows.append(
            {
                "quota_code": code,
                "label": label,
                "value": quota.get("Value"),
                "unit": quota.get("Unit"),
                "adjustable": quota.get("Adjustable"),
                "usage_metric": (quota.get("UsageMetric") or {}).get("MetricName"),
            }
        )
    return dumps({"region": REGION, "results": rows})


def aws_rightsizing_hints() -> str:
    """CE rightsizing, then Compute Optimizer. Degrade gracefully if not enrolled."""
    start, end = _month_window()
    ce = _call(
        "ce",
        CE_ENDPOINT_REGION,
        "get_rightsizing_recommendation",
        Service="AmazonEC2",
        Configuration={"RecommendationTarget": "SAME_INSTANCE_FAMILY", "BenefitsConsidered": True},
    )
    hints: dict[str, Any] = {
        "region_filter": COST_REGION,
        "period": {"start": start, "end": end},
        "cost_explorer_rightsizing": None,
        "compute_optimizer": None,
    }
    if ce.get("error"):
        hints["cost_explorer_rightsizing"] = {"unavailable": ce.get("message")}
    else:
        summary = ce.get("Summary") or {}
        recs = []
        for rec in (ce.get("RightsizingRecommendations") or [])[:MAX_ITEMS]:
            current = rec.get("CurrentInstance") or {}
            recs.append(
                {
                    "account": rec.get("AccountId"),
                    "type": rec.get("RightsizingType"),
                    "instance": (current.get("ResourceDetails") or {})
                    .get("EC2ResourceDetails", {})
                    .get("InstanceType"),
                    "az": current.get("ResourceId"),
                }
            )
        hints["cost_explorer_rightsizing"] = {
            "total_recommendations": summary.get("TotalRecommendationCount"),
            "estimated_monthly_savings": (summary.get("TotalEstimatedMonthlySavings") or {}).get(
                "Amount"
            )
            or summary.get("EstimatedTotalMonthlySavingsAmount"),
            **_truncate(recs),
        }

    opt = _call(
        "compute-optimizer",
        REGION,
        "get_ec2_instance_recommendations",
    )
    if opt.get("error"):
        hints["compute_optimizer"] = {"unavailable": opt.get("message")}
    else:
        recs = []
        for rec in (opt.get("instanceRecommendations") or opt.get("InstanceRecommendations") or [])[
            :MAX_ITEMS
        ]:
            recs.append(
                {
                    "instance": rec.get("instanceArn") or rec.get("InstanceArn"),
                    "finding": rec.get("finding") or rec.get("Finding"),
                    "current": rec.get("currentInstanceType") or rec.get("CurrentInstanceType"),
                }
            )
        hints["compute_optimizer"] = _truncate(recs)
    return dumps(hints)


def _parse(tool_json: str) -> dict[str, Any]:
    try:
        data = json.loads(tool_json)
    except json.JSONDecodeError:
        return {"error": True, "message": "internal: non-json tool result"}
    return data if isinstance(data, dict) else {"error": True, "message": "internal: bad shape"}


def aws_executive_brief() -> str:
    """Compose a short exec summary from live whoami/cost/capacity tools. Never invent."""
    who = _parse(aws_whoami())
    cost = _parse(aws_cost_month())
    by_svc = _parse(aws_cost_by_service())
    budgets = _parse(aws_budgets())
    ec2 = _parse(aws_ec2_capacity())
    asg = _parse(aws_asg())
    rds = _parse(aws_rds())
    quotas = _parse(aws_service_quotas())
    rightsizing = _parse(aws_rightsizing_hints())

    top = None
    if not by_svc.get("error"):
        services = by_svc.get("results") or []
        if services:
            top = services[0]

    budget_line: Any
    if budgets.get("error"):
        budget_line = {"unavailable": budgets.get("message")}
    elif not (budgets.get("results") or []):
        budget_line = "none configured"
    else:
        budget_line = budgets.get("results")[:3]

    quota_line: Any
    if quotas.get("error"):
        quota_line = {"unavailable": quotas.get("message")}
    else:
        quota_line = quotas.get("results")

    rightsizing_line: Any
    if rightsizing.get("error"):
        rightsizing_line = {"unavailable": rightsizing.get("message")}
    else:
        ce_rs = rightsizing.get("cost_explorer_rightsizing")
        co = rightsizing.get("compute_optimizer")
        if isinstance(ce_rs, dict) and ce_rs.get("unavailable") and isinstance(co, dict) and co.get(
            "unavailable"
        ):
            rightsizing_line = {
                "unavailable": "CE rightsizing and Compute Optimizer both unavailable",
                "ce": ce_rs.get("unavailable"),
                "compute_optimizer": co.get("unavailable"),
            }
        else:
            rightsizing_line = {
                "ce_total_recommendations": (ce_rs or {}).get("total_recommendations")
                if isinstance(ce_rs, dict)
                else None,
                "compute_optimizer": co,
            }

    return dumps(
        {
            "account": who.get("account") if not who.get("error") else {"unavailable": who.get("message")},
            "region": REGION,
            "as_of_utc": datetime.now(timezone.utc).date().isoformat(),
            "spend_mtd": cost.get("unblended_cost")
            if not cost.get("error")
            else {"unavailable": cost.get("message")},
            "top_service": top if top else ("unavailable" if by_svc.get("error") else None),
            "budgets": budget_line,
            "capacity": {
                "ec2_running": ec2.get("running") if not ec2.get("error") else {"unavailable": ec2.get("message")},
                "ec2_stopped": ec2.get("stopped") if not ec2.get("error") else None,
                "asg_at_max": asg.get("at_max") if not asg.get("error") else {"unavailable": asg.get("message")},
                "rds_count": (rds.get("count") if not rds.get("error") else {"unavailable": rds.get("message")}),
            },
            "quotas": quota_line,
            "rightsizing": rightsizing_line,
            "errors": {
                name: payload.get("message")
                for name, payload in (
                    ("whoami", who),
                    ("cost_month", cost),
                    ("cost_by_service", by_svc),
                    ("budgets", budgets),
                    ("ec2", ec2),
                    ("asg", asg),
                    ("rds", rds),
                )
                if payload.get("error")
            },
        }
    )


TOOL_FUNCS = {
    "aws_whoami": aws_whoami,
    "aws_cost_month": aws_cost_month,
    "aws_cost_by_service": aws_cost_by_service,
    "aws_budgets": aws_budgets,
    "aws_ec2_capacity": aws_ec2_capacity,
    "aws_asg": aws_asg,
    "aws_rds": aws_rds,
    "aws_ebs_summary": aws_ebs_summary,
    "aws_service_quotas": aws_service_quotas,
    "aws_rightsizing_hints": aws_rightsizing_hints,
    "aws_executive_brief": aws_executive_brief,
}


def _self_check() -> None:
    if set(TOOL_FUNCS) != set(READ_TOOLS):
        missing = set(READ_TOOLS) - set(TOOL_FUNCS)
        extra = set(TOOL_FUNCS) - set(READ_TOOLS)
        raise SystemExit(f"tool set mismatch missing={missing} extra={extra}")
    source = open(__file__, encoding="utf-8").read()
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("AWS_SECRET_ACCESS_KEY = \"") or stripped.startswith(
            "AWS_ACCESS_KEY_ID = \""
        ):
            raise SystemExit("literal credential assignment in source")
        if " = \"AKIA" in stripped or " = \"ASIA" in stripped:
            raise SystemExit("access-key-shaped literal in source")
    if REGION != "us-east-2" and not os.environ.get("AWS_DEFAULT_REGION"):
        raise SystemExit("default region must be us-east-2")
    # No generic CLI wrapper (import or call). This file must not shell out.
    if "import sub" + "process" in source:
        raise SystemExit("generic command execution is not allowed")
    if "os.sys" + "tem(" in source:
        raise SystemExit("generic command execution is not allowed")


def build_mcp():
    from fastmcp import FastMCP
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    mcp = FastMCP(name="aws-budget")

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
            "AWS credentials are not set; tools will return an error until the Secret exists",
            file=sys.stderr,
        )
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8084"))
    mcp = build_mcp()
    mcp.run(transport="http", host=host, port=port, path="/mcp")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-check":
        _self_check()
        print("aws-budget-mcp self-check ok")
        sys.exit(0)
    main()
