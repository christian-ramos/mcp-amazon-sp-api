"""Tests de tools MCP: listings."""

import json

from mcp_amazon_sp_api.tools.listings import (
    get_listing_content,
    get_listing_issues,
    get_product_type_info,
    list_my_listings,
    update_listing_attribute,
    update_listing_batch,
)

from .conftest import parse


class TestGetListingContent:
    def test_extracts_attributes(self, mock_client):
        mock_client.get_listing_item.return_value = {
            "sku": "SKU-001",
            "summaries": [{"asin": "B001", "status": "BUYABLE", "productType": "WATER_BOTTLE"}],
            "attributes": {
                "item_name": [{"value": "Water Bottle 500ml Stainless Steel"}],
                "bullet_point": [{"value": "Insulated"}, {"value": "Leak-proof lid"}],
                "product_description": [{"value": "Best stainless steel water bottle"}],
                "generic_keyword": [{"value": "water bottle stainless steel insulated"}],
            },
            "issues": [], "offers": [],
        }
        result = parse(get_listing_content(sku="SKU-001"))
        assert result["title"] == "Water Bottle 500ml Stainless Steel"
        assert result["bulletPoints"] == ["Insulated", "Leak-proof lid"]
        assert result["description"] == "Best stainless steel water bottle"
        assert result["issueCount"] == 0

    def test_handles_empty_attributes(self, mock_client):
        mock_client.get_listing_item.return_value = {"sku": "SKU-001", "summaries": [], "attributes": {}, "issues": [], "offers": []}
        result = parse(get_listing_content(sku="SKU-001"))
        assert result["title"] is None
        assert result["bulletPoints"] == []

    def test_error_handling(self, mock_client):
        mock_client.get_listing_item.side_effect = RuntimeError("Not found")
        assert "error" in parse(get_listing_content(sku="INVALID"))


class TestListMyListings:
    def test_returns_listings(self, mock_client):
        mock_client.search_listings_items.return_value = [{
            "sku": "SKU-001",
            "summaries": [{"asin": "B001", "itemName": "Bottle A", "status": "BUYABLE", "productType": "WATER_BOTTLE"}],
            "issues": [{"severity": "WARNING", "code": "W1", "message": "msg"}],
        }]
        result = parse(list_my_listings())
        assert result[0]["sku"] == "SKU-001"
        assert result[0]["issueCount"] == 1

    def test_error_handling(self, mock_client):
        mock_client.search_listings_items.side_effect = RuntimeError("Error")
        assert "error" in parse(list_my_listings())


class TestGetListingIssues:
    def test_returns_issues(self, mock_client):
        mock_client.get_listing_item.return_value = {
            "issues": [
                {"severity": "ERROR", "code": "E1", "message": "Título demasiado largo", "attributeNames": ["item_name"]},
                {"severity": "WARNING", "code": "W1", "message": "Faltan keywords", "attributeNames": ["generic_keyword"]},
            ],
        }
        result = parse(get_listing_issues(sku="SKU-001"))
        assert result["issueCount"] == 2
        assert result["issues"][0]["severity"] == "ERROR"


class TestGetProductTypeInfo:
    def test_returns_definition(self, mock_client):
        mock_client.get_product_type_definition.return_value = {
            "productType": "WATER_BOTTLE",
            "schema": {"properties": {"attributes": {"properties": {"item_name": {"title": "Title"}, "bullet_point": {"title": "Bullets"}}, "required": ["item_name"]}}},
        }
        result = parse(get_product_type_info(product_type="WATER_BOTTLE"))
        assert result["totalAttributes"] == 2
        assert "item_name" in result["requiredAttributes"]

    def test_searches_by_keywords(self, mock_client):
        mock_client.search_product_types.return_value = [{"name": "WATER_BOTTLE", "displayName": "Water Bottle", "marketplaceIds": []}]
        result = parse(get_product_type_info(keywords="water bottle"))
        assert result[0]["name"] == "WATER_BOTTLE"


class TestUpdateListingAttribute:
    def test_without_confirm_returns_plan(self, mock_client):
        result = parse(update_listing_attribute(sku="SKU-001", product_type="WATER_BOTTLE", attribute_name="item_name", value="Nuevo título"))
        assert result["confirmed"] is False
        assert result["plan"]["attribute"] == "item_name"
        assert "confirm=True" in result["message"]

    def test_updates_single_attribute(self, mock_client):
        mock_client.patch_listing_item.return_value = {"sku": "SKU-001", "status": "ACCEPTED", "submissionId": "sub-123", "issues": []}
        result = parse(update_listing_attribute(sku="SKU-001", product_type="WATER_BOTTLE", attribute_name="item_name", value="Nuevo título", confirm=True))
        assert result["status"] == "ACCEPTED"

    def test_handles_json_array_for_bullets(self, mock_client):
        mock_client.patch_listing_item.return_value = {"status": "ACCEPTED", "issues": []}
        update_listing_attribute(sku="SKU-001", product_type="WATER_BOTTLE", attribute_name="bullet_point", value='["Bullet 1", "Bullet 2"]', confirm=True)
        assert len(mock_client.patch_listing_item.call_args[0][2][0]["value"]) == 2

    def test_error_handling(self, mock_client):
        mock_client.patch_listing_item.side_effect = RuntimeError("Invalid")
        assert "error" in parse(update_listing_attribute(sku="SKU-001", product_type="WATER_BOTTLE", attribute_name="item_name", value="test", confirm=True))


class TestUpdateListingBatch:
    def test_without_confirm_returns_plan(self, mock_client):
        updates = json.dumps({"item_name": "Nuevo título", "bullet_point": ["B1", "B2"]})
        result = parse(update_listing_batch(sku="SKU-001", product_type="WATER_BOTTLE", updates=updates))
        assert result["confirmed"] is False
        assert "item_name" in result["plan"]["attributesToUpdate"]

    def test_updates_multiple_attributes(self, mock_client):
        mock_client.patch_listing_item.return_value = {"sku": "SKU-001", "status": "ACCEPTED", "submissionId": "sub-456", "issues": []}
        updates = json.dumps({"item_name": "Nuevo título", "bullet_point": ["B1", "B2"], "product_description": "Desc"})
        result = parse(update_listing_batch(sku="SKU-001", product_type="WATER_BOTTLE", updates=updates, confirm=True))
        assert result["status"] == "ACCEPTED"
        assert set(result["attributesUpdated"]) == {"item_name", "bullet_point", "product_description"}

    def test_invalid_json_returns_error(self, mock_client):
        result = parse(update_listing_batch(sku="SKU-001", product_type="WATER_BOTTLE", updates="not json"))
        assert "JSON inválido" in result["error"]

    def test_error_handling(self, mock_client):
        mock_client.patch_listing_item.side_effect = RuntimeError("API error")
        assert "error" in parse(update_listing_batch(sku="SKU-001", product_type="WATER_BOTTLE", updates='{"item_name": "test"}', confirm=True))
