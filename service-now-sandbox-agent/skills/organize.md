# Skill: organize

Help a manager **group and tidy** the existing queue — by state,
priority, and assignee. Writes are optional and must be confirmed.

## Do this

1. Call `sn_incident_summary` for counts by state and by priority.
   Those counts are the source of truth.
2. Call `sn_list_incidents` if you need the actual INC rows behind
   a bucket (unassigned, P1, on hold).
3. Call `sn_list_requested_items` when they ask about catalog / RITM
   work, not just incidents.
4. Suggest an organize plan in words first: “assign INC0010001 to
   alice; add a work note on INC0010002.”
5. Only after the human says yes, call `sn_assign_incident` or
   `sn_add_work_note`. One write per confirmed item.

## Do not

- Assign or comment without asking.
- Close, cancel, or resolve an incident (no such tool).
- Re-open a closed ticket.
- Invent an assignee who did not appear in a tool result or in the
  human’s instruction.

## How to say it

“Active queue: N New, M In Progress, K On Hold. Unassigned: … .
Proposed next step: … (say yes to write).”
