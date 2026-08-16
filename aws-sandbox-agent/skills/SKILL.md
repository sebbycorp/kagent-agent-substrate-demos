# Skills index — `aws-budget`

All agent skills for this demo live in this folder. They are **not**
mounted into the gVisor actor.

kagent **0.10.0-rc2** `SandboxAgentSpec` CEL-rejects `spec.skills`
(*"spec.skills is not supported for sandbox agents"*). The live Viper
agents (`fortigate`, `hello-substrate`) put instructions in
`declarative.systemMessage`. This demo does the same: ConfigMap
`aws-budget-skills` (`k8s/skills-configmap.yaml`) holds these files,
and `declarative.promptTemplate` includes them into `systemMessage`.
Repo paths such as `aws-sandbox-agent/skills/` are not visible inside
the actor. Keep this folder in sync with that ConfigMap. Do not invent
extra skills in chat or in a second repo.

| Skill | File | When to use |
|-------|------|-------------|
| Budget | [budget.md](budget.md) | Month-to-date spend, by-service breakdown, AWS Budgets vs actuals |
| Capacity | [capacity.md](capacity.md) | EC2 / ASG / RDS / EBS / quotas in **us-east-2** |
| Executive brief | [executive-brief.md](executive-brief.md) | One short answer an exec can read in 30 seconds |

## Standing rules (every skill)

1. Region is **us-east-2**. Do not report another region as “ours.”
2. Prefer **read-only** tools. There are almost no writes; ask before any write.
3. **Never invent** spend, instance counts, quota numbers, or budget status.
   If a tool fails or returns empty, say so.
4. **Never print** access keys, secret keys, session tokens, or Vault tokens.
5. Cost Explorer / Budgets are global APIs (us-east-1 endpoint) but results
   must be **filtered** to us-east-2 where the API allows it.
6. No generic AWS CLI. No IAM create, no terminate, no budget-delete.

## Tool map

| Skill | Tools |
|-------|-------|
| Budget | `aws_whoami`, `aws_cost_month`, `aws_cost_by_service`, `aws_budgets` |
| Capacity | `aws_ec2_capacity`, `aws_asg`, `aws_rds`, `aws_ebs_summary`, `aws_service_quotas`, `aws_rightsizing_hints` |
| Executive brief | `aws_executive_brief` (composes the above; still must call tools) |
