"""Tests unitarios para InvoicesClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient
from .conftest import make_response, make_api_error


class TestGetInvoices:
    @patch.object(AmazonClient, "_invoices_api")
    def test_returns_invoices(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_invoices.return_value = make_response({
            "invoices": [{"invoiceId": "INV-1"}, {"invoiceId": "INV-2"}],
        })
        result = client.get_invoices()
        assert len(result) == 2

    @patch.object(AmazonClient, "_invoices_api")
    def test_filters_by_order(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_invoices.return_value = make_response({"invoices": []})
        client.get_invoices(order_id="111-222-333")
        kwargs = mock_api.get_invoices.call_args[1]
        assert kwargs["orderId"] == "111-222-333"

    @patch.object(AmazonClient, "_invoices_api")
    def test_filters_by_date(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_invoices.return_value = make_response({"invoices": []})
        client.get_invoices(date_from="2025-01-01", date_to="2025-01-31")
        kwargs = mock_api.get_invoices.call_args[1]
        assert kwargs["dateStart"] == "2025-01-01"
        assert kwargs["dateEnd"] == "2025-01-31"

    @patch.object(AmazonClient, "_invoices_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_invoices.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_invoices()


class TestGetInvoiceDocument:
    @patch.object(AmazonClient, "_invoices_api")
    def test_returns_document(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_invoices_document.return_value = make_response({
            "invoiceId": "INV-1", "url": "https://..."
        })
        result = client.get_invoice_document("INV-1")
        assert result["invoiceId"] == "INV-1"

    @patch.object(AmazonClient, "_invoices_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_invoices_document.side_effect = make_api_error(404)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_invoice_document("BAD")
