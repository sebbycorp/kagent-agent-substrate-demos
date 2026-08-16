# UI runbook

Clicks only. Commands live in [cli-runbook.md](cli-runbook.md).
Story + why: [../JOURNEY.md](../JOURNEY.md).

## kagent UI (Viper)

1. Publish Docker NodePort **30500** on the k3s container (already done on Viper).
2. Open [http://172.16.10.135:30500/](http://172.16.10.135:30500/).
3. You should see the kagent Agents list. `hello-substrate`, `fortigate`,
   `aws-budget`, and `servicenow` are existing lab agents — leave them alone.
4. After apply, pick **kagent/gcp-budget**.
5. If the agent is grey / not Ready, wait. First **golden snapshot** is
   often 60–90 seconds. Refresh. Ready means `ActorTemplate` exists and
   `status.goldenSnapshot` is set.
6. Ask:

   > What's our us-east1 spend this month and are we over capacity?

7. You should see tool calls (`gcp_whoami`, `gcp_cost_month`,
   `gcp_compute_capacity`, or `gcp_executive_brief`) and a short
   exec-style answer. If the model invents a dollar amount with no
   tool call, say “use the tools; do not estimate spend.”
8. Do not paste the service-account JSON into the chat box.

## GCP console (SA for the agent)

1. Open [https://console.cloud.google.com/](https://console.cloud.google.com/).
2. Org **maniak.io**. Projects that exist (names only):
   **viper-kagent**, **maniak-io**, **qr-maniak-io**.
3. Billing → account **011C38-867461-BE95B1** (id only in docs).
4. IAM → create service account `gcp-budget-agent` → attach the
   read-mostly permissions in [security.md](security.md).
5. Keys → **Add key** → JSON. Download once. Keep the file
   **outside this repo**.
6. APIs: enable Cloud Billing, Cloud Billing Budget, Compute Engine,
   Cloud Resource Manager on the projects the SA will read.
7. Region focus is **us-east1**. Do not screenshot the JSON.

## Vault UI (optional vs CLI)

1. Open [http://172.16.10.135:30200/](http://172.16.10.135:30200/).
2. Unseal if needed ([k8s-viper vault-eso-setup](https://github.com/sebbycorp/k8s-viper/blob/main/docs/vault-eso-setup.md)).
3. KV → `secret/platform/gcp-budget`.
4. Keys (names only in docs): `credentials_json`, `billing_account`,
   `project`, `region`.
5. Paste values locally. Never screenshot `credentials_json`.

## What to record on video

1. **CLI**: prereqs, Vault `kv put` with the JSON redacted,
   `docker build` + `ctr import`, host `kubectl kustomize` piped into
   `docker exec -i k3s-viper kubectl apply -f -`,
   `get sandboxagent` until Ready (`gs://ate-snapshots/kagent/gcp-budget`).
2. **UI**: kagent Agents list → `gcp-budget` Ready → the
   spend/capacity question → tool calls → answer.
3. **Do not** record Vault tokens or the service-account JSON.
