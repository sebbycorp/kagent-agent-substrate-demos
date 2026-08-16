# Skill: capacity

Help an executive understand **whether us-east-2 compute is tight** —
running instances, ASGs, RDS, EBS, and service quotas.

## Do this

1. `aws_ec2_capacity` — instance ids, types, AZs, states. Summarize
   running vs stopped. Do not list every tag unless asked.
2. `aws_asg` — desired / min / max vs in-service. Flag any ASG at max.
3. `aws_rds` — engine, class, Multi-AZ, status.
4. `aws_ebs_summary` — count and GiB by volume type; unattached volumes.
5. `aws_service_quotas` — key compute quotas (On-Demand vCPU, etc.).
   Compare **used vs value**. If a quota API is not enabled, say so.
6. `aws_rightsizing_hints` — Cost Explorer rightsizing or Compute Optimizer.
   If the account is not enrolled, **degrade gracefully** (say “not available”)
   instead of inventing idle CPU.

## Do not

- Recommend terminate / stop / scale-in unless the human asked, and then
  still **ask before any write** (this agent has no terminate tool).
- Treat a single AZ outage story as current state without tools.
- Confuse “quota remaining” with “we should buy more.”

## How to say it

“N instances running in us-east-2 (types…), M ASGs at max, RDS: …,
On-Demand standard vCPU quota used/limit. Rightsizing: … or not enrolled.”
