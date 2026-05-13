# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Verify environment
uv run main.py

# Run tests (installs test deps automatically)
uv sync --group test
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_email_flow.py -v

# Lint and format
uvx ruff format .
uvx ruff check --select I --fix && uvx ruff format .
```

## Architecture

This project sends scheduled HTML payment confirmation emails to carers using Prefect Cloud for orchestration.

**Flow (`email_flow.py`):** The main entry point is `example_email_send_message_flow(email_addresses: List[str])`. It:
1. Loads a Gmail credential block (`gmail-access-app`) from Prefect Cloud
2. Loads a JSON config variable (`email_config`) from Prefect Cloud
3. Validates the config with `validate_config()` — checks for required keys at both the top level (`orgname`, `carers`) and per-carer level (`hours`, `rate`, `sig`, `reference`)
4. For each email address × each carer, submits an `email_send_message` task using templates from `email_template.py`

**Templates (`email_template.py`):** `_get_date_range()` computes prev/current month dynamically at runtime. `email_subject()` and `email_body()` use this to produce dated HTML emails without hardcoded dates.

**Deployment (`deploy.py`):** Deploys from GitHub source to a Prefect managed work pool (`managed-prefect-workpool`). Run this script to push a new deployment to Prefect Cloud. At deploy time it reads `email_config` from Prefect Cloud and forwards `email_config["email_addresses"]` as the deployment's default `email_addresses` parameter — so recipient addresses are never committed to this public repo.

**`starter.py`** is a reference-only example — not part of the deployed flow.

## Prefect Cloud Requirements

The flow requires these resources to exist in Prefect Cloud before running:
- **Credentials block:** `gmail-access-app` (Gmail `EmailServerCredentials`)
- **Variable:** `email_config` (JSON with shape below)
- **Work pool:** `managed-prefect-workpool`

```json
{
  "orgname": "<org_name>",
  "email_addresses": ["<recipient@example.com>"],
  "carers": {
    "<carer_name>": {
      "hours": 40,
      "rate": "£10.00",
      "sig": "<signer_name>",
      "reference": "<ref_number>"
    }
  }
}
```

## Known Issues and Backlog

**Resolved — managed-pool image collision (2026-05-13):**
The default managed work pool image (`prefecthq/prefect-client:3-latest`, a slim variant) plus an unpinned `prefect-email` install caused a namespace collision when `prefect-email` transitively pulled in full `prefect`. The worker died at startup before Prefect's log handler initialised, so flow runs surfaced as Crashed with no logs and only after the 24h+ heartbeat sweep. Fix lives in `deploy.py` `job_variables`: pin to the full `prefecthq/prefect:3-python3.11` image and pin `prefect-email>=0.4.2,<0.5`. Do **not** revert these without re-testing on the managed pool.

**Resolved — silent SMTP hangs:**
`email_send_message` task in `email_flow.py` is configured with `timeout_seconds=150` to bound any single email send. Without this, a hung SMTP connection could silently swallow a flow run.

**Backlog — recipient list dual source-of-truth:**
Recipients currently live in **two** Cloud-side places: the `email_config.email_addresses` variable (read by `deploy.py` at deploy time) and the deployment record's `parameters` field (set by `deploy.py`). Editing the variable alone does **not** propagate to scheduled runs — `python deploy.py` must be re-run for the new list to reach the deployment record. The cleaner alternative (deferred) is to make `email_addresses` optional in `example_email_send_message_flow`, and fall back to `email_config["email_addresses"]` inside the flow itself. That would collapse the dependency to a single Cloud variable that flows through to every run with zero redeploy. Defer unless recipient lists change often.

**Operational quirk — deployment parameter overwrites:**
Every successful `python deploy.py` run overwrites the deployment record's `parameters` field on Prefect Cloud. UI edits to that field do not survive a redeploy. To change recipients durably, edit `email_config` in the Variables UI then re-run `python deploy.py`.

**Operational quirk — Cloud UI Parameters editor needs explicit Save:**
Editing a deployment's `Parameters` field inline in the Prefect Cloud UI does **not** auto-commit — an explicit Save action is required, otherwise the change is discarded on navigation and the deployment record keeps its previous value. To verify a UI edit landed, run `prefect deployment inspect example-email-send-message-flow/email-deployment` and check that the `updated` timestamp has advanced past the last `python deploy.py` run.

## Testing Notes

Tests use `prefect_test_fixture` (from `tests/conftest.py`) to isolate Prefect state. Email credentials and `email_send_message` tasks are mocked — tests do not send real emails. Pytest is configured in `pyproject.toml` with `-v --tb=short` defaults.
