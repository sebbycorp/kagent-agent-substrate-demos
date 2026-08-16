# Skill: tickets

Help a manager **see what IT tickets already exist** on the ServiceNow
personal developer instance. Read-only.

## Do this

1. Call `sn_whoami` first if identity is not already known this turn.
   Confirm the instance host and the user you are acting as.
2. Call `sn_list_incidents` for open/active incidents. Lead with
   number, short description, state, priority, assignee.
3. If the human names an INC (or pastes a sys_id), call `sn_get_incident`.
4. If they describe a problem without a number, call `sn_search_incidents`
   with their words. Do not invent a matching INC.
5. Keep the list compact. Do not dump every field unless asked.

## Do not

- Guess ticket state from a previous chat.
- Treat a closed incident as open because it “sounds current.”
- Print the ServiceNow password or a basic-auth header.
- Open a new incident. This agent does not create tickets.

## How to say it

Lead with one sentence: “N active incidents (as of tool time); P1/P2
count is M; oldest unassigned is INC….” Then a short table. If the
Table API is denied, say the HTTP status instead of fabricating a queue.
