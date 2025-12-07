"""Unit tests for email_template.py functions."""

import datetime
from unittest.mock import patch

from email_template import _get_date_range, email_body, email_subject


class TestEmailTemplate:
    """Tests for email template generation functions."""

    @patch("email_template.datetime")
    def test_get_date_range_returns_correct_months(self, mock_datetime):
        """Test date range calculation returns previous and current month."""
        mock_datetime.date.today.return_value = datetime.date(2024, 6, 15)
        mock_datetime.timedelta = datetime.timedelta

        prev_month, prev_year, now_month, now_year = _get_date_range()

        assert prev_month == "May"
        assert prev_year == "2024"
        assert now_month == "June"
        assert now_year == "2024"

    def test_email_subject_contains_name(self):
        """Test email subject contains the provided name."""
        result = email_subject("John Doe")

        assert "John Doe" in result

    def test_email_body_contains_required_elements(self):
        """Test email body contains all required information."""
        result = email_body(
            name="John Doe",
            hours=40,
            org_name="Test Org",
            rate="£12.50",
            sig="Jane Manager",
            reference="REF001",
        )

        assert "Test Org" in result
        assert "John Doe" in result
        assert "40 hours @ £12.50" in result
        assert "Jane Manager" in result
        assert "REF001" in result
