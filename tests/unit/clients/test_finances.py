"""Tests unitarios para FinancesClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient
from .conftest import make_response, make_api_error


class TestGetFinancialEvents:
    @patch.object(AmazonClient, "_finances_api")
    def test_returns_financial_events(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.list_financial_events.return_value = make_response({
            "FinancialEvents": {"ShipmentEventList": [{"AmazonOrderId": "111"}], "RefundEventList": []}
        })
        events = client.get_financial_events(posted_after="2025-01-01")
        assert "ShipmentEventList" in events

    @patch.object(AmazonClient, "_finances_api")
    def test_passes_posted_before(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.list_financial_events.return_value = make_response({"FinancialEvents": {}})
        client.get_financial_events(posted_after="2025-01-01", posted_before="2025-01-31")
        assert mock_api.list_financial_events.call_args[1]["PostedBefore"] == "2025-01-31"

    @patch.object(AmazonClient, "_finances_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.list_financial_events.side_effect = make_api_error(500)
        with pytest.raises(RuntimeError, match="eventos financieros"):
            client.get_financial_events(posted_after="2025-01-01")


class TestGetFinancialEventsForOrder:
    @patch.object(AmazonClient, "_finances_api")
    def test_returns_events(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_financial_events_for_order.return_value = make_response({
            "FinancialEvents": {"ShipmentEventList": [{"ShipmentItemList": [{"SellerSKU": "SKU-001"}]}], "RefundEventList": []}
        })
        events = client.get_financial_events_for_order("111-222-333")
        assert len(events["ShipmentEventList"]) == 1

    @patch.object(AmazonClient, "_finances_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_financial_events_for_order.side_effect = make_api_error(404)
        with pytest.raises(RuntimeError, match="finanzas de 111"):
            client.get_financial_events_for_order("111")
