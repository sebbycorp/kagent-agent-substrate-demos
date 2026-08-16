# Skills index — `servicenow`

All agent skills for this demo live in this folder. They are **not**
mounted into the gVisor actor.

kagent **0.10.0-rc2** `SandboxAgentSpec` CEL-rejects `spec.skills`
(*"spec.skills is not supported for sandbox agents"*). The live Viper
agents (`fortigate`, `hello-substrate`, `aws-budget`) put instructions
in `declarative.systemMessage`. This demo does the same: ConfigMap
`servicenow-skills` (`k8s/skills-configmap.yaml`) holds these files,
and `declarative.promptTemplate` includes them into `systemMessage`.
Repo paths such as `service-now-sandbox-agent/skills/` are not visible
inside the actor. Keep this folder in sync with that ConfigMap. Do not
invent extra skills in chat or in a second repo.

| Skill | File | When to use |
|-------|------|-------------|
| Tickets | [tickets.md](tickets.md) | What is open, look up an INC, search |
| Organize | [organize.md](organize.md) | Group by state/priority/assignee; optional writes |
| Executive brief | [executive-brief.md](executive-brief.md) | One short answer a manager can read in 30 seconds |

## Standing rules (every skill)

1. Instance is the ServiceNow **personal developer instance** whose
   host name is `https://dev203166.service-now.com`. Do not invent
   another instance.
2. Prefer **read-only** tools. Ask before any write (`sn_add_work_note`,
   `sn_assign_incident`).
3. **Never invent** ticket numbers, states, priorities, or assignees.
   If a tool fails or returns empty, say so.
4. **Never print** passwords, basic-auth headers, or Vault tokens.
   Host name and user_name are fine.
5. No generic shell. No Table API calls outside the named tools.
6. Compact answers. Managers want counts and a short list, not a dump.

## Tool map

| Skill | Tools |
|-------|-------|
| Tickets | `sn_whoami`, `sn_list_incidents`, `sn_get_incident`, `sn_search_incidents` |
| Organize | `sn_incident_summary`, `sn_list_requested_items`, `sn_add_work_note`, `sn_assign_incident` |
| Executive brief | compose from `sn_whoami` + `sn_incident_summary` + `sn_list_incidents` (still must call tools) |
