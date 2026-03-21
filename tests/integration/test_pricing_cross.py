"""Tests de integración para precios cross-marketplace (sandbox SP-API).

La funcionalidad cross-marketplace usa la Listings Items API internamente.
En sandbox solo funciona con seller_id y SKUs específicos del test case.
"""

import pytest

from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestCrossMarketplacePricingSandbox:

    def test_get_prices_handles_errors_gracefully(self, client):
        """get_prices_all_marketplaces no lanza excepción — devuelve errores inline."""
        result = client.get_prices_all_marketplaces(
            "NONEXISTENT-SKU", marketplaces=["ES"],
        )
        assert isinstance(result, list)
        assert len(result) == 1
        # Puede tener precio=None o error, ambos son válidos
        assert "marketplace" in result[0]
