# Skills index — `gcp-budget`

All agent skills for this demo live in this folder. They are **not**
mounted into the gVisor actor.

kagent **0.10.0-rc2** `SandboxAgentSpec` CEL-rejects `spec.skills`
(*"spec.skills is not supported for sandbox agents"*). The live Viper
agents (`fortigate`, `hello-substrate`, `aws-budget`, `servicenow`) put
instructions in `declarative.systemMessage`. This demo does the same:
ConfigMap `gcp-budget-skills` (`k8s/skills-configmap.yaml`) holds these
files, and `declarative.promptTemplate` includes them into
`systemMessage`. Repo paths such as `gcp-sandbox-agent/skills/` are not
visible inside the actor. Keep this folder in sync with that ConfigMap.
Do not invent extra skills in chat or in a second repo.

| Skill | File | When to use |
|-------|------|-------------|
| Budget | [budget.md](budget.md) | Billing account, Cloud Billing budgets vs configured limits |
| Capacity | [capacity.md](capacity.md) | GCE instances / disks / quotas in **us-east1** |
| Executive brief | [executive-brief.md](executive-brief.md) | One short answer an exec can read in 30 seconds |

## Standing rules (every skill)

1. Region is **us-east1**. Org is **maniak.io**. Do not report another
   region as “ours.”
2. Prefer **read-only** tools. There are almost no writes; ask before any write.
3. **Never invent** spend, instance counts, quota numbers, or budget status.
   If a tool fails or returns empty, say so. Cloud Billing does **not**
   expose month-to-date spend — say unavailable, do not estimate `$0`.
4. **Never print** service-account JSON, private keys, or Vault tokens.
   Project ids and the billing account id are fine.
5. Projects that exist (names only): **viper-kagent**, **maniak-io**,
   **qr-maniak-io**. Do not invent other project ids.
6. No generic Google Cloud CLI. No project-delete, no IAM-create.

## Tool map

| Skill | Tools |
|-------|-------|
| Budget | `gcp_whoami`, `gcp_cost_month`, `gcp_budgets`, `gcp_cost_by_service` |
| Capacity | `gcp_compute_capacity`, `gcp_quotas`, `gcp_projects` |
| Executive brief | `gcp_executive_brief` (composes the above; still must call tools) |
