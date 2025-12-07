"""Unit tests for email_flow.py functions and flow."""

from unittest.mock import MagicMock, patch

import pytest

from email_flow import example_email_send_message_flow, validate_config


class TestValidateConfig:
    """Tests for the validate_config function."""

    def test_valid_config_returns_orgname_and_carers(self, valid_email_config):
        """Test valid config returns correctly extracted values."""
        org_name, carers = validate_config(valid_email_config)

        assert org_name == "Test Organization"
        assert len(carers) == 2
        assert "John Doe" in carers

    def test_none_config_raises_valueerror(self):
        """Test None config raises appropriate error."""
        with pytest.raises(ValueError, match="email_config variable not found"):
            validate_config(None)

    def test_missing_required_keys_raises_valueerror(self):
        """Test missing required keys raise errors."""
        with pytest.raises(ValueError, match="missing required key 'carers'"):
            validate_config({"orgname": "Test"})

    def test_empty_carers_raises_valueerror(self):
        """Test empty carers dict raises error."""
        with pytest.raises(ValueError, match="non-empty object"):
            validate_config({"orgname": "Test", "carers": {}})

    def test_carer_missing_keys_raises_valueerror(self):
        """Test carer with missing keys raises error."""
        config = {"orgname": "Test", "carers": {"Bad": {"hours": 10}}}

        with pytest.raises(ValueError, match="missing required keys"):
            validate_config(config)


class TestExampleEmailSendMessageFlow:
    """Tests for the email flow using .fn() pattern."""

    @patch("email_flow.get_run_logger")
    @patch("email_flow.email_send_message")
    @patch("email_flow.Variable")
    @patch("email_flow.EmailServerCredentials")
    def test_flow_sends_emails_for_each_carer(
        self, mock_credentials, mock_variable, mock_email_send, mock_logger, valid_email_config
    ):
        """Test flow sends email for each carer in config."""
        mock_credentials.load.return_value = MagicMock()
        mock_variable.get.return_value = valid_email_config
        mock_logger.return_value = MagicMock()

        mock_task = MagicMock()
        mock_task.submit.return_value = "task_result"
        mock_email_send.with_options.return_value = mock_task

        result = example_email_send_message_flow.fn(["test@example.com"])

        assert result == "task_result"
        assert mock_email_send.with_options.call_count == 2  # Two carers

    @patch("email_flow.get_run_logger")
    @patch("email_flow.Variable")
    @patch("email_flow.EmailServerCredentials")
    def test_flow_raises_on_invalid_config(self, mock_credentials, mock_variable, mock_logger):
        """Test flow raises ValueError with invalid config."""
        mock_credentials.load.return_value = MagicMock()
        mock_variable.get.return_value = None
        mock_logger.return_value = MagicMock()

        with pytest.raises(ValueError, match="email_config variable not found"):
            example_email_send_message_flow.fn(["test@example.com"])
