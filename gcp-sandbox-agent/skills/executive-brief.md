# Skill: executive brief

One short brief an exec can read in **30 seconds**. Prefer the composed
tool `gcp_executive_brief`, which must itself call the live GCP APIs.
If that tool errors, fall back to the budget + capacity tools and compose
the same shape yourself — still no invented numbers.

## Shape

```text
Identity: <sa email>  Org: maniak.io  Region: us-east1  As of: <UTC date>
Projects: <ids the tool returned>
Billing: <account id> open=<true/false>  Budgets: <name> limit or “none configured”
Spend MTD: unavailable (<reason from the tool>) — never a guessed dollar
Capacity: <running instances>, <disk count>
Quotas: <tightest quota used/limit> or “quota API unavailable”
Risk: <one sentence, or “none from these reads”>
```

## Rules

- Four to eight lines. No essay.
- Every count comes from a tool result in this turn.
- If spend is unavailable, write `unavailable` — do not write `$0`.
- If something failed, keep the line and write `unavailable (<reason>)`.
- Never attach service-account JSON, private keys, or Vault tokens.
