"""Tests unitarios para PricingClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient
from .conftest import make_response, make_api_error


class TestGetCompetitivePricing:
    @patch.object(AmazonClient, "_products_api")
    def test_returns_pricing_list(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_competitive_pricing_for_asins.return_value = make_response([
            {"ASIN": "B001", "Product": {"CompetitivePricing": {}}},
            {"ASIN": "B002", "Product": {"CompetitivePricing": {}}},
        ])
        result = client.get_competitive_pricing(["B001", "B002"])
        assert len(result) == 2
        assert result[0]["ASIN"] == "B001"

    @patch.object(AmazonClient, "_products_api")
    def test_passes_asin_list(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_competitive_pricing_for_asins.return_value = make_response([])
        client.get_competitive_pricing(["B001", "B002"])
        mock_api.get_competitive_pricing_for_asins.assert_called_once_with(["B001", "B002"])

    @patch.object(AmazonClient, "_products_api")
    def test_handles_single_payload(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_competitive_pricing_for_asins.return_value = make_response(
            {"ASIN": "B001", "Product": {}}
        )
        result = client.get_competitive_pricing(["B001"])
        assert len(result) == 1

    @patch.object(AmazonClient, "_products_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_competitive_pricing_for_asins.side_effect = make_api_error(403)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_competitive_pricing(["B001"])


class TestGetItemOffers:
    @patch.object(AmazonClient, "_products_api")
    def test_returns_offers(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_item_offers.return_value = make_response({
            "Summary": {"TotalOfferCount": 5},
            "Offers": [{"SellerId": "A1", "ListingPrice": {"Amount": "10.00"}}],
        })
        result = client.get_item_offers("B001")
        assert result["Summary"]["TotalOfferCount"] == 5

    @patch.object(AmazonClient, "_products_api")
    def test_passes_condition(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_item_offers.return_value = make_response({})
        client.get_item_offers("B001", item_condition="Used")
        mock_api.get_item_offers.assert_called_once_with("B001", "Used")

    @patch.object(AmazonClient, "_products_api")
    def test_default_condition_new(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_item_offers.return_value = make_response({})
        client.get_item_offers("B001")
        mock_api.get_item_offers.assert_called_once_with("B001", "New")

    @patch.object(AmazonClient, "_products_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_item_offers.side_effect = make_api_error(500)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_item_offers("B001")


class TestGetProductPricing:
    @patch.object(AmazonClient, "_products_api")
    def test_returns_pricing(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_product_pricing_for_asins.return_value = make_response([
            {"ASIN": "B001", "Product": {"Offers": []}},
        ])
        result = client.get_product_pricing(["B001"])
        assert len(result) == 1

    @patch.object(AmazonClient, "_products_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_product_pricing_for_asins.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_product_pricing(["B001"])
