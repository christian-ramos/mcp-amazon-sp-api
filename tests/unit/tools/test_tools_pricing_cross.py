"""Tests de tools MCP: Precios cross-marketplace."""

from mcp_amazon_sp_api.tools.pricing_cross import (
    get_cross_marketplace_prices,
    sync_marketplace_prices,
    update_marketplace_price,
)

from .conftest import parse


class TestGetCrossMarketplacePrices:
    def test_returns_prices(self, mock_client):
        mock_client.get_prices_all_marketplaces.return_value = [
            {"marketplace": "ES", "price": "12.99", "currency": "EUR"},
            {"marketplace": "DE", "price": "13.99", "currency": "EUR"},
        ]
        result = parse(get_cross_marketplace_prices(sku="SKU-1", marketplaces="ES,DE"))
        assert result["sku"] == "SKU-1"
        assert len(result["prices"]) == 2

    def test_all_marketplaces_when_empty(self, mock_client):
        mock_client.get_prices_all_marketplaces.return_value = []
        parse(get_cross_marketplace_prices(sku="SKU-1"))
        mock_client.get_prices_all_marketplaces.assert_called_once_with(
            "SKU-1", marketplaces=None
        )

    def test_error_handling(self, mock_client):
        mock_client.get_prices_all_marketplaces.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_cross_marketplace_prices(sku="SKU-1"))


class TestUpdateMarketplacePrice:
    def test_without_confirm_returns_plan(self, mock_client):
        result = parse(update_marketplace_price(
            sku="SKU-1", product_type="PHONE_CASE", price=14.99, marketplace="DE",
        ))
        assert result["confirmed"] is False
        assert "14.99" in result["plan"]["newPrice"]
        assert "confirm=True" in result["message"]

    def test_updates_price_with_confirm(self, mock_client):
        mock_client.update_price.return_value = {
            "status": "ACCEPTED", "submissionId": "SUB-1", "issues": [],
        }
        result = parse(update_marketplace_price(
            sku="SKU-1", product_type="PHONE_CASE", price=14.99, marketplace="DE", confirm=True,
        ))
        assert result["status"] == "ACCEPTED"
        assert result["price"] == 14.99

    def test_error_handling(self, mock_client):
        mock_client.update_price.side_effect = RuntimeError("Unsupported")
        assert "error" in parse(update_marketplace_price(
            sku="SKU-1", product_type="PHONE_CASE", price=10.0, marketplace="XX", confirm=True,
        ))


class TestSyncMarketplacePrices:
    def test_without_confirm_returns_plan(self, mock_client):
        result = parse(sync_marketplace_prices(
            sku="SKU-1", product_type="PHONE_CASE", base_price=12.99, targets="DE,FR",
        ))
        assert result["confirmed"] is False
        assert result["plan"]["adjustedPrice"] == 12.99
        assert "DE" in result["plan"]["targetMarketplaces"]

    def test_syncs_prices_with_confirm(self, mock_client):
        mock_client.sync_prices.return_value = [
            {"marketplace": "DE", "price": 12.99, "status": "ACCEPTED", "issues": []},
            {"marketplace": "FR", "price": 12.99, "status": "ACCEPTED", "issues": []},
        ]
        result = parse(sync_marketplace_prices(
            sku="SKU-1", product_type="PHONE_CASE", base_price=12.99, targets="DE,FR", confirm=True,
        ))
        assert result["basePrice"] == 12.99
        assert len(result["results"]) == 2

    def test_with_adjustment(self, mock_client):
        mock_client.sync_prices.return_value = [
            {"marketplace": "DE", "price": 11.0, "status": "ACCEPTED", "issues": []},
        ]
        result = parse(sync_marketplace_prices(
            sku="SKU-1", product_type="PHONE_CASE", base_price=10.0,
            targets="DE", adjustment_pct=10.0, confirm=True,
        ))
        assert result["adjustedPrice"] == 11.0

    def test_error_handling(self, mock_client):
        mock_client.sync_prices.side_effect = RuntimeError("Fail")
        assert "error" in parse(sync_marketplace_prices(
            sku="SKU-1", product_type="PHONE_CASE", base_price=10.0, targets="DE", confirm=True,
        ))
