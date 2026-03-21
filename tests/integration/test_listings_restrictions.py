"""Tests de integración para Listings Restrictions API (sandbox SP-API).

Sandbox test case: cualquier ASIN válido con sellerId devuelve restricciones.
Requiere seller_id — usa listings_client fixture.
"""

import pytest

from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestListingsRestrictionsSandbox:

    def test_get_listings_restrictions(self, listings_client):
        """Sandbox devuelve restricciones de ejemplo para cualquier ASIN."""
        result = listings_client.get_listings_restrictions("B00V5DG6IQ")
        assert isinstance(result, list)
        if result:
            assert "conditionType" in result[0]
