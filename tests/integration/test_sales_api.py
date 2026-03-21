"""Tests de integración para Sales API (sandbox SP-API)."""

import pytest
from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestSalesApiSandbox:

    def test_get_order_metrics(self, client):
        """Sandbox puede no soportar order metrics."""
        try:
            result = client.get_order_metrics(days_back=7)
            assert isinstance(result, list)
        except RuntimeError:
            pytest.skip("Sandbox no soporta order metrics")
