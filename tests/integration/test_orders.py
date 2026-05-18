"""Integración: Orders API — sandbox: CreatedAfter='TEST_CASE_200', order_id='TEST_CASE_200'."""

import pytest

from tests.conftest import skip_without_credentials

pytestmark = [pytest.mark.integration, skip_without_credentials]


class TestGetOrdersSandbox:
    def test_returns_non_empty_list(self, client):
        orders = client.get_orders(created_after="TEST_CASE_200", max_results=5)
        assert isinstance(orders, list)
        assert len(orders) > 0

    def test_order_has_required_fields(self, client):
        order = client.get_orders(created_after="TEST_CASE_200", max_results=1)[0]
        assert "AmazonOrderId" in order
        assert "OrderStatus" in order
        assert "PurchaseDate" in order
        assert "CurrencyCode" in order["OrderTotal"]

    def test_respects_max_results(self, client):
        assert len(client.get_orders(created_after="TEST_CASE_200", max_results=1)) <= 1

    def test_order_has_fulfillment_info(self, client):
        order = client.get_orders(created_after="TEST_CASE_200", max_results=1)[0]
        assert "FulfillmentChannel" in order


class TestGetOrderItemsSandbox:
    def test_returns_non_empty_list(self, client):
        items = client.get_order_items("TEST_CASE_200")
        assert len(items) > 0

    def test_item_has_required_fields(self, client):
        item = client.get_order_items("TEST_CASE_200")[0]
        for field in ("ASIN", "SellerSKU", "Title", "QuantityOrdered"):
            assert field in item

    def test_item_has_price_and_tax(self, client):
        item = client.get_order_items("TEST_CASE_200")[0]
        assert "CurrencyCode" in item["ItemPrice"]
        assert "Amount" in item["ItemTax"]

    def test_rejects_invalid_order_id(self, client):
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_order_items("902-1845936-5435065")
