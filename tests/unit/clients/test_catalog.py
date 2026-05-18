"""Tests unitarios para CatalogClient."""

from unittest.mock import MagicMock, patch

from mcp_amazon_sp_api.sp_client import AmazonClient

from .conftest import make_response


class TestGetCatalogItem:
    @patch.object(AmazonClient, "_catalog_api")
    def test_returns_payload(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_catalog_item.return_value = make_response({
            "summaries": [{"itemName": "Water Bottle 500ml"}], "relationships": [],
        })
        result = client.get_catalog_item("B001")
        assert result["summaries"][0]["itemName"] == "Water Bottle 500ml"

    @patch.object(AmazonClient, "_catalog_api")
    def test_includes_all_data_fields(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_catalog_item.return_value = make_response({})
        client.get_catalog_item("B001")
        included = mock_api.get_catalog_item.call_args[1]["includedData"]
        assert "summaries" in included
        assert "images" in included
        assert "salesRanks" in included


class TestSearchCatalogItems:
    @patch.object(AmazonClient, "_catalog_api")
    def test_search_by_keywords(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.search_catalog_items.return_value = make_response({"items": [{"asin": "B001"}, {"asin": "B002"}]})
        assert len(client.search_catalog_items(keywords="water bottle")) == 2

    @patch.object(AmazonClient, "_catalog_api")
    def test_search_by_identifiers(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.search_catalog_items.return_value = make_response({"items": [{"asin": "B001"}]})
        client.search_catalog_items(identifiers=["B001"])
        kwargs = mock_api.search_catalog_items.call_args[1]
        assert kwargs["identifiers"] == ["B001"]
        assert kwargs["identifiersType"] == "ASIN"

    @patch.object(AmazonClient, "_catalog_api")
    def test_empty_result(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.search_catalog_items.return_value = make_response({"items": []})
        assert client.search_catalog_items(keywords="nonexistent") == []
