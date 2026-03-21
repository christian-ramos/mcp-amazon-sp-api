"""Tests unitarios para FbaReportsClient."""

from unittest.mock import patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient
from mcp_amazon_sp_api.clients.reports_fba import (
    FBA_INVENTORY, FBA_INVENTORY_HEALTH, FBA_RETURNS,
    FBA_REIMBURSEMENTS, FBA_STORAGE_FEES, FBA_LONGTERM_STORAGE,
    RESTOCK_RECOMMENDATIONS,
)


class TestFbaReportsMethods:
    """Verifica que cada método llama a request_and_download_report con el report type correcto."""

    @patch.object(AmazonClient, "request_and_download_report")
    def test_get_fba_inventory_report(self, mock_rad, client):
        mock_rad.return_value = '[{"sku": "SKU-1", "qty": 10}]'
        result = client.get_fba_inventory_report()
        assert result[0]["sku"] == "SKU-1"
        assert mock_rad.call_args[0][0] == FBA_INVENTORY

    @patch.object(AmazonClient, "request_and_download_report")
    def test_get_fba_inventory_health(self, mock_rad, client):
        mock_rad.return_value = '[{"sku": "SKU-1", "age": "90"}]'
        result = client.get_fba_inventory_health()
        assert result[0]["age"] == "90"
        assert mock_rad.call_args[0][0] == FBA_INVENTORY_HEALTH

    @patch.object(AmazonClient, "request_and_download_report")
    def test_get_fba_returns_report(self, mock_rad, client):
        mock_rad.return_value = '[{"sku": "SKU-1", "reason": "DEFECTIVE"}]'
        result = client.get_fba_returns_report("2025-01-01", "2025-01-31")
        assert result[0]["reason"] == "DEFECTIVE"
        assert mock_rad.call_args[0][0] == FBA_RETURNS
        assert mock_rad.call_args[0][1] == "2025-01-01"
        assert mock_rad.call_args[0][2] == "2025-01-31"

    @patch.object(AmazonClient, "request_and_download_report")
    def test_get_fba_reimbursements(self, mock_rad, client):
        mock_rad.return_value = '[{"sku": "SKU-1", "amount": "5.00"}]'
        result = client.get_fba_reimbursements("2025-01-01", "2025-01-31")
        assert result[0]["amount"] == "5.00"
        assert mock_rad.call_args[0][0] == FBA_REIMBURSEMENTS

    @patch.object(AmazonClient, "request_and_download_report")
    def test_get_fba_storage_fees(self, mock_rad, client):
        mock_rad.return_value = '[{"sku": "SKU-1", "fee": "1.20"}]'
        result = client.get_fba_storage_fees()
        assert result[0]["fee"] == "1.20"
        assert mock_rad.call_args[0][0] == FBA_STORAGE_FEES

    @patch.object(AmazonClient, "request_and_download_report")
    def test_get_fba_longterm_storage_fees(self, mock_rad, client):
        mock_rad.return_value = '[{"sku": "SKU-1", "fee": "3.50"}]'
        result = client.get_fba_longterm_storage_fees()
        assert result[0]["fee"] == "3.50"
        assert mock_rad.call_args[0][0] == FBA_LONGTERM_STORAGE

    @patch.object(AmazonClient, "request_and_download_report")
    def test_get_restock_recommendations(self, mock_rad, client):
        mock_rad.return_value = '[{"sku": "SKU-1", "recommendedQty": "50"}]'
        result = client.get_restock_recommendations()
        assert result[0]["recommendedQty"] == "50"
        assert mock_rad.call_args[0][0] == RESTOCK_RECOMMENDATIONS

    @patch.object(AmazonClient, "request_and_download_report")
    def test_tsv_content_parsed(self, mock_rad, client):
        mock_rad.return_value = "sku\tqty\nSKU-1\t10\nSKU-2\t20\n"
        result = client.get_fba_inventory_report()
        assert len(result) == 2
        assert result[1]["qty"] == "20"

    @patch.object(AmazonClient, "request_and_download_report")
    def test_propagates_error(self, mock_rad, client):
        mock_rad.side_effect = RuntimeError("Report failed")
        with pytest.raises(RuntimeError, match="Report failed"):
            client.get_fba_inventory_report()

    @patch.object(AmazonClient, "request_and_download_report")
    def test_inventory_reports_pass_none_end_date(self, mock_rad, client):
        mock_rad.return_value = "[]"
        client.get_fba_inventory_report()
        assert mock_rad.call_args[0][2] is None

    @patch.object(AmazonClient, "request_and_download_report")
    def test_custom_poll_and_timeout(self, mock_rad, client):
        mock_rad.return_value = "[]"
        client.get_fba_returns_report(
            "2025-01-01", "2025-01-31",
            poll_interval=5, timeout=60,
        )
        assert mock_rad.call_args[1]["poll_interval"] == 5
        assert mock_rad.call_args[1]["timeout"] == 60
