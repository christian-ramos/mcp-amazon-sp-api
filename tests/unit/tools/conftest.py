"""Fixtures compartidos para tests de MCP tools."""

import json
from unittest.mock import patch, MagicMock

import pytest

from mcp_amazon_sp_api import server


def parse(result: str) -> dict | list:
    return json.loads(result)


@pytest.fixture(autouse=True)
def mock_client(env_credentials):
    """Mockea _get_client para todos los tests de tools."""
    mock = MagicMock()
    with patch.object(server, "_get_client", return_value=mock):
        yield mock
