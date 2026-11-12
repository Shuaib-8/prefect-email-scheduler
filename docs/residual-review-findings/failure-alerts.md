## Residual Review Findings

Source: code review of branch `failure-alerts` (run `20261112-131829-59d19597`), 2026-11-12.
Reviewers: correctness, adversarial, reliability, testing and project-standards. Both actionable findings were independently validated.

- **P1 - `email_flow.py:130` - Partial email-send failures end Completed, so the failure alert never fires.**
  The flow returns only the last submitted `email_send_message` future (`return subject`). Prefect 3 derives the flow state from the returned value only, so if an earlier send fails and the last one succeeds, the run ends Completed and `automations.py` (Failed/Crashed/TimedOut) never alerts.
  Suggested fix: return the list of all submitted futures, or `wait()` on them and raise if any failed. Add a test where the first send fails and the last succeeds.
  Not applied: it changes how the deployed flow terminates, so it needs an explicit decision.
  Tracker: not filed. GitHub issue creation was blocked by the session's permission policy, so this file is the durable record.

### Lower-confidence notes (below the actionable bar, kept for visibility)
- `automations.py` reports success without reading the automation back, even though Cloud has silently dropped a 201-created automation before (seen with `send-email-notification`). Consider a `GET /automations/{id}` check after upsert.
- Runs that never start (stuck Late) produce no alert. Consider adding `prefect.flow-run.Late` to `FAILURE_EVENTS`.
- The trigger pins the deployment UUID. Deleting and recreating the deployment silently orphans the alert until `automations.py` is re-run.
- End-to-end delivery is unproven: no real failure event has yet produced an alert email.
- The plan's KTD1/R2 still name `send-email-notification`, but the implementation uses `send-notification` with a Cloud `email` block (see the `automations.py` docstring).
