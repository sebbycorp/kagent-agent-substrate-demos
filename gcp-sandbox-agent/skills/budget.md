# Skill: budget

Help an executive understand **billing posture in us-east1** (org
maniak.io) and whether configured Cloud Billing budgets exist.

## Do this

1. Call `gcp_whoami` first if identity is not already known this turn.
   Confirm the service-account email and billing account id you will
   attribute the answer to.
2. Call `gcp_cost_month` for billing-account get + linked projects +
   the calendar month window. Quote the **time window**.
3. Call `gcp_budgets` and report configured limits (specified amount
   or last-period-amount *limit*). Say “no budgets configured” if the
   list is empty — do not invent a $X limit.
4. Call `gcp_cost_by_service`. If spend-by-service is unavailable,
   say so. Do **not** treat Cloud Catalog SKU prices as invoices.

## Do not

- Guess last month’s bill from memory or from a previous chat.
- Invent month-to-date spend. Cloud Billing Accounts / Budgets /
  Catalog do not return MTD dollars. If the tool says unavailable,
  keep that word.
- Print the service-account JSON, `private_key`, or Vault tokens.
  Billing account id (`011C38-867461-BE95B1`) and project ids are fine.

## How to say it

Lead with one sentence: “Billing account NAME is open; N projects
linked; M budgets configured (limits …). Month-to-date spend is
unavailable from Cloud Billing APIs.” Then the table. If an API is
denied, name the API (`billing.accounts.get`, `billing.budgets.list`)
instead of fabricating $0.
