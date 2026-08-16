# Skill: capacity

Help an executive understand **whether us-east1 compute is tight** —
running instances, disks, and Compute Engine quotas.

## Do this

1. `gcp_projects` — list accessible projects. Expected names:
   viper-kagent, maniak-io, qr-maniak-io. Do not invent others.
2. `gcp_compute_capacity` — instance names, machine types, zones,
   status; disk count / GiB by type; unattached disks. Summarize
   running vs stopped. Do not list every disk unless asked.
3. `gcp_quotas` — key compute quotas in **us-east1** (instances,
   CPUs, disk GB, in-use addresses). Compare **usage vs limit**.
   Flag anything at or above 80%. If the quota API is denied, say so.

## Do not

- Recommend delete / stop / scale-in unless the human asked, and then
  still **ask before any write** (this agent has no mutate tools).
- Treat a single-zone outage story as current state without tools.
- Confuse “quota remaining” with “we should buy more.”
- Answer for regions other than us-east1.

## How to say it

“N instances running in us-east1 (types…), M disks (unattached: …),
tightest quota used/limit. Projects visible: ….”
