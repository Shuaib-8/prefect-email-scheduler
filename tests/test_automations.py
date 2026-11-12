"""
Tests for the failure-alert automation script.

The Prefect Cloud client is faked — these tests never talk to Prefect Cloud.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import httpx
import pytest
from prefect.exceptions import ObjectNotFound, PrefectHTTPStatusError

from automations import (
    ALERT_BLOCK_NAME,
    AUTOMATION_NAME,
    FAILURE_EVENTS,
    build_automation_payload,
    resolve_recipients,
    upsert_alert_block,
    upsert_automation,
)


def _response(json_body: Any) -> MagicMock:
    response = MagicMock()
    response.json.return_value = json_body
    return response


def _http_error(status_code: int) -> PrefectHTTPStatusError:
    request = httpx.Request("GET", "https://api.example.test/")
    response = httpx.Response(status_code, request=request)
    return PrefectHTTPStatusError("error", request=request, response=response)


def _fake_block_client(
    existing_block_id: UUID | None,
    created_block_id: UUID | None = None,
    lookup_error: Exception | None = None,
) -> MagicMock:
    """
    Fake client for the alert-block upsert. With no existing block, the name lookup raises
    `lookup_error` (default ObjectNotFound, i.e. a 404).
    """
    block_type_id = uuid4()

    async def read_block_document_by_name(name: str, block_type_slug: str) -> MagicMock:
        if existing_block_id is None:
            raise lookup_error or ObjectNotFound(http_exc=_http_error(404))
        return MagicMock(id=existing_block_id)

    async def request(method: str, path: str, **kwargs: Any) -> MagicMock:
        if path == "/block_types/slug/{slug}":
            return _response({"id": str(block_type_id)})
        if path == "/block_schemas/filter":
            return _response(
                [
                    {
                        "id": "00000000-0000-0000-0000-000000000001",
                        "created": "2025-01-01T00:00:00Z",
                    },
                    {
                        "id": "00000000-0000-0000-0000-000000000002",
                        "created": "2025-08-16T00:00:00Z",
                    },
                ]
            )
        return _response(None)

    client = MagicMock()
    client.read_block_document_by_name = AsyncMock(side_effect=read_block_document_by_name)
    client.request = AsyncMock(side_effect=request)
    client.create_block_document = AsyncMock(return_value=MagicMock(id=created_block_id))
    client.update_block_document = AsyncMock(return_value=None)
    return client


def _fake_automation_client(existing_ids: list[UUID], created_id: UUID | None = None) -> MagicMock:
    """Fake client whose filter call returns the given automation ids."""

    async def request(method: str, path: str, **kwargs: Any) -> MagicMock:
        if path == "/automations/filter":
            return _response([{"id": str(existing_id)} for existing_id in existing_ids])
        if method == "POST" and path == "/automations/":
            return _response({"id": str(created_id)})
        return _response(None)

    client = MagicMock()
    client.request = AsyncMock(side_effect=request)
    return client


def _calls(client: MagicMock, method: str, path: str) -> list[Any]:
    return [
        call
        for call in client.request.await_args_list
        if call.args[0] == method and call.args[1] == path
    ]


class TestBuildAutomationPayload:
    def test_notification_action_uses_the_alert_block(self) -> None:
        alert_block_id = uuid4()

        payload = build_automation_payload(uuid4(), alert_block_id)

        (action,) = payload["actions"]
        assert action["type"] == "send-notification"
        assert action["block_document_id"] == str(alert_block_id)
        assert action["subject"]
        assert "{{ flow_run.name }}" in action["body"]
        assert "{{ flow_run|ui_url }}" in action["body"]

    def test_trigger_fires_on_terminal_failures_of_this_deployment_only(self) -> None:
        deployment_id = uuid4()

        trigger = build_automation_payload(deployment_id, uuid4())["trigger"]

        assert trigger["type"] == "event"
        assert trigger["posture"] == "Reactive"
        assert trigger["threshold"] == 1
        assert set(trigger["expect"]) == set(FAILURE_EVENTS)
        assert set(FAILURE_EVENTS) == {
            "prefect.flow-run.Failed",
            "prefect.flow-run.Crashed",
            "prefect.flow-run.TimedOut",
        }
        assert trigger["match_related"] == {
            "prefect.resource.id": f"prefect.deployment.{deployment_id}"
        }

    def test_payload_is_named_and_enabled(self) -> None:
        payload = build_automation_payload(uuid4(), uuid4())

        assert payload["name"] == AUTOMATION_NAME
        assert payload["enabled"] is True


class TestUpsertAlertBlock:
    @pytest.mark.asyncio
    async def test_creates_block_with_latest_schema_when_missing(self) -> None:
        created_block_id = uuid4()
        client = _fake_block_client(existing_block_id=None, created_block_id=created_block_id)

        result = await upsert_alert_block(client, ["owner@example.com"])

        assert result == created_block_id
        (create_call,) = client.create_block_document.await_args_list
        block_document = create_call.args[0]
        assert block_document.name == ALERT_BLOCK_NAME
        assert block_document.block_schema_id == UUID("00000000-0000-0000-0000-000000000002")
        assert block_document.data == {"emails": ["owner@example.com"]}
        client.update_block_document.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_replaces_recipients_when_block_exists(self) -> None:
        existing_block_id = uuid4()
        client = _fake_block_client(existing_block_id=existing_block_id)

        result = await upsert_alert_block(client, ["new@example.com"])

        assert result == existing_block_id
        (update_call,) = client.update_block_document.await_args_list
        block_id, block_document = update_call.args
        assert block_id == existing_block_id
        assert block_document.data == {"emails": ["new@example.com"]}
        assert block_document.merge_existing_data is False
        client.create_block_document.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_404_lookup_errors_propagate(self) -> None:
        client = _fake_block_client(existing_block_id=None, lookup_error=_http_error(500))

        with pytest.raises(PrefectHTTPStatusError):
            await upsert_alert_block(client, ["owner@example.com"])

        client.create_block_document.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_empty_recipient_list_is_rejected(self) -> None:
        client = _fake_block_client(existing_block_id=None)

        with pytest.raises(ValueError, match="recipient"):
            await upsert_alert_block(client, [])

        client.read_block_document_by_name.assert_not_awaited()


class TestUpsertAutomation:
    @pytest.mark.asyncio
    async def test_creates_when_no_automation_with_that_name_exists(self) -> None:
        created_id = uuid4()
        client = _fake_automation_client(existing_ids=[], created_id=created_id)
        payload = build_automation_payload(uuid4(), uuid4())

        result = await upsert_automation(client, payload)

        assert result == created_id
        (create_call,) = _calls(client, "POST", "/automations/")
        assert create_call.kwargs["json"] == payload
        assert _calls(client, "PUT", "/automations/{id}") == []

    @pytest.mark.asyncio
    async def test_updates_in_place_when_one_exists(self) -> None:
        existing_id = uuid4()
        client = _fake_automation_client(existing_ids=[existing_id])
        payload = build_automation_payload(uuid4(), uuid4())

        result = await upsert_automation(client, payload)

        assert result == existing_id
        (update_call,) = _calls(client, "PUT", "/automations/{id}")
        assert update_call.kwargs["path_params"] == {"id": existing_id}
        assert update_call.kwargs["json"] == payload
        assert _calls(client, "POST", "/automations/") == []

    @pytest.mark.asyncio
    async def test_updates_first_when_duplicates_exist(self) -> None:
        first_id, second_id = uuid4(), uuid4()
        client = _fake_automation_client(existing_ids=[first_id, second_id])
        payload = build_automation_payload(uuid4(), uuid4())

        result = await upsert_automation(client, payload)

        assert result == first_id
        (update_call,) = _calls(client, "PUT", "/automations/{id}")
        assert update_call.kwargs["path_params"] == {"id": first_id}

    @pytest.mark.asyncio
    async def test_lookup_filters_by_automation_name(self) -> None:
        client = _fake_automation_client(existing_ids=[], created_id=uuid4())
        payload = build_automation_payload(uuid4(), uuid4())

        await upsert_automation(client, payload)

        (filter_call,) = _calls(client, "POST", "/automations/filter")
        assert filter_call.kwargs["json"]["automations"]["name"] == {"any_": [AUTOMATION_NAME]}


class TestResolveRecipients:
    @pytest.mark.asyncio
    async def test_explicit_addresses_win_without_loading_credentials(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        load_credentials = AsyncMock()
        monkeypatch.setattr("automations.EmailServerCredentials.aload", load_credentials)

        result = await resolve_recipients(["a@example.com", "b@example.com"])

        assert result == ["a@example.com", "b@example.com"]
        load_credentials.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_defaults_to_the_gmail_block_username(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        load_credentials = AsyncMock(return_value=MagicMock(username="owner@example.com"))
        monkeypatch.setattr("automations.EmailServerCredentials.aload", load_credentials)

        result = await resolve_recipients(None)

        assert result == ["owner@example.com"]
        load_credentials.assert_awaited_once_with("gmail-access-app")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("username", [None, ""])
    async def test_missing_block_username_asks_for_explicit_email(
        self, monkeypatch: pytest.MonkeyPatch, username: str | None
    ) -> None:
        load_credentials = AsyncMock(return_value=MagicMock(username=username))
        monkeypatch.setattr("automations.EmailServerCredentials.aload", load_credentials)

        with pytest.raises(ValueError, match="--email"):
            await resolve_recipients(None)
