"""Tests de integración para Messaging API (sandbox SP-API)."""

import pytest
from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestMessagingSandbox:

    def test_get_messaging_actions(self, client):
        """Sandbox puede no soportar messaging con order IDs genéricos."""
        try:
            result = client.get_messaging_actions("111-222-333")
            assert isinstance(result, dict)
        except RuntimeError:
            pytest.skip("Sandbox no soporta messaging con este order ID")
