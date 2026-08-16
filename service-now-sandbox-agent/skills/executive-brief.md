# Skill: executive brief

One short brief a manager can read in **30 seconds**. Compose it from
live `sn_whoami`, `sn_incident_summary`, and `sn_list_incidents`.
If a tool errors, keep the line and write `unavailable (<reason>)` —
still no invented numbers.

## Shape

```text
Instance: <host>  User: <user_name>  As of: <UTC date>
Active incidents: <n>
By state: <New n, In Progress n, …>
By priority: <P1 n, P2 n, …>
Unassigned / needs eyes: <INC list or “none in this page”>
Catalog RITMs: <n or “not requested”>
Risk: <one sentence, or “none from these reads”>
```

## Rules

- Four to eight lines. No essay.
- Every count and INC number comes from a tool result in this turn.
- If something failed, keep the line and write `unavailable (<reason>)`.
- Never attach passwords, basic-auth headers, or Vault tokens.
