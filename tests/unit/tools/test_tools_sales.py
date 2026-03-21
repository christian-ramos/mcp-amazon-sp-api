"""Tests de tools MCP: Ventas y Tráfico."""

from mcp_amazon_sp_api.server import get_sales_and_traffic
from .conftest import parse


class TestGetSalesAndTraffic:
    def test_returns_traffic_data(self, mock_client):
        mock_client.get_sales_and_traffic_report.return_value = [
            {"asin": "B001", "sessions": 100, "conversion": "5.2", "buyBoxPct": "95.0"},
            {"asin": "B002", "sessions": 50, "conversion": "3.1", "buyBoxPct": "88.0"},
        ]
        result = parse(get_sales_and_traffic(days_back=7))
        assert result["totalEntries"] == 2
        assert result["salesAndTraffic"][0]["sessions"] == 100
        assert "Últimos 7 días" in result["period"]

    def test_limits_to_200(self, mock_client):
        mock_client.get_sales_and_traffic_report.return_value = [
            {"asin": f"B{i:03d}"} for i in range(250)
        ]
        result = parse(get_sales_and_traffic())
        assert len(result["salesAndTraffic"]) == 200
        assert result["totalEntries"] == 250

    def test_error_handling(self, mock_client):
        mock_client.get_sales_and_traffic_report.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_sales_and_traffic())
