"""Tests de tools MCP: Invoices."""

from mcp_amazon_sp_api.tools.invoices import download_invoice, get_invoices
from .conftest import parse


class TestGetInvoices:
    def test_returns_invoices(self, mock_client):
        mock_client.get_invoices.return_value = [
            {"invoiceId": "INV-1"}, {"invoiceId": "INV-2"},
        ]
        result = parse(get_invoices())
        assert result["totalInvoices"] == 2

    def test_filters_by_order(self, mock_client):
        mock_client.get_invoices.return_value = []
        parse(get_invoices(order_id="111"))
        kwargs = mock_client.get_invoices.call_args[1]
        assert kwargs["order_id"] == "111"

    def test_error_handling(self, mock_client):
        mock_client.get_invoices.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_invoices())


class TestDownloadInvoice:
    def test_returns_document(self, mock_client):
        mock_client.get_invoice_document.return_value = {"invoiceId": "INV-1", "url": "https://..."}
        result = parse(download_invoice(invoice_id="INV-1"))
        assert result["invoiceId"] == "INV-1"

    def test_error_handling(self, mock_client):
        mock_client.get_invoice_document.side_effect = RuntimeError("Fail")
        assert "error" in parse(download_invoice(invoice_id="BAD"))
