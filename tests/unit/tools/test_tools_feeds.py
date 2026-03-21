"""Tests de tools MCP: Feeds."""

from mcp_amazon_sp_api.tools.feeds import bulk_update_prices, check_feed
from .conftest import parse


class TestBulkUpdatePrices:
    def test_without_confirm_returns_plan(self, mock_client):
        result = parse(bulk_update_prices(
            updates='[{"sku": "SKU-1", "price": 14.99}, {"sku": "SKU-2", "price": 9.99}]'
        ))
        assert result["confirmed"] is False
        assert result["plan"]["totalSkus"] == 2
        mock_client.bulk_update_prices.assert_not_called()

    def test_submits_feed_with_confirm(self, mock_client):
        mock_client.bulk_update_prices.return_value = {
            "feedId": "FEED-1", "feedDocumentId": "DOC-1",
        }
        result = parse(bulk_update_prices(
            updates='[{"sku": "SKU-1", "price": 14.99}, {"sku": "SKU-2", "price": 9.99}]',
            confirm=True,
        ))
        assert result["feedId"] == "FEED-1"
        assert result["totalUpdates"] == 2

    def test_invalid_json(self, mock_client):
        result = parse(bulk_update_prices(updates="not json"))
        assert "error" in result

    def test_error_handling(self, mock_client):
        mock_client.bulk_update_prices.side_effect = RuntimeError("Fail")
        result = parse(bulk_update_prices(updates='[{"sku": "X", "price": 1}]', confirm=True))
        assert "error" in result


class TestCheckFeed:
    def test_done_with_result(self, mock_client):
        mock_client.get_feed_status.return_value = {
            "feedId": "FEED-1",
            "feedType": "POST_FLAT_FILE_PRICEANDQUANTITYONLY_UPDATE_DATA",
            "processingStatus": "DONE",
            "resultFeedDocumentId": "RESULT-DOC-1",
        }
        mock_client.get_feed_result.return_value = "sku\tstatus\nSKU-1\tSuccess"
        result = parse(check_feed(feed_id="FEED-1"))
        assert result["processingStatus"] == "DONE"
        assert "SKU-1" in result["result"]

    def test_in_progress(self, mock_client):
        mock_client.get_feed_status.return_value = {
            "feedId": "FEED-1",
            "processingStatus": "IN_PROGRESS",
            "resultFeedDocumentId": None,
        }
        result = parse(check_feed(feed_id="FEED-1"))
        assert "Espera" in result["nextStep"]

    def test_fatal(self, mock_client):
        mock_client.get_feed_status.return_value = {
            "feedId": "FEED-1",
            "processingStatus": "FATAL",
            "resultFeedDocumentId": None,
        }
        result = parse(check_feed(feed_id="FEED-1"))
        assert "falló" in result["nextStep"]

    def test_error_handling(self, mock_client):
        mock_client.get_feed_status.side_effect = RuntimeError("Not found")
        assert "error" in parse(check_feed(feed_id="BAD"))
