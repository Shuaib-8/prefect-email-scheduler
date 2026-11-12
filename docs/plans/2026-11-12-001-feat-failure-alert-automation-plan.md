---
title: "feat: Email alert when the scheduled email deployment fails"
date: 2026-11-12
type: feat
depth: lightweight
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
---

# feat: Email alert when the scheduled email deployment fails

## Summary

Add an idempotent script, `automations.py`, that creates or updates a Prefect Cloud automation. The automation emails the project owner whenever a run of `example-email-send-message-flow/email-deployment` ends Failed, Crashed or TimedOut.

## Problem Frame

On 2026-11-12 the monthly run failed at 08:00 UTC because Gmail had revoked the app password. Nobody was alerted, so the failure was only found by chance hours later. The scheduler does not retry a failed run, and the next attempt is a month away. Prefect Cloud has no automations configured.

## Requirements

- **R1.** An email alert is sent when a run of `email-deployment` enters Failed, Crashed or TimedOut.
- **R2.** The alert is delivered by Prefect Cloud's built-in `send-email-notification` action, so it works even when the Gmail credentials (`gmail-access-app`) are broken. That failure mode is exactly what the alert has to catch.
- **R3.** The automation is defined in code, and re-running the script converges on one automation rather than creating duplicates.
- **R4.** No email address is committed to the repo, because the repo is public. This follows the same principle as `deploy.py` sourcing recipients from Cloud.

## Key Technical Decisions

- **KTD1. Use Cloud's `send-email-notification` action, not a notification block.** A block that sends through Gmail SMTP would fail in the very scenario it needs to report. Cloud's action needs no block. Its schema, taken from the Cloud OpenAPI `SendEmailNotification`, requires `emails` and `body`, with optional `subject` and `body_format`.
- **KTD2. Call the REST API directly for this action.** The Prefect 3.7 SDK has no `SendEmailNotification` action class, so `Automation`/`AutomationCore` would reject it during validation. The trigger is still built with the SDK's `EventTrigger` and serialised to JSON. The automation itself is created or updated through the authenticated Cloud client's HTTP session (`POST /automations/`, `PUT /automations/{id}`).
- **KTD3. Make the script idempotent by matching on the automation name.** Look up existing automations by a fixed name. If none exists, create one. If one exists, update it in place. If more than one exists, update the first and warn about the rest.
- **KTD4. Resolve the alert recipient at runtime.** Default to the `username` of the `gmail-access-app` block, which is the owner's own Gmail address. Allow an explicit `--email` override. Never hardcode the address.
- **KTD5. Scope the trigger to this deployment only.** Use a reactive `EventTrigger` that expects `prefect.flow-run.Failed`, `prefect.flow-run.Crashed` and `prefect.flow-run.TimedOut`, with `match_related` set to `prefect.resource.id = prefect.deployment.<deployment-id>`, and `threshold: 1`. Look up the deployment id by name when the script runs.

## Implementation Units

### U1. Automation definition and upsert script

**Goal:** Add `automations.py`. It builds the automation payload, then creates the automation or updates the existing one with the same name.
**Requirements:** R1, R2, R3, R4
**Dependencies:** none
**Files:** `automations.py` (new), `tests/test_automations.py` (new)
**Approach:** Keep payload building in a pure function, taking the deployment id and recipient list and returning the JSON body. Keep the upsert in an async function that takes a client, so tests can pass in a fake client. The `__main__` entry point resolves the deployment id and recipient, then calls the upsert. The alert body uses Prefect's Jinja templating to include the flow run name, its state and the UI link.
**Patterns to follow:** The `deploy.py` script-style entry point, and the type-annotated, docstring-heavy style of `email_flow.py`.
**Test scenarios:**
- The payload contains `send-email-notification` with the given emails, and a trigger that expects the three terminal-failure events and matches the given deployment id.
- An empty recipient list raises `ValueError`.
- Upsert with no existing automation of that name issues one POST, and no PUT.
- Upsert with one existing automation of that name issues a PUT to that id, and no POST.
- Upsert with two existing automations of that name updates the first and returns its id.
**Verification:** Tests pass. Running the script against Cloud twice leaves exactly one automation with that name, and `prefect automation ls` shows it enabled.

### U2. Document the alert

**Goal:** Record the automation in `CLAUDE.md` under Prefect Cloud Requirements and in the Known Issues history, and add a short section to `README.md`.
**Requirements:** R3
**Dependencies:** U1
**Files:** `CLAUDE.md`, `README.md`
**Test expectation:** none, documentation only.

## Scope Boundaries

### Deferred to Follow-Up Work
- Task-level retries on `email_send_message`.
- Pinning the managed-pool image to an exact Prefect version.
- Fixing the stale `.venv` script shebangs (local environment only).

## Risks

- **The Cloud action schema may drift.** The REST payload is not validated by the SDK. Mitigation: the live run in U1's Verification fails loudly on a 422 response.
- **The event name for TimedOut.** TimedOut is a FAILED-type state, and its event is `prefect.flow-run.TimedOut`. Including both Failed and TimedOut costs nothing.
