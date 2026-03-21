"""Tests unitarios para FeedsClient."""

from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient
from .conftest import make_response, make_api_error


class TestSubmitFeed:
    @patch.object(AmazonClient, "_feeds_api")
    def test_returns_feed_and_doc_ids(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.submit_feed.return_value = [
            make_response({"feedDocumentId": "DOC-1", "url": "https://..."}),
            make_response({"feedId": "FEED-1"}),
        ]
        result = client.submit_feed("POST_FLAT_FILE_PRICEANDQUANTITYONLY_UPDATE_DATA", "sku\tprice\nSKU-1\t10.00")
        assert result["feedId"] == "FEED-1"
        assert result["feedDocumentId"] == "DOC-1"

    @patch.object(AmazonClient, "_feeds_api")
    def test_passes_feed_type_and_content(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.submit_feed.return_value = [
            make_response({"feedDocumentId": "DOC-1"}),
            make_response({"feedId": "FEED-1"}),
        ]
        client.submit_feed("MY_FEED_TYPE", "content here", "application/json")
        call_args = mock_api.submit_feed.call_args
        assert call_args[0][0] == "MY_FEED_TYPE"
        assert call_args[0][2] == "application/json"

    @patch.object(AmazonClient, "_feeds_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.submit_feed.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.submit_feed("TYPE", "content")


class TestGetFeedStatus:
    @patch.object(AmazonClient, "_feeds_api")
    def test_returns_status(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_feed.return_value = make_response({
            "feedId": "FEED-1",
            "feedType": "POST_FLAT_FILE_PRICEANDQUANTITYONLY_UPDATE_DATA",
            "processingStatus": "DONE",
            "resultFeedDocumentId": "RESULT-DOC-1",
        })
        status = client.get_feed_status("FEED-1")
        assert status["processingStatus"] == "DONE"
        assert status["resultFeedDocumentId"] == "RESULT-DOC-1"

    @patch.object(AmazonClient, "_feeds_api")
    def test_in_progress(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_feed.return_value = make_response({
            "feedId": "FEED-1",
            "processingStatus": "IN_PROGRESS",
        })
        status = client.get_feed_status("FEED-1")
        assert status["processingStatus"] == "IN_PROGRESS"
        assert status["resultFeedDocumentId"] is None

    @patch.object(AmazonClient, "_feeds_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_feed.side_effect = make_api_error(404)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_feed_status("BAD-FEED")


class TestGetFeedResult:
    @patch.object(AmazonClient, "_feeds_api")
    def test_returns_content(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_feed_document.return_value = "sku\tstatus\nSKU-1\tSuccess\n"
        result = client.get_feed_result("RESULT-DOC-1")
        assert "SKU-1" in result

    @patch.object(AmazonClient, "_feeds_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_feed_document.side_effect = make_api_error(404)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_feed_result("BAD-DOC")


class TestBulkUpdatePrices:
    @patch.object(AmazonClient, "submit_feed")
    def test_builds_json_and_submits(self, mock_submit, client):
        mock_submit.return_value = {"feedId": "FEED-1", "feedDocumentId": "DOC-1"}
        updates = [
            {"sku": "SKU-1", "price": 14.99},
            {"sku": "SKU-2", "price": 9.99},
        ]
        result = client.bulk_update_prices(updates)
        assert result["feedId"] == "FEED-1"
        assert mock_submit.call_args[0][0] == "JSON_LISTINGS_FEED"
        import json
        body = json.loads(mock_submit.call_args[0][1])
        assert body["header"]["version"] == "2.0"
        assert len(body["messages"]) == 2
        assert body["messages"][0]["sku"] == "SKU-1"
        assert body["messages"][0]["operationType"] == "PATCH"
        assert body["messages"][0]["patches"][0]["path"] == "/attributes/purchasable_offer"


class TestBulkUpdateInventory:
    @patch.object(AmazonClient, "submit_feed")
    def test_builds_json_and_submits(self, mock_submit, client):
        mock_submit.return_value = {"feedId": "FEED-1", "feedDocumentId": "DOC-1"}
        updates = [
            {"sku": "SKU-1", "quantity": 50},
            {"sku": "SKU-2", "quantity": 0},
        ]
        result = client.bulk_update_inventory(updates)
        assert result["feedId"] == "FEED-1"
        assert mock_submit.call_args[0][0] == "JSON_LISTINGS_FEED"
        import json
        body = json.loads(mock_submit.call_args[0][1])
        assert len(body["messages"]) == 2
        assert body["messages"][0]["patches"][0]["path"] == "/attributes/fulfillment_availability"
        assert body["messages"][1]["patches"][0]["value"][0]["quantity"] == 0
