"""Tests de integración para Fulfillment Inbound API (sandbox SP-API).

El sandbox de FulfillmentInbound v0 requiere parámetros exactos.
"""

import pytest

from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestFulfillmentInboundSandbox:

    def test_list_inbound_shipments(self, client):
        """list_inbound_shipments — sandbox puede no tener datos."""
        try:
            result = client.list_inbound_shipments()
            assert isinstance(result, list)
        except RuntimeError:
            pytest.skip("Sandbox no soporta inbound shipments con estos parámetros")

    def test_get_inbound_guidance(self, client):
        """get_inbound_guidance — sandbox puede no soportar."""
        try:
            result = client.get_inbound_guidance(["B00V5DG6IQ"])
            assert isinstance(result, list)
        except RuntimeError:
            pytest.skip("Sandbox no soporta inbound guidance con estos parámetros")
