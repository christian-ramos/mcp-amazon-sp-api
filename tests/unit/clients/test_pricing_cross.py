"""Tests unitarios para CrossMarketplacePricingClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.config import EU_MARKETPLACES
from mcp_amazon_sp_api.sp_client import AmazonClient

from .conftest import make_api_error, make_response


class TestGetPricesAllMarketplaces:
    @patch.object(AmazonClient, "_listings_api")
    def test_returns_prices_for_specified_marketplaces(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_item.return_value = make_response(
            {
                "offers": [
                    {
                        "buyingPrice": {
                            "listingPrice": {"amount": "12.99", "currencyCode": "EUR"}
                        },
                        "fulfillmentChannel": "AFN",
                    }
                ],
                "status": "BUYABLE",
            }
        )
        result = client.get_prices_all_marketplaces("SKU-1", marketplaces=["ES", "DE"])
        assert len(result) == 2
        assert result[0]["marketplace"] == "ES"
        assert result[0]["price"] == "12.99"

    @patch.object(AmazonClient, "_listings_api")
    def test_handles_no_offers(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_item.return_value = make_response({"offers": []})
        result = client.get_prices_all_marketplaces("SKU-1", marketplaces=["DE"])
        assert result[0]["price"] is None
        assert result[0]["status"] == "NO_OFFER"

    @patch.object(AmazonClient, "_listings_api")
    def test_handles_api_error_gracefully(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_item.side_effect = make_api_error(404)
        result = client.get_prices_all_marketplaces("SKU-1", marketplaces=["FR"])
        assert "error" in result[0]
        assert result[0]["marketplace"] == "FR"

    def test_unsupported_marketplace(self, client):
        result = client.get_prices_all_marketplaces("SKU-1", marketplaces=["XX"])
        assert "error" in result[0]
        assert "no soportado" in result[0]["error"]

    @patch.object(AmazonClient, "_listings_api")
    def test_defaults_to_all_eu(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_item.return_value = make_response({"offers": []})
        result = client.get_prices_all_marketplaces("SKU-1")
        assert len(result) == len(EU_MARKETPLACES)


class TestUpdatePrice:
    @patch.object(AmazonClient, "_listings_api")
    def test_updates_price(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.patch_listings_item.return_value = make_response(
            {
                "sku": "SKU-1",
                "status": "ACCEPTED",
                "submissionId": "SUB-1",
            }
        )
        result = client.update_price("SKU-1", "WATER_BOTTLE", 14.99, "DE")
        assert result["status"] == "ACCEPTED"
        body = mock_api.patch_listings_item.call_args[1]["body"]
        assert body["productType"] == "WATER_BOTTLE"
        patches = body["patches"]
        assert patches[0]["path"] == "/attributes/purchasable_offer"
        value = patches[0]["value"][0]
        assert value["marketplace_id"] == EU_MARKETPLACES["DE"]["id"]
        assert value["our_price"][0]["schedule"][0]["value_with_tax"] == 14.99

    def test_raises_for_unsupported_marketplace(self, client):
        with pytest.raises(RuntimeError, match="no soportado"):
            client.update_price("SKU-1", "WATER_BOTTLE", 10.0, "XX")

    @patch.object(AmazonClient, "_listings_api")
    def test_raises_on_api_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.patch_listings_item.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.update_price("SKU-1", "WATER_BOTTLE", 10.0, "DE")


class TestSyncPrices:
    @patch.object(AmazonClient, "update_price")
    def test_syncs_to_multiple_marketplaces(self, mock_update, client):
        mock_update.return_value = {"status": "ACCEPTED", "issues": []}
        result = client.sync_prices("SKU-1", "WATER_BOTTLE", 12.99, ["DE", "FR", "IT"])
        assert len(result) == 3
        assert all(r["status"] == "ACCEPTED" for r in result)
        assert all(r["price"] == 12.99 for r in result)

    @patch.object(AmazonClient, "update_price")
    def test_applies_adjustment(self, mock_update, client):
        mock_update.return_value = {"status": "ACCEPTED", "issues": []}
        result = client.sync_prices(
            "SKU-1", "WATER_BOTTLE", 10.00, ["DE"], adjustment_pct=10.0
        )
        assert result[0]["price"] == 11.00
        mock_update.assert_called_once_with("SKU-1", "WATER_BOTTLE", 11.00, "DE")

    @patch.object(AmazonClient, "update_price")
    def test_negative_adjustment(self, mock_update, client):
        mock_update.return_value = {"status": "ACCEPTED", "issues": []}
        result = client.sync_prices(
            "SKU-1", "WATER_BOTTLE", 10.00, ["FR"], adjustment_pct=-5.0
        )
        assert result[0]["price"] == 9.50

    @patch.object(AmazonClient, "update_price")
    def test_handles_partial_failure(self, mock_update, client):
        mock_update.side_effect = [
            {"status": "ACCEPTED", "issues": []},
            RuntimeError("Error SP-API al actualizar precio en IT"),
        ]
        result = client.sync_prices("SKU-1", "WATER_BOTTLE", 12.99, ["DE", "IT"])
        assert result[0]["status"] == "ACCEPTED"
        assert "error" in result[1]
