"""Tests de integración para Invoices API (sandbox SP-API)."""

import pytest
from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestInvoicesSandbox:

    def test_get_invoices(self, client):
        """Sandbox puede no soportar invoices."""
        try:
            result = client.get_invoices()
            assert isinstance(result, list)
        except RuntimeError:
            pytest.skip("Sandbox no soporta invoices")
