"""
Create or update the Prefect Cloud automation that emails an alert when a run of the
scheduled email deployment fails, crashes or times out.

Safe to re-run: the alert block and the automation are matched by name and updated in place.

Usage:
    uv run automations.py                      # alert the gmail-access-app account owner
    uv run automations.py --email me@x.com     # alert a specific address (repeatable)

Why Prefect Cloud's built-in `email` notification block rather than a Gmail-backed one:
Cloud delivers these emails itself, so the alert still arrives when the flow's own Gmail
credentials are the thing that broke (a revoked app password — the 2026-11-12 failure).

Why not Cloud's `send-email-notification` action: Cloud accepts it (201) but the
automation never persists — it cannot be read back or listed afterwards. A
`send-notification` action pointing at an `email` block persists normally.

The `email` block type is Cloud-only and has no SDK `Block` class, so the block is managed
as a raw block document (type and schema looked up by slug), and the automation is
sent as a plain JSON payload through the client's typed REST helper.
"""

import argparse
import asyncio
import logging
from typing import Any
from uuid import UUID

from prefect.client.orchestration import PrefectClient, get_client
from prefect.client.schemas.actions import BlockDocumentCreate, BlockDocumentUpdate
from prefect.events.schemas.automations import EventTrigger, Posture
from prefect.exceptions import ObjectNotFound
from prefect_email import EmailServerCredentials

DEPLOYMENT_NAME = "example-email-send-message-flow/email-deployment"
AUTOMATION_NAME = "email-deployment-failure-alert"
ALERT_BLOCK_NAME = "email-deployment-failure-alert"
ALERT_BLOCK_TYPE_SLUG = "email"
CREDENTIALS_BLOCK_NAME = "gmail-access-app"

# TimedOut is a FAILED-type state but emits its own event name, so list it explicitly.
FAILURE_EVENTS = (
    "prefect.flow-run.Failed",
    "prefect.flow-run.Crashed",
    "prefect.flow-run.TimedOut",
)

ALERT_SUBJECT = "Prefect: scheduled carer payment email did not send"
ALERT_BODY = """\
The scheduled payment email run did not complete.

Flow run: {{ flow_run.name }}
State: {{ flow_run.state.name }}
Message: {{ flow_run.state.message }}

Open the run: {{ flow_run|ui_url }}

The scheduler does not retry failed runs. After fixing the cause, re-send with:
  prefect deployment run 'example-email-send-message-flow/email-deployment'
"""

logger = logging.getLogger(__name__)


def build_automation_payload(deployment_id: UUID, alert_block_id: UUID) -> dict[str, Any]:
    """Build the Prefect Cloud automation body for the failure alert."""
    trigger = EventTrigger(
        expect=set(FAILURE_EVENTS),
        match_related={"prefect.resource.id": f"prefect.deployment.{deployment_id}"},
        posture=Posture.Reactive,
        threshold=1,
    )
    return {
        "name": AUTOMATION_NAME,
        "description": (
            f"Email an alert when a run of {DEPLOYMENT_NAME} fails, crashes or times out."
        ),
        "enabled": True,
        "trigger": trigger.model_dump(mode="json"),
        "actions": [
            {
                "type": "send-notification",
                "block_document_id": str(alert_block_id),
                "subject": ALERT_SUBJECT,
                "body": ALERT_BODY,
            }
        ],
    }


async def find_alert_block_id(client: PrefectClient) -> UUID | None:
    """Return the id of the existing alert block, or None if it has not been created yet."""
    try:
        document = await client.read_block_document_by_name(
            name=ALERT_BLOCK_NAME, block_type_slug=ALERT_BLOCK_TYPE_SLUG
        )
    except ObjectNotFound:
        return None
    return document.id


async def create_alert_block(client: PrefectClient, data: dict[str, Any]) -> UUID:
    """Create the alert block against the newest schema of the Cloud `email` block type."""
    block_type = (
        await client.request(
            "GET", "/block_types/slug/{slug}", path_params={"slug": ALERT_BLOCK_TYPE_SLUG}
        )
    ).json()
    schemas = (
        await client.request(
            "POST",
            "/block_schemas/filter",
            json={"block_schemas": {"block_type_id": {"any_": [block_type["id"]]}}},
        )
    ).json()
    latest_schema = max(schemas, key=lambda schema: schema["created"])
    document = await client.create_block_document(
        BlockDocumentCreate(
            name=ALERT_BLOCK_NAME,
            block_type_id=UUID(block_type["id"]),
            block_schema_id=UUID(latest_schema["id"]),
            data=data,
        )
    )
    return document.id


async def upsert_alert_block(client: PrefectClient, recipient_emails: list[str]) -> UUID:
    """
    Create the Cloud `email` notification block, or replace its recipients if it exists.
    Returns its id. Raises ValueError if no recipients are given.
    """
    if not recipient_emails:
        raise ValueError("At least one alert recipient email address is required.")
    data = {"emails": recipient_emails}

    existing_block_id = await find_alert_block_id(client)
    if existing_block_id is None:
        return await create_alert_block(client, data)

    await client.update_block_document(
        existing_block_id, BlockDocumentUpdate(data=data, merge_existing_data=False)
    )
    return existing_block_id


async def upsert_automation(client: PrefectClient, payload: dict[str, Any]) -> UUID:
    """Create the automation, or update the existing one with the same name. Returns its id."""
    response = await client.request(
        "POST",
        "/automations/filter",
        json={"automations": {"name": {"any_": [payload["name"]]}}},
    )
    existing_ids = [UUID(automation["id"]) for automation in response.json()]

    if not existing_ids:
        response = await client.request("POST", "/automations/", json=payload)
        return UUID(response.json()["id"])

    if len(existing_ids) > 1:
        logger.warning(
            "Found %d automations named %r; updating %s only.",
            len(existing_ids),
            payload["name"],
            existing_ids[0],
        )
    await client.request(
        "PUT", "/automations/{id}", path_params={"id": existing_ids[0]}, json=payload
    )
    return existing_ids[0]


async def resolve_recipients(override_emails: list[str] | None) -> list[str]:
    """
    Use the explicit addresses if given, else the Gmail account the flow sends from —
    so no address has to live in this public repo.
    """
    if override_emails:
        return override_emails
    credentials = await EmailServerCredentials.aload(CREDENTIALS_BLOCK_NAME)
    if not credentials.username:
        raise ValueError(
            f"Block {CREDENTIALS_BLOCK_NAME!r} has no username; pass --email explicitly."
        )
    return [credentials.username]


async def main(override_emails: list[str] | None) -> None:
    recipient_emails = await resolve_recipients(override_emails)
    async with get_client() as client:
        deployment = await client.read_deployment_by_name(DEPLOYMENT_NAME)
        alert_block_id = await upsert_alert_block(client, recipient_emails)
        automation_id = await upsert_automation(
            client, build_automation_payload(deployment.id, alert_block_id)
        )
    print(f"Automation {AUTOMATION_NAME!r} is in place ({automation_id}).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create or update the email-deployment failure-alert automation."
    )
    parser.add_argument(
        "--email",
        action="append",
        dest="emails",
        help="Alert recipient (repeatable). Defaults to the gmail-access-app username.",
    )
    asyncio.run(main(parser.parse_args().emails))
