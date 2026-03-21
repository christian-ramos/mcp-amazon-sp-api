"""Tests unitarios para OrdersClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient
from .conftest import make_response, make_api_error


class TestGetOrders:
    @patch.object(AmazonClient, "_orders_api")
    def test_returns_orders(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_orders.return_value = make_response({
            "Orders": [
                {"AmazonOrderId": "111", "OrderStatus": "Shipped"},
                {"AmazonOrderId": "222", "OrderStatus": "Unshipped"},
            ],
            "NextToken": None,
        })
        orders = client.get_orders(created_after="2025-01-01T00:00:00Z")
        assert len(orders) == 2
        assert orders[0]["AmazonOrderId"] == "111"

    @patch.object(AmazonClient, "_orders_api")
    def test_paginates(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_orders.side_effect = [
            make_response({"Orders": [{"AmazonOrderId": "111"}], "NextToken": "page2"}),
            make_response({"Orders": [{"AmazonOrderId": "222"}], "NextToken": None}),
        ]
        orders = client.get_orders(created_after="2025-01-01T00:00:00Z")
        assert len(orders) == 2
        assert mock_api.get_orders.call_count == 2

    @patch.object(AmazonClient, "_orders_api")
    def test_respects_max_results(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_orders.return_value = make_response({
            "Orders": [{"AmazonOrderId": str(i)} for i in range(10)],
            "NextToken": "more",
        })
        orders = client.get_orders(created_after="2025-01-01T00:00:00Z", max_results=5)
        assert len(orders) == 5

    @patch.object(AmazonClient, "_orders_api")
    def test_raises_runtime_error_on_api_failure(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_orders.side_effect = make_api_error(403)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_orders(created_after="2025-01-01T00:00:00Z")

    @patch.object(AmazonClient, "_orders_api")
    def test_passes_created_before(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_orders.return_value = make_response({"Orders": [], "NextToken": None})
        client.get_orders(created_after="2025-01-01", created_before="2025-01-31")
        assert mock_api.get_orders.call_args[1]["CreatedBefore"] == "2025-01-31"


class TestGetOrderItems:
    @patch.object(AmazonClient, "_orders_api")
    def test_returns_items(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_order_items.return_value = make_response({
            "OrderItems": [{"ASIN": "B001", "QuantityOrdered": 2}, {"ASIN": "B002", "QuantityOrdered": 1}]
        })
        items = client.get_order_items("111-222-333")
        assert len(items) == 2
        assert items[0]["ASIN"] == "B001"

    @patch.object(AmazonClient, "_orders_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_order_items.side_effect = make_api_error(500)
        with pytest.raises(RuntimeError, match="items de 111"):
            client.get_order_items("111")
