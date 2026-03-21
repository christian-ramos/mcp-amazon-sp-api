"""Tests de tools MCP: Inventario en tiempo real."""

from mcp_amazon_sp_api.server import get_inventory
from .conftest import parse


class TestGetInventory:
    def test_returns_all_inventory(self, mock_client):
        mock_client.get_inventory_summary.return_value = [
            {"sellerSku": "SKU-1", "totalQuantity": 10},
            {"sellerSku": "SKU-2", "totalQuantity": 5},
        ]
        result = parse(get_inventory())
        assert result["totalSkus"] == 2
        assert result["inventory"][0]["sellerSku"] == "SKU-1"
        mock_client.get_inventory_summary.assert_called_once_with(skus=None)

    def test_filters_by_single_sku(self, mock_client):
        mock_client.get_inventory_summary.return_value = [
            {"sellerSku": "SKU-1", "totalQuantity": 10},
        ]
        parse(get_inventory(sku="SKU-1"))
        mock_client.get_inventory_summary.assert_called_once_with(skus=["SKU-1"])

    def test_filters_by_multiple_skus(self, mock_client):
        mock_client.get_inventory_summary.return_value = []
        parse(get_inventory(sku="SKU-1, SKU-2, SKU-3"))
        mock_client.get_inventory_summary.assert_called_once_with(
            skus=["SKU-1", "SKU-2", "SKU-3"]
        )

    def test_limits_to_200(self, mock_client):
        mock_client.get_inventory_summary.return_value = [
            {"sellerSku": f"SKU-{i}"} for i in range(250)
        ]
        result = parse(get_inventory())
        assert len(result["inventory"]) == 200
        assert result["totalSkus"] == 250

    def test_error_handling(self, mock_client):
        mock_client.get_inventory_summary.side_effect = RuntimeError("API down")
        result = parse(get_inventory())
        assert "error" in result

    def test_empty_sku_string_returns_all(self, mock_client):
        mock_client.get_inventory_summary.return_value = []
        parse(get_inventory(sku=""))
        mock_client.get_inventory_summary.assert_called_once_with(skus=None)
