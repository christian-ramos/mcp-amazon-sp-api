"""Tests de tools MCP: Precios y competencia."""

from mcp_amazon_sp_api.tools.pricing import get_competitive_pricing, get_competitor_offers

from .conftest import parse


class TestGetCompetitivePricing:
    def test_returns_formatted_pricing(self, mock_client):
        mock_client.get_competitive_pricing.return_value = [{
            "ASIN": "B001",
            "status": "Success",
            "Product": {
                "CompetitivePricing": {
                    "CompetitivePrices": [{
                        "condition": "New",
                        "belongsToRequester": True,
                        "Price": {
                            "LandedPrice": {"Amount": "12.99", "CurrencyCode": "EUR"},
                            "ListingPrice": {"Amount": "10.99", "CurrencyCode": "EUR"},
                            "Shipping": {"Amount": "2.00", "CurrencyCode": "EUR"},
                        },
                    }],
                    "NumberOfOfferListings": [{"condition": "New", "Count": 5}],
                },
                "SalesRankings": [{"ProductCategoryId": "water_bottles", "Rank": 150}],
            },
        }]
        result = parse(get_competitive_pricing(asins="B001"))
        assert len(result) == 1
        assert result[0]["asin"] == "B001"
        assert len(result[0]["competitivePrices"]) == 1
        assert result[0]["competitivePrices"][0]["belongsToRequester"] is True

    def test_multiple_asins(self, mock_client):
        mock_client.get_competitive_pricing.return_value = [
            {"ASIN": "B001", "status": "Success", "Product": {"CompetitivePricing": {"CompetitivePrices": [], "NumberOfOfferListings": []}, "SalesRankings": []}},
            {"ASIN": "B002", "status": "Success", "Product": {"CompetitivePricing": {"CompetitivePrices": [], "NumberOfOfferListings": []}, "SalesRankings": []}},
        ]
        result = parse(get_competitive_pricing(asins="B001, B002"))
        assert len(result) == 2
        mock_client.get_competitive_pricing.assert_called_once_with(["B001", "B002"])

    def test_limits_to_20_asins(self, mock_client):
        mock_client.get_competitive_pricing.return_value = []
        asins = ",".join(f"B{i:03d}" for i in range(30))
        parse(get_competitive_pricing(asins=asins))
        called_with = mock_client.get_competitive_pricing.call_args[0][0]
        assert len(called_with) == 20

    def test_error_handling(self, mock_client):
        mock_client.get_competitive_pricing.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_competitive_pricing(asins="B001"))


class TestGetCompetitorOffers:
    def test_returns_offers(self, mock_client):
        mock_client.get_item_offers.return_value = {
            "Summary": {
                "TotalOfferCount": 3,
                "LowestPrices": [{"condition": "New", "LandedPrice": {"Amount": "9.99"}}],
                "BuyBoxPrices": [{"condition": "New", "LandedPrice": {"Amount": "10.99"}}],
                "BuyBoxEligibleOfferCounts": [{"condition": "New", "OfferCount": 2}],
            },
            "Offers": [{
                "SellerId": "A1SELLER",
                "SubCondition": "New",
                "ListingPrice": {"Amount": "10.99", "CurrencyCode": "EUR"},
                "Shipping": {"Amount": "0.00", "CurrencyCode": "EUR"},
                "IsFulfilledByAmazon": True,
                "IsBuyBoxWinner": True,
                "IsFeaturedMerchant": True,
            }],
        }
        result = parse(get_competitor_offers(asin="B001"))
        assert result["totalOffers"] == 3
        assert len(result["offers"]) == 1
        assert result["offers"][0]["isBuyBoxWinner"] is True
        assert result["offers"][0]["isFba"] is True

    def test_limits_offers_to_20(self, mock_client):
        mock_client.get_item_offers.return_value = {
            "Summary": {"TotalOfferCount": 30},
            "Offers": [{"SellerId": f"A{i}"} for i in range(30)],
        }
        result = parse(get_competitor_offers(asin="B001"))
        assert len(result["offers"]) == 20

    def test_error_handling(self, mock_client):
        mock_client.get_item_offers.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_competitor_offers(asin="B001"))
