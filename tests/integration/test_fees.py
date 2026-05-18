"""Integración: ProductFees V0 API.
Sandbox test case (productFeesV0.json):
  ASIN='B00V5DG6IQ', Identifier='UmaS1', price=10 USD, shipping=10 USD, is_fba=False

La librería hardcodea Identifier=ASIN en create_fees_body(), pero el sandbox
requiere Identifier="UmaS1". En producción no afecta porque Identifier es solo
un correlation ID. Usamos _request directo para enviar el body exacto.
"""

import pytest

from tests.conftest import skip_without_credentials

pytestmark = [pytest.mark.integration, skip_without_credentials]

SANDBOX_FEES_BODY = {
    "FeesEstimateRequest": {
        "MarketplaceId": "ATVPDKIKX0DER",
        "IsAmazonFulfilled": False,
        "PriceToEstimateFees": {
            "ListingPrice": {"CurrencyCode": "USD", "Amount": 10},
            "Shipping": {"CurrencyCode": "USD", "Amount": 10},
            "Points": {"PointsNumber": 0, "PointsMonetaryValue": {"CurrencyCode": "USD", "Amount": 0}},
        },
        "Identifier": "UmaS1",
    }
}


class TestProductFeesSandbox:
    def test_fees_estimate_returns_success(self, client):
        api = client._product_fees_api()
        resp = api._request("/products/fees/v0/items/B00V5DG6IQ/feesEstimate", data=SANDBOX_FEES_BODY, params={"method": "POST"}, add_marketplace=False)
        assert resp.payload["FeesEstimateResult"]["Status"] == "Success"

    def test_fees_estimate_has_total(self, client):
        api = client._product_fees_api()
        resp = api._request("/products/fees/v0/items/B00V5DG6IQ/feesEstimate", data=SANDBOX_FEES_BODY, params={"method": "POST"}, add_marketplace=False)
        total = resp.payload["FeesEstimateResult"]["FeesEstimate"]["TotalFeesEstimate"]
        assert "CurrencyCode" in total
        assert float(total["Amount"]) > 0

    def test_fees_estimate_has_fee_detail_list(self, client):
        api = client._product_fees_api()
        resp = api._request("/products/fees/v0/items/B00V5DG6IQ/feesEstimate", data=SANDBOX_FEES_BODY, params={"method": "POST"}, add_marketplace=False)
        assert isinstance(resp.payload["FeesEstimateResult"]["FeesEstimate"]["FeeDetailList"], list)

    def test_library_wrapper_error_is_descriptive(self, client):
        with pytest.raises(RuntimeError) as exc_info:
            client.get_fees_estimate(asin="B00V5DG6IQ", price=10.0)
        assert "fees de B00V5DG6IQ" in str(exc_info.value)
