"""Tests de tools MCP: catalog (list_products, get_product_details, get_sales_rankings)."""

from mcp_amazon_sp_api.tools.analysis import get_sales_rankings
from mcp_amazon_sp_api.tools.catalog_orders import get_product_details, list_products

from .conftest import parse


class TestListProducts:
    def test_with_keywords(self, mock_client):
        mock_client.search_catalog_items.return_value = [
            {"asin": "B001", "summaries": [{"itemName": "Water Bottle 500ml", "brand": "Acme"}]}
        ]
        result = parse(list_products(keywords="bottle"))
        assert result[0]["asin"] == "B001"
        mock_client.search_catalog_items.assert_called_once_with(keywords="bottle")

    def test_without_keywords_uses_default(self, mock_client):
        mock_client.search_catalog_items.return_value = []
        list_products()
        mock_client.search_catalog_items.assert_called_once_with(keywords="water bottle")

    def test_handles_empty_summaries(self, mock_client):
        mock_client.search_catalog_items.return_value = [{"asin": "B001", "summaries": []}]
        assert parse(list_products(keywords="test"))[0]["title"] is None

    def test_returns_error_on_exception(self, mock_client):
        mock_client.search_catalog_items.side_effect = RuntimeError("API down")
        assert "error" in parse(list_products(keywords="test"))


class TestGetProductDetails:
    def test_basic_details(self, mock_client):
        mock_client.get_catalog_item.return_value = {
            "summaries": [{"itemName": "Water Bottle 1L Stainless Steel", "brand": "Acme", "manufacturer": "Acme Co.", "classification": {"displayName": "Bottles"}}],
            "relationships": [], "images": [{"images": [{"url": "http://img1"}, {"url": "http://img2"}]}], "salesRanks": [{"rank": 5000}],
        }
        result = parse(get_product_details(asin="B001"))
        assert result["title"] == "Water Bottle 1L Stainless Steel"
        assert result["imageCount"] == 2

    def test_parent_child_relationships(self, mock_client):
        mock_client.get_catalog_item.return_value = {
            "summaries": [{"itemName": "Parent"}],
            "relationships": [{"relationships": [{"type": "VARIATION", "childAsins": ["B002", "B003"], "parentAsins": [], "variationTheme": {"name": "Color"}}]}],
            "images": [], "salesRanks": [],
        }
        result = parse(get_product_details(asin="B001"))
        assert result["relationships"][0]["childAsins"] == ["B002", "B003"]

    def test_error_handling(self, mock_client):
        mock_client.get_catalog_item.side_effect = RuntimeError("Not found")
        assert "error" in parse(get_product_details(asin="INVALID"))


class TestGetSalesRankings:
    def test_returns_rankings(self, mock_client):
        mock_client.get_catalog_item.return_value = {
            "summaries": [{"itemName": "Water Bottle 500ml"}],
            "salesRanks": [{"marketplaceId": "A1RKKUPIHCS9HS", "ranks": [
                {"title": "Kitchen & Dining", "rank": 5000, "link": "http://..."},
                {"title": "Reusable Water Bottles", "rank": 150, "link": "http://..."},
            ]}],
        }
        result = parse(get_sales_rankings(asin="B001"))
        assert len(result["rankings"]) == 2
        assert result["rankings"][0]["rank"] == 5000

    def test_empty_rankings(self, mock_client):
        mock_client.get_catalog_item.return_value = {"summaries": [{"itemName": "Producto"}], "salesRanks": []}
        assert parse(get_sales_rankings(asin="B001"))["rankings"] == []

    def test_error_handling(self, mock_client):
        mock_client.get_catalog_item.side_effect = RuntimeError("Not found")
        assert "error" in parse(get_sales_rankings(asin="INVALID"))
