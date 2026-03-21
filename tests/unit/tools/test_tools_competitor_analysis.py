"""Tests de tools MCP: Análisis de competencia."""

from mcp_amazon_sp_api.server import analyze_competitor_prices, compare_with_competitors
from .conftest import parse


class TestAnalyzeCompetitorPrices:
    def test_returns_results(self, mock_client):
        mock_client.analyze_competitor_prices.return_value = [
            {"asin": "B001", "title": "Bottle A", "listingPrice": {"Amount": "9.99"}, "totalOffers": 3},
            {"asin": "B002", "title": "Bottle B", "listingPrice": {"Amount": "12.99"}, "totalOffers": 1},
        ]
        result = parse(analyze_competitor_prices(keywords="water bottle 16"))
        assert result["keywords"] == "water bottle 16"
        assert result["totalResults"] == 2
        assert result["competitors"][0]["asin"] == "B001"

    def test_passes_max_results(self, mock_client):
        mock_client.analyze_competitor_prices.return_value = []
        parse(analyze_competitor_prices(keywords="bottle", max_results=5))
        mock_client.analyze_competitor_prices.assert_called_once_with("bottle", 5)

    def test_error_handling(self, mock_client):
        mock_client.analyze_competitor_prices.side_effect = RuntimeError("Fail")
        assert "error" in parse(analyze_competitor_prices(keywords="bottle"))


class TestCompareWithCompetitors:
    def test_returns_comparison(self, mock_client):
        mock_client.compare_with_competitors.return_value = {
            "myProduct": {"asin": "MY001", "title": "My Case", "listingPrice": {"Amount": "14.99"}},
            "competitors": [
                {"asin": "B001", "title": "Competidor", "listingPrice": {"Amount": "9.99"}},
            ],
            "totalCompetitors": 1,
        }
        result = parse(compare_with_competitors(my_asin="MY001", keywords="water bottle 16"))
        assert result["myProduct"]["asin"] == "MY001"
        assert result["totalCompetitors"] == 1

    def test_error_handling(self, mock_client):
        mock_client.compare_with_competitors.side_effect = RuntimeError("Fail")
        assert "error" in parse(compare_with_competitors(my_asin="X", keywords="bottle"))
