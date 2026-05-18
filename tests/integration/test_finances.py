"""Integración: Finances V0 API.
Sandbox test cases (financesV0.json):
  listFinancialEvents: MaxResultsPerPage=10, NextToken="jehgri34yo7jr9e8f984tr9i4o"
  getFinancialEventsForOrder: orderId="485-734-5434857", MaxResultsPerPage=10
  Error: orderId="BAD-ORDER"
"""

import pytest

from tests.conftest import skip_without_credentials

pytestmark = [pytest.mark.integration, skip_without_credentials]


class TestFinancesSandbox:
    def test_list_financial_events_returns_data(self, client):
        api = client._finances_api()
        resp = api.list_financial_events(MaxResultsPerPage=10, NextToken="jehgri34yo7jr9e8f984tr9i4o")
        events = resp.payload.get("FinancialEvents", {})
        assert isinstance(events, dict)
        assert any(isinstance(v, list) for v in events.values())

    def test_list_financial_events_has_event_types(self, client):
        api = client._finances_api()
        resp = api.list_financial_events(MaxResultsPerPage=10, NextToken="jehgri34yo7jr9e8f984tr9i4o")
        events = resp.payload.get("FinancialEvents", {})
        known_types = {"PayWithAmazonEventList", "ServiceProviderCreditEventList", "RentalTransactionEventList", "ProductAdsPaymentEventList", "ShipmentEventList", "RefundEventList"}
        assert known_types & set(events.keys())

    def test_get_financial_events_for_order_returns_data(self, client):
        events = client.get_financial_events_for_order("485-734-5434857", max_results=10)
        assert isinstance(events, dict)
        assert any(isinstance(v, list) and len(v) > 0 for v in events.values())

    def test_get_financial_events_for_order_has_amounts(self, client):
        events = client.get_financial_events_for_order("485-734-5434857", max_results=10)
        found = any("CurrencyCode" in str(e) for v in events.values() if isinstance(v, list) for e in v if isinstance(e, dict))
        assert found

    def test_bad_order_id_raises_error(self, client):
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_financial_events_for_order("BAD-ORDER")
