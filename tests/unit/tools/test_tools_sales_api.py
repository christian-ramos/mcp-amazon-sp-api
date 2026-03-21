"""Tests de tools MCP: Sales API."""

from mcp_amazon_sp_api.tools.sales_api import get_order_metrics
from .conftest import parse


class TestGetOrderMetrics:
    def test_returns_metrics(self, mock_client):
        mock_client.get_order_metrics.return_value = [
            {"interval": "2025-01-01--2025-01-02", "unitCount": 5, "orderCount": 3},
            {"interval": "2025-01-02--2025-01-03", "unitCount": 8, "orderCount": 4},
        ]
        result = parse(get_order_metrics(days_back=7))
        assert result["totalEntries"] == 2
        assert result["granularity"] == "Day"
        assert "Últimos 7 días" in result["period"]

    def test_passes_granularity(self, mock_client):
        mock_client.get_order_metrics.return_value = []
        parse(get_order_metrics(days_back=30, granularity="Week"))
        mock_client.get_order_metrics.assert_called_once_with(days_back=30, granularity="Week")

    def test_error_handling(self, mock_client):
        mock_client.get_order_metrics.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_order_metrics())
