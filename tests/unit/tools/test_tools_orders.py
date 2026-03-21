"""Tests de tools MCP: orders y sales summary."""

from mcp_amazon_sp_api.server import get_orders, get_order_items, get_sales_summary
from .conftest import parse


class TestGetOrders:
    def test_returns_formatted_orders(self, mock_client):
        mock_client.get_orders.return_value = [{
            "AmazonOrderId": "111-222-333", "OrderStatus": "Shipped",
            "PurchaseDate": "2025-03-15T10:00:00Z",
            "OrderTotal": {"Amount": "19.99", "CurrencyCode": "EUR"},
            "NumberOfItemsShipped": 2, "NumberOfItemsUnshipped": 0,
            "FulfillmentChannel": "AFN",
        }]
        result = parse(get_orders(days_back=7))
        assert len(result) == 1
        assert result[0]["orderId"] == "111-222-333"
        assert result[0]["items"] == 2

    def test_filters_by_status(self, mock_client):
        mock_client.get_orders.return_value = [
            {"AmazonOrderId": "111", "OrderStatus": "Shipped", "NumberOfItemsShipped": 1, "NumberOfItemsUnshipped": 0},
            {"AmazonOrderId": "222", "OrderStatus": "Unshipped", "NumberOfItemsShipped": 0, "NumberOfItemsUnshipped": 1},
        ]
        result = parse(get_orders(days_back=7, status="Shipped"))
        assert len(result) == 1
        assert result[0]["orderId"] == "111"

    def test_status_filter_case_insensitive(self, mock_client):
        mock_client.get_orders.return_value = [
            {"AmazonOrderId": "111", "OrderStatus": "Shipped", "NumberOfItemsShipped": 1, "NumberOfItemsUnshipped": 0},
        ]
        assert len(parse(get_orders(days_back=7, status="shipped"))) == 1

    def test_error_handling(self, mock_client):
        mock_client.get_orders.side_effect = RuntimeError("Timeout")
        assert "error" in parse(get_orders(days_back=7))


class TestGetOrderItems:
    def test_returns_items(self, mock_client):
        mock_client.get_order_items.return_value = [{
            "ASIN": "B001", "SellerSKU": "SKU-001", "Title": "Funda iPhone 16",
            "QuantityOrdered": 2,
            "ItemPrice": {"Amount": "19.99", "CurrencyCode": "EUR"},
            "ItemTax": {"Amount": "4.20", "CurrencyCode": "EUR"},
        }]
        result = parse(get_order_items(order_id="111-222-333"))
        assert result[0]["asin"] == "B001"
        assert result[0]["quantity"] == 2

    def test_error_handling(self, mock_client):
        mock_client.get_order_items.side_effect = RuntimeError("Not found")
        assert "error" in parse(get_order_items(order_id="INVALID"))


class TestGetSalesSummary:
    def test_aggregates_correctly(self, mock_client):
        mock_client.get_orders.return_value = [
            {"AmazonOrderId": "111", "OrderStatus": "Shipped", "OrderTotal": {"Amount": "19.99", "CurrencyCode": "EUR"}, "NumberOfItemsShipped": 1, "NumberOfItemsUnshipped": 0},
            {"AmazonOrderId": "222", "OrderStatus": "Shipped", "OrderTotal": {"Amount": "29.99", "CurrencyCode": "EUR"}, "NumberOfItemsShipped": 2, "NumberOfItemsUnshipped": 0},
        ]
        mock_client.get_order_items.side_effect = [
            [{"ASIN": "B001", "Title": "Funda A", "QuantityOrdered": 1, "ItemPrice": {"Amount": "19.99"}}],
            [{"ASIN": "B001", "Title": "Funda A", "QuantityOrdered": 1, "ItemPrice": {"Amount": "14.99"}},
             {"ASIN": "B002", "Title": "Funda B", "QuantityOrdered": 1, "ItemPrice": {"Amount": "15.00"}}],
        ]
        result = parse(get_sales_summary(days_back=30))
        assert result["totalOrders"] == 2
        assert result["totalUnits"] == 3
        assert result["topProducts"][0]["asin"] == "B001"

    def test_handles_order_items_failure_gracefully(self, mock_client):
        mock_client.get_orders.return_value = [
            {"AmazonOrderId": "111", "OrderStatus": "Shipped", "OrderTotal": {"Amount": "19.99", "CurrencyCode": "EUR"}, "NumberOfItemsShipped": 1, "NumberOfItemsUnshipped": 0},
        ]
        mock_client.get_order_items.side_effect = RuntimeError("Items API down")
        result = parse(get_sales_summary(days_back=7))
        assert result["totalOrders"] == 1
        assert result["topProducts"] == []

    def test_empty_orders(self, mock_client):
        mock_client.get_orders.return_value = []
        result = parse(get_sales_summary(days_back=7))
        assert result["totalOrders"] == 0

    def test_error_handling(self, mock_client):
        mock_client.get_orders.side_effect = RuntimeError("Connection error")
        assert "error" in parse(get_sales_summary(days_back=7))
