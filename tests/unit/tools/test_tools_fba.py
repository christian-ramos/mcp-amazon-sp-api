"""Tests de tools MCP: FBA e Inventario."""

from mcp_amazon_sp_api.tools.fba_inventory import (
    get_fba_fees_report,
    get_fba_inventory,
    get_fba_returns,
    get_restock_suggestions,
)

from .conftest import parse


class TestGetFbaInventory:
    def test_returns_inventory(self, mock_client):
        mock_client.get_fba_inventory_report.return_value = [
            {"sku": "SKU-1", "qty": 10},
            {"sku": "SKU-2", "qty": 5},
        ]
        result = parse(get_fba_inventory())
        assert result["totalSkus"] == 2
        assert result["inventory"][0]["sku"] == "SKU-1"

    def test_limits_to_200(self, mock_client):
        mock_client.get_fba_inventory_report.return_value = [
            {"sku": f"SKU-{i}"} for i in range(250)
        ]
        result = parse(get_fba_inventory())
        assert len(result["inventory"]) == 200
        assert result["totalSkus"] == 250

    def test_error_handling(self, mock_client):
        mock_client.get_fba_inventory_report.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_fba_inventory())


class TestGetFbaReturns:
    def test_returns_with_reasons(self, mock_client):
        mock_client.get_fba_returns_report.return_value = [
            {"sku": "SKU-1", "reason": "DEFECTIVE", "qty": 1},
            {"sku": "SKU-2", "reason": "CUSTOMER_RETURN", "qty": 2},
        ]
        result = parse(get_fba_returns(days_back=14))
        assert result["totalReturns"] == 2
        assert "Últimos 14 días" in result["period"]

    def test_error_handling(self, mock_client):
        mock_client.get_fba_returns_report.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_fba_returns())


class TestGetFbaFeesReport:
    def test_returns_both_fee_types(self, mock_client):
        mock_client.get_fba_storage_fees.return_value = [
            {"sku": "SKU-1", "fee": "1.20"},
        ]
        mock_client.get_fba_longterm_storage_fees.return_value = [
            {"sku": "SKU-1", "fee": "3.50"},
        ]
        result = parse(get_fba_fees_report())
        assert result["storageFees"]["totalSkus"] == 1
        assert result["longtermStorageFees"]["totalSkus"] == 1

    def test_error_handling(self, mock_client):
        mock_client.get_fba_storage_fees.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_fba_fees_report())


class TestGetRestockSuggestions:
    def test_returns_recommendations(self, mock_client):
        mock_client.get_restock_recommendations.return_value = [
            {"sku": "SKU-1", "recommendedQty": 50},
        ]
        result = parse(get_restock_suggestions())
        assert result["totalSkus"] == 1
        assert result["recommendations"][0]["recommendedQty"] == 50

    def test_error_handling(self, mock_client):
        mock_client.get_restock_recommendations.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_restock_suggestions())
