"""Tests de tools MCP: Brand Analytics."""

from mcp_amazon_sp_api.tools.brand_analytics import get_market_basket, get_repeat_purchases, get_search_performance, get_search_terms
from .conftest import parse


class TestGetSearchTerms:
    def test_returns_search_terms(self, mock_client):
        mock_client.get_search_terms_report.return_value = [
            {"term": "funda iphone 16", "clickShare": "5.2"},
            {"term": "carcasa iphone", "clickShare": "3.1"},
        ]
        result = parse(get_search_terms(days_back=30))
        assert result["totalTerms"] == 2
        assert result["searchTerms"][0]["term"] == "funda iphone 16"

    def test_limits_to_100(self, mock_client):
        mock_client.get_search_terms_report.return_value = [
            {"term": f"term-{i}"} for i in range(150)
        ]
        result = parse(get_search_terms())
        assert len(result["searchTerms"]) == 100
        assert result["totalTerms"] == 150

    def test_error_handling(self, mock_client):
        mock_client.get_search_terms_report.side_effect = RuntimeError("No brand")
        result = parse(get_search_terms())
        assert "error" in result


class TestGetSearchPerformance:
    def test_returns_performance(self, mock_client):
        mock_client.get_search_query_performance.return_value = [
            {"query": "funda", "impressions": 1000, "clicks": 50},
        ]
        result = parse(get_search_performance(asins="B001,B002"))
        assert result["totalEntries"] == 1
        assert result["performance"][0]["impressions"] == 1000
        mock_client.get_search_query_performance.assert_called_once_with(["B001", "B002"])

    def test_error_handling(self, mock_client):
        mock_client.get_search_query_performance.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_search_performance(asins="B001"))


class TestGetMarketBasket:
    def test_returns_basket(self, mock_client):
        mock_client.get_market_basket_report.return_value = [
            {"asin": "B001", "comboAsin": "B002", "comboPct": "12.5"},
        ]
        result = parse(get_market_basket())
        assert result["totalEntries"] == 1
        assert result["marketBasket"][0]["comboAsin"] == "B002"

    def test_error_handling(self, mock_client):
        mock_client.get_market_basket_report.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_market_basket())


class TestGetRepeatPurchases:
    def test_returns_repeat_data(self, mock_client):
        mock_client.get_repeat_purchase_report.return_value = [
            {"asin": "B001", "repeatRate": "0.15"},
        ]
        result = parse(get_repeat_purchases())
        assert result["totalEntries"] == 1
        assert result["repeatPurchases"][0]["repeatRate"] == "0.15"

    def test_error_handling(self, mock_client):
        mock_client.get_repeat_purchase_report.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_repeat_purchases())
