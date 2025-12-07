"""
Pytest configuration and fixtures for Prefect email scheduler tests.

Provides isolated testing environment for Prefect flows and tasks.
"""

import os

import pytest

# Set environment variable to use an ephemeral SQLite database for testing
# This is an alternative approach when prefect_test_harness has import issues
os.environ.setdefault("PREFECT_API_DATABASE_CONNECTION_URL", "sqlite+aiosqlite:///test.db")
os.environ.setdefault("PREFECT_HOME", "/tmp/prefect-test")


@pytest.fixture(autouse=True, scope="session")
def prefect_test_fixture():
    """
    Session-scoped fixture that provides isolated Prefect testing environment.

    Using prefect_test_harness when available, otherwise falls back to
    environment variable-based isolation.
    """
    try:
        from prefect.testing.utilities import prefect_test_harness

        with prefect_test_harness():
            yield
    except (ImportError, NameError):
        # Fallback: environment variables already set above provide isolation
        yield


@pytest.fixture
def valid_email_config():
    """Provides a valid email configuration dictionary for testing."""
    return {
        "orgname": "Test Organization",
        "carers": {
            "John Doe": {
                "hours": 40,
                "rate": "£12.50",
                "sig": "Jane Manager",
                "reference": "REF001",
            },
            "Alice Smith": {
                "hours": 30,
                "rate": "£11.95",
                "sig": "Jane Manager",
                "reference": "REF002",
            },
        },
    }


@pytest.fixture
def single_carer_config():
    """Provides a minimal valid config with single carer."""
    return {
        "orgname": "Single Org",
        "carers": {
            "Test Carer": {
                "hours": 20,
                "rate": "£10.00",
                "sig": "Test Sig",
                "reference": "TEST123",
            },
        },
    }
