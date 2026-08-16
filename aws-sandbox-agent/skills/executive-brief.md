# Skill: executive brief

One short brief an exec can read in **30 seconds**. Prefer the composed
tool `aws_executive_brief`, which must itself call the live AWS APIs.
If that tool errors, fall back to the budget + capacity tools and compose
the same shape yourself — still no invented numbers.

## Shape

```text
Account: <id>  Region: us-east-2  As of: <UTC date>
Spend MTD: $<n>  Top service: <name> $<n>
Budgets: <name> actual/limit or “none configured”
Capacity: <running instances>, <ASGs at max>, <RDS count>
Quotas: <tightest quota used/limit> or “quota API unavailable”
Rightsizing: <one line> or “not enrolled / API denied”
Risk: <one sentence, or “none from these reads”>
```

## Rules

- Four to eight lines. No essay.
- Every dollar and count comes from a tool result in this turn.
- If something failed, keep the line and write `unavailable (<reason>)`.
- Never attach keys, ARNs of access keys, or Vault paths with tokens.
