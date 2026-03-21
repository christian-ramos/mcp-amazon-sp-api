"""Tests de integración para Products Pricing API (sandbox SP-API).

Sandbox test cases de productPricingV0.json:
- getCompetitivePricing: MarketplaceId=ATVPDKIKX0DER, ItemType=Asin
- getItemOffers: Asin=B00V5DG6IQ, ItemCondition=New
- getProductPricing: MarketplaceId=ATVPDKIKX0DER, ItemType=Asin
"""

import pytest

from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestPricingSandbox:

    def test_get_competitive_pricing(self, client):
        """Competitive pricing para ASINs del sandbox."""
        result = client.get_competitive_pricing(["B00V5DG6IQ", "B00551Q3CS"])
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_get_item_offers(self, client):
        """Ofertas para ASIN B00V5DG6IQ en sandbox."""
        result = client.get_item_offers("B00V5DG6IQ", item_condition="New")
        assert isinstance(result, dict)

    def test_get_product_pricing(self, client):
        """Product pricing para ASINs del sandbox."""
        result = client.get_product_pricing(["B00V5DG6IQ", "B00551Q3CS"])
        assert isinstance(result, list)
        assert len(result) >= 1
