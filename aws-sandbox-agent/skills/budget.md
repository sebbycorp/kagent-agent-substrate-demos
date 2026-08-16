# Skill: budget

Help an executive understand **what we are spending in us-east-2** and
whether we are on track versus AWS Budgets.

## Do this

1. Call `aws_whoami` first if identity is not already known this turn.
   Confirm the account id you will attribute spend to.
2. Call `aws_cost_month` for month-to-date unblended cost, **us-east-2 filter**.
3. Call `aws_cost_by_service` for the same period. Name the top services.
4. Call `aws_budgets` and compare actual vs limit. Say “no budgets configured”
   if the list is empty — do not invent a $X limit.
5. Quote the **time window** Cost Explorer returned (start/end). Month-to-date
   is not “the invoice.”

## Do not

- Guess last month’s bill from memory or from a previous chat.
- Treat Cost Explorer forecasts as commitments.
- Print billing account credentials or the IAM access key id in full.
  Account id (12 digits) is fine.

## How to say it

Lead with one sentence: “us-east-2 month-to-date is $A (as of DATE), top
service is B at $C, budget D is E% used.” Then the table. If CE is denied,
say the IAM action that failed (`ce:GetCostAndUsage`) instead of fabricating $0.
