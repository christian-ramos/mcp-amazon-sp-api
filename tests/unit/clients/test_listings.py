"""Tests unitarios para ListingsClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient
from .conftest import make_response, make_api_error


class TestGetListingItem:
    @patch.object(AmazonClient, "_listings_api")
    def test_returns_listing(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_item.return_value = make_response({
            "sku": "SKU-001",
            "summaries": [{"asin": "B001", "status": "BUYABLE"}],
            "attributes": {
                "item_name": [{"value": "Water Bottle 16"}],
                "bullet_point": [{"value": "bullet1"}, {"value": "bullet2"}],
            },
            "issues": [],
        })

        result = client.get_listing_item("SKU-001")
        assert result["sku"] == "SKU-001"
        assert result["attributes"]["item_name"][0]["value"] == "Water Bottle 16"
        mock_api.get_listings_item.assert_called_once_with(
            "A1SELLER", "SKU-001",
            marketplaceIds=["A1RKKUPIHCS9HS"],
            includedData=["summaries", "attributes", "issues", "offers", "fulfillmentAvailability"],
        )

    @patch.object(AmazonClient, "_listings_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_item.side_effect = make_api_error(404)

        with pytest.raises(RuntimeError, match="listing SKU-001"):
            client.get_listing_item("SKU-001")


class TestSearchListingsItems:
    @patch.object(AmazonClient, "_listings_api")
    def test_returns_list(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.search_listings_items.return_value = make_response({
            "listingsItems": [
                {"sku": "SKU-001", "summaries": [{"asin": "B001"}]},
                {"sku": "SKU-002", "summaries": [{"asin": "B002"}]},
            ]
        })

        items = client.search_listings_items(page_size=10)
        assert len(items) == 2

    @patch.object(AmazonClient, "_listings_api")
    def test_passes_filters(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.search_listings_items.return_value = make_response({"listingsItems": []})

        client.search_listings_items(with_status="BUYABLE", with_issue_severity="ERROR")
        call_kwargs = mock_api.search_listings_items.call_args[1]
        assert call_kwargs["withStatus"] == "BUYABLE"
        assert call_kwargs["withIssueSeverity"] == "ERROR"

    @patch.object(AmazonClient, "_listings_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.search_listings_items.side_effect = make_api_error(500)

        with pytest.raises(RuntimeError, match="buscar listings"):
            client.search_listings_items()


class TestPatchListingItem:
    @patch.object(AmazonClient, "_listings_api")
    def test_sends_patches(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.patch_listings_item.return_value = make_response({
            "sku": "SKU-001",
            "status": "ACCEPTED",
            "submissionId": "sub-123",
            "issues": [],
        })

        patches = [{
            "op": "replace",
            "path": "/attributes/item_name",
            "value": [{"value": "Nuevo título", "language_tag": "es_ES", "marketplace_id": "A1RKKUPIHCS9HS"}],
        }]
        result = client.patch_listing_item("SKU-001", "WATER_BOTTLE", patches)
        assert result["status"] == "ACCEPTED"

        call_kwargs = mock_api.patch_listings_item.call_args[1]
        assert call_kwargs["body"]["productType"] == "WATER_BOTTLE"
        assert len(call_kwargs["body"]["patches"]) == 1

    @patch.object(AmazonClient, "_listings_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.patch_listings_item.side_effect = make_api_error(400)

        with pytest.raises(RuntimeError, match="actualizar listing SKU-001"):
            client.patch_listing_item("SKU-001", "WATER_BOTTLE", [])


class TestGetProductTypeDefinition:
    @patch.object(AmazonClient, "_product_type_definitions_api")
    def test_returns_definition(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_definitions_product_type.return_value = make_response({
            "productType": "WATER_BOTTLE",
            "schema": {"properties": {"attributes": {"properties": {"item_name": {}}}}},
        })

        result = client.get_product_type_definition("WATER_BOTTLE")
        assert result["productType"] == "WATER_BOTTLE"

    @patch.object(AmazonClient, "_product_type_definitions_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_definitions_product_type.side_effect = make_api_error(404)

        with pytest.raises(RuntimeError, match="definición de INVALID"):
            client.get_product_type_definition("INVALID")


class TestSearchProductTypes:
    @patch.object(AmazonClient, "_product_type_definitions_api")
    def test_returns_types(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.search_definitions_product_types.return_value = make_response({
            "productTypes": [
                {"name": "WATER_BOTTLE", "displayName": "Water Bottle"},
            ]
        })

        result = client.search_product_types(keywords="water bottle")
        assert len(result) == 1
        assert result[0]["name"] == "WATER_BOTTLE"

    @patch.object(AmazonClient, "_product_type_definitions_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.search_definitions_product_types.side_effect = make_api_error(500)

        with pytest.raises(RuntimeError, match="buscar product types"):
            client.search_product_types(keywords="test")
