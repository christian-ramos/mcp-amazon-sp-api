"""Tests unitarios para SalesReportsClient."""

from unittest.mock import patch

import pytest

from mcp_amazon_sp_api.clients.reports_sales import SALES_AND_TRAFFIC
from mcp_amazon_sp_api.sp_client import AmazonClient


class TestSalesReportsMethods:

    @patch.object(AmazonClient, "request_and_download_report")
    def test_get_sales_and_traffic_report(self, mock_rad, client):
        mock_rad.return_value = '[{"asin": "B001", "sessions": 100, "buyBoxPct": "95.0"}]'
        result = client.get_sales_and_traffic_report("2025-01-01", "2025-01-31")
        assert result[0]["sessions"] == 100
        assert mock_rad.call_args[0][0] == SALES_AND_TRAFFIC
        assert mock_rad.call_args[0][1] == "2025-01-01"
        assert mock_rad.call_args[0][2] == "2025-01-31"

    @patch.object(AmazonClient, "request_and_download_report")
    def test_tsv_content_parsed(self, mock_rad, client):
        mock_rad.return_value = "asin\tsessions\tconversion\nB001\t100\t5.2\nB002\t50\t3.1\n"
        result = client.get_sales_and_traffic_report("2025-01-01", "2025-01-31")
        assert len(result) == 2
        assert result[0]["asin"] == "B001"

    @patch.object(AmazonClient, "request_and_download_report")
    def test_propagates_error(self, mock_rad, client):
        mock_rad.side_effect = RuntimeError("Report failed")
        with pytest.raises(RuntimeError, match="Report failed"):
            client.get_sales_and_traffic_report("2025-01-01", "2025-01-31")

    @patch.object(AmazonClient, "request_and_download_report")
    def test_custom_poll_and_timeout(self, mock_rad, client):
        mock_rad.return_value = "[]"
        client.get_sales_and_traffic_report(
            "2025-01-01", "2025-01-31",
            poll_interval=5, timeout=60,
        )
        assert mock_rad.call_args[1]["poll_interval"] == 5
        assert mock_rad.call_args[1]["timeout"] == 60
