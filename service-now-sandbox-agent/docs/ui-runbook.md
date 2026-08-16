# UI runbook

Clicks only. Commands live in [cli-runbook.md](cli-runbook.md).
Story + why: [../JOURNEY.md](../JOURNEY.md).

## kagent UI (Viper)

1. Publish Docker NodePort **30500** on the k3s container (already done on Viper).
2. Open [http://172.16.10.135:30500/](http://172.16.10.135:30500/).
3. You should see the kagent Agents list. `hello-substrate`, `fortigate`,
   and `aws-budget` are existing lab agents — leave them alone.
4. After apply, pick **kagent/servicenow**.
5. If the agent is grey / not Ready, wait. First **golden snapshot** is
   often 60–90 seconds. Refresh. Ready means `ActorTemplate` exists and
   `status.goldenSnapshot` is set.
6. Ask:

   > What IT tickets are open, and how should we organize them?

7. You should see tool calls (`sn_whoami`, `sn_incident_summary`,
   `sn_list_incidents`, …) and a short manager-style answer. If you see
   invented INC numbers with no tool call, the model ignored the system
   message — say “use the tools.”
8. Do not paste the ServiceNow password into the chat box.

## ServiceNow (PDI)

1. Open [https://dev203166.service-now.com](https://dev203166.service-now.com).
2. Sign in with the same user you will put in Vault (not committed).
3. Filter navigator → **Incidents** → confirm there are rows the
   integration user can read.
4. Optional: **Service Catalog** → requested items, if you will ask
   the agent about RITMs.
5. Do not screenshot the password field.

## Vault UI (optional vs CLI)

1. Open [http://172.16.10.135:30200/](http://172.16.10.135:30200/).
2. Unseal if needed ([k8s-viper vault-eso-setup](https://github.com/sebbycorp/k8s-viper/blob/main/docs/vault-eso-setup.md)).
3. KV → `secret/platform/servicenow`.
4. Keys (names only in docs): `host`, `username`, `password`.
5. Host value: `https://dev203166.service-now.com`.
6. Paste username/password locally. Never screenshot the password.

## What to record on video

1. **CLI**: prereqs, Vault `kv put` with the password redacted,
   `docker build` + `ctr import`, host `kubectl kustomize` piped into
   `docker exec -i k3s-viper kubectl apply -f -`,
   `get sandboxagent` until Ready (`gs://ate-snapshots/kagent/servicenow`).
2. **UI**: kagent Agents list → `servicenow` Ready → the open-tickets
   question → tool calls → answer.
3. **Do not** record Vault tokens or the ServiceNow password.
