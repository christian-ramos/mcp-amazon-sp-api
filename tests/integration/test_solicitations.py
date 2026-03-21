"""Tests de integración para Solicitations API (sandbox SP-API)."""

import pytest
from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestSolicitationsSandbox:

    def test_get_solicitation_actions(self, client):
        """Sandbox puede no soportar solicitations con order IDs genéricos."""
        try:
            result = client.get_solicitation_actions("111-222-333")
            assert isinstance(result, dict)
        except RuntimeError:
            pytest.skip("Sandbox no soporta solicitations con este order ID")
