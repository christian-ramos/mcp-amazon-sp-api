"""Tests unitarios para InventoryClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient

from .conftest import make_api_error, make_response


class TestGetInventorySummary:
    @patch.object(AmazonClient, "_inventories_api")
    def test_returns_summaries(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_inventory_summary_marketplace.return_value = make_response({
            "inventorySummaries": [
                {"sellerSku": "SKU-1", "fnSku": "FN-1", "totalQuantity": 10},
                {"sellerSku": "SKU-2", "fnSku": "FN-2", "totalQuantity": 5},
            ],
            "nextToken": None,
        })
        result = client.get_inventory_summary()
        assert len(result) == 2
        assert result[0]["sellerSku"] == "SKU-1"

    @patch.object(AmazonClient, "_inventories_api")
    def test_filters_by_skus(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_inventory_summary_marketplace.return_value = make_response({
            "inventorySummaries": [{"sellerSku": "SKU-1", "totalQuantity": 10}],
            "nextToken": None,
        })
        client.get_inventory_summary(skus=["SKU-1", "SKU-2"])
        kwargs = mock_api.get_inventory_summary_marketplace.call_args[1]
        assert kwargs["sellerSkus"] == "SKU-1,SKU-2"

    @patch.object(AmazonClient, "_inventories_api")
    def test_filters_by_start_date(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_inventory_summary_marketplace.return_value = make_response({
            "inventorySummaries": [],
            "nextToken": None,
        })
        client.get_inventory_summary(start_date_time="2025-01-01T00:00:00Z")
        kwargs = mock_api.get_inventory_summary_marketplace.call_args[1]
        assert kwargs["startDateTime"] == "2025-01-01T00:00:00Z"

    @patch.object(AmazonClient, "_inventories_api")
    def test_paginates(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_inventory_summary_marketplace.side_effect = [
            make_response({
                "inventorySummaries": [{"sellerSku": "SKU-1"}],
                "nextToken": "page2",
            }),
            make_response({
                "inventorySummaries": [{"sellerSku": "SKU-2"}],
                "nextToken": None,
            }),
        ]
        result = client.get_inventory_summary()
        assert len(result) == 2
        assert mock_api.get_inventory_summary_marketplace.call_count == 2

    @patch.object(AmazonClient, "_inventories_api")
    def test_pagination_uses_next_token(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_inventory_summary_marketplace.side_effect = [
            make_response({
                "inventorySummaries": [{"sellerSku": "SKU-1"}],
                "nextToken": "token123",
            }),
            make_response({
                "inventorySummaries": [{"sellerSku": "SKU-2"}],
                "nextToken": None,
            }),
        ]
        client.get_inventory_summary(skus=["SKU-1"])
        second_call_kwargs = mock_api.get_inventory_summary_marketplace.call_args_list[1][1]
        assert second_call_kwargs["nextToken"] == "token123"
        assert "sellerSkus" not in second_call_kwargs

    @patch.object(AmazonClient, "_inventories_api")
    def test_raises_runtime_error_on_api_failure(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_inventory_summary_marketplace.side_effect = make_api_error(403)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_inventory_summary()

    @patch.object(AmazonClient, "_inventories_api")
    def test_empty_result(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_inventory_summary_marketplace.return_value = make_response({
            "inventorySummaries": [],
            "nextToken": None,
        })
        assert client.get_inventory_summary() == []
