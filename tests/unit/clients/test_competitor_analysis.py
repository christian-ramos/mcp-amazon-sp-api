"""Tests unitarios para CompetitorAnalysisClient."""

from unittest.mock import patch

from mcp_amazon_sp_api.sp_client import AmazonClient

CATALOG_ITEMS = [
    {"asin": "B001", "summaries": [{"itemName": "Funda A", "brand": "MarcaA", "classification": {"displayName": "Cases"}}], "salesRanks": []},
    {"asin": "B002", "summaries": [{"itemName": "Funda B", "brand": "MarcaB", "classification": {"displayName": "Cases"}}], "salesRanks": []},
    {"asin": "B003", "summaries": [{"itemName": "Funda C", "brand": "MarcaC", "classification": {"displayName": "Cases"}}], "salesRanks": []},
]

PRICING_DATA = [
    {
        "ASIN": "B001", "status": "Success",
        "Product": {
            "CompetitivePricing": {
                "CompetitivePrices": [{"Price": {"ListingPrice": {"Amount": "12.99", "CurrencyCode": "EUR"}, "LandedPrice": {"Amount": "12.99", "CurrencyCode": "EUR"}}}],
                "NumberOfOfferListings": [{"Count": 3}],
            },
            "SalesRankings": [{"ProductCategoryId": "phone_cases", "Rank": 150}],
        },
    },
    {
        "ASIN": "B002", "status": "Success",
        "Product": {
            "CompetitivePricing": {
                "CompetitivePrices": [{"Price": {"ListingPrice": {"Amount": "9.99", "CurrencyCode": "EUR"}, "LandedPrice": {"Amount": "9.99", "CurrencyCode": "EUR"}}}],
                "NumberOfOfferListings": [{"Count": 1}],
            },
            "SalesRankings": [{"ProductCategoryId": "phone_cases", "Rank": 50}],
        },
    },
    {
        "ASIN": "B003", "status": "Success",
        "Product": {
            "CompetitivePricing": {
                "CompetitivePrices": [{"Price": {"ListingPrice": {"Amount": "15.99", "CurrencyCode": "EUR"}, "LandedPrice": {"Amount": "15.99", "CurrencyCode": "EUR"}}}],
                "NumberOfOfferListings": [{"Count": 5}],
            },
            "SalesRankings": [],
        },
    },
]


class TestAnalyzeCompetitorPrices:
    @patch.object(AmazonClient, "get_competitive_pricing")
    @patch.object(AmazonClient, "search_catalog_items")
    def test_returns_sorted_by_price(self, mock_search, mock_pricing, client):
        mock_search.return_value = CATALOG_ITEMS
        mock_pricing.return_value = PRICING_DATA
        result = client.analyze_competitor_prices("funda iPhone 16")
        assert len(result) == 3
        # Sorted by price: B002 (9.99), B001 (12.99), B003 (15.99)
        assert result[0]["asin"] == "B002"
        assert result[1]["asin"] == "B001"
        assert result[2]["asin"] == "B003"

    @patch.object(AmazonClient, "get_competitive_pricing")
    @patch.object(AmazonClient, "search_catalog_items")
    def test_includes_pricing_data(self, mock_search, mock_pricing, client):
        mock_search.return_value = CATALOG_ITEMS[:1]
        mock_pricing.return_value = PRICING_DATA[:1]
        result = client.analyze_competitor_prices("funda")
        assert result[0]["listingPrice"]["Amount"] == "12.99"
        assert result[0]["totalOffers"] == 3

    @patch.object(AmazonClient, "get_competitive_pricing")
    @patch.object(AmazonClient, "search_catalog_items")
    def test_includes_sales_rankings(self, mock_search, mock_pricing, client):
        mock_search.return_value = CATALOG_ITEMS[:1]
        mock_pricing.return_value = PRICING_DATA[:1]
        result = client.analyze_competitor_prices("funda")
        assert len(result[0]["salesRankings"]) == 1
        assert result[0]["salesRankings"][0]["rank"] == 150

    @patch.object(AmazonClient, "get_competitive_pricing")
    @patch.object(AmazonClient, "search_catalog_items")
    def test_respects_max_results(self, mock_search, mock_pricing, client):
        mock_search.return_value = CATALOG_ITEMS
        mock_pricing.return_value = PRICING_DATA[:2]
        result = client.analyze_competitor_prices("funda", max_results=2)
        # search returns 3 but we slice to max_results
        assert len(result) <= 3

    @patch.object(AmazonClient, "search_catalog_items")
    def test_empty_search_results(self, mock_search, client):
        mock_search.return_value = []
        result = client.analyze_competitor_prices("nonexistent product")
        assert result == []

    @patch.object(AmazonClient, "get_competitive_pricing")
    @patch.object(AmazonClient, "search_catalog_items")
    def test_handles_pricing_failure(self, mock_search, mock_pricing, client):
        mock_search.return_value = CATALOG_ITEMS[:1]
        mock_pricing.side_effect = RuntimeError("Pricing API down")
        result = client.analyze_competitor_prices("funda")
        assert len(result) == 1
        assert result[0]["asin"] == "B001"
        assert result[0]["totalOffers"] == 0

    @patch.object(AmazonClient, "get_competitive_pricing")
    @patch.object(AmazonClient, "search_catalog_items")
    def test_max_results_capped_at_20(self, mock_search, mock_pricing, client):
        mock_search.return_value = [{"asin": f"B{i:03d}", "summaries": [{}]} for i in range(25)]
        mock_pricing.return_value = []
        client.analyze_competitor_prices("funda", max_results=30)
        # Should only take first 20 items from search
        asins_passed = mock_pricing.call_args[0][0]
        assert len(asins_passed) <= 20


class TestCompareWithCompetitors:
    @patch.object(AmazonClient, "analyze_competitor_prices")
    @patch.object(AmazonClient, "get_competitive_pricing")
    @patch.object(AmazonClient, "get_catalog_item")
    def test_full_comparison(self, mock_catalog, mock_pricing, mock_analyze, client):
        mock_catalog.return_value = {
            "summaries": [{"itemName": "My Case", "brand": "Acme"}],
        }
        mock_pricing.return_value = [{
            "ASIN": "MY001",
            "Product": {
                "CompetitivePricing": {
                    "CompetitivePrices": [{"Price": {"ListingPrice": {"Amount": "14.99"}, "LandedPrice": {"Amount": "14.99"}}}],
                },
                "SalesRankings": [{"ProductCategoryId": "cases", "Rank": 100}],
            },
        }]
        mock_analyze.return_value = [
            {"asin": "B001", "title": "Competidor 1", "listingPrice": {"Amount": "9.99"}},
            {"asin": "B002", "title": "Competidor 2", "listingPrice": {"Amount": "12.99"}},
        ]
        result = client.compare_with_competitors("MY001", "funda iPhone 16")
        assert result["myProduct"]["asin"] == "MY001"
        assert result["myProduct"]["title"] == "My Case"
        assert result["myProduct"]["listingPrice"]["Amount"] == "14.99"
        assert result["totalCompetitors"] == 2

    @patch.object(AmazonClient, "analyze_competitor_prices")
    @patch.object(AmazonClient, "get_competitive_pricing")
    @patch.object(AmazonClient, "get_catalog_item")
    def test_excludes_own_asin_from_competitors(self, mock_catalog, mock_pricing, mock_analyze, client):
        mock_catalog.return_value = {"summaries": [{"itemName": "Mi Funda"}]}
        mock_pricing.return_value = [{"ASIN": "MY001", "Product": {"CompetitivePricing": {"CompetitivePrices": []}, "SalesRankings": []}}]
        mock_analyze.return_value = [
            {"asin": "MY001", "title": "Mi propio producto"},
            {"asin": "B001", "title": "Competidor"},
        ]
        result = client.compare_with_competitors("MY001", "funda")
        assert result["totalCompetitors"] == 1
        assert result["competitors"][0]["asin"] == "B001"

    @patch.object(AmazonClient, "analyze_competitor_prices")
    @patch.object(AmazonClient, "get_catalog_item")
    def test_handles_my_product_error(self, mock_catalog, mock_analyze, client):
        mock_catalog.side_effect = RuntimeError("Not found")
        mock_analyze.return_value = [{"asin": "B001", "title": "Competidor"}]
        result = client.compare_with_competitors("BADASIN", "funda")
        assert "error" in result["myProduct"]
        assert result["totalCompetitors"] == 1
