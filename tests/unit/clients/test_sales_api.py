"""Tests unitarios para SalesApiClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient
from .conftest import make_response, make_api_error


class TestGetOrderMetrics:
    @patch.object(AmazonClient, "_sales_api")
    def test_returns_metrics(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_order_metrics.return_value = make_response([
            {"interval": "2025-01-01--2025-01-02", "unitCount": 5, "orderItemCount": 5, "orderCount": 3},
            {"interval": "2025-01-02--2025-01-03", "unitCount": 8, "orderItemCount": 8, "orderCount": 4},
        ])
        result = client.get_order_metrics(days_back=7)
        assert len(result) == 2
        assert result[0]["unitCount"] == 5

    @patch.object(AmazonClient, "_sales_api")
    def test_passes_granularity(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_order_metrics.return_value = make_response([])
        client.get_order_metrics(days_back=30, granularity="Week")
        call_kwargs = mock_api.get_order_metrics.call_args[1]
        assert "granularity" in call_kwargs

    @patch.object(AmazonClient, "_sales_api")
    def test_handles_single_payload(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_order_metrics.return_value = make_response(
            {"interval": "2025-01-01--2025-01-31", "unitCount": 100}
        )
        result = client.get_order_metrics(days_back=30, granularity="Month")
        assert len(result) == 1

    @patch.object(AmazonClient, "_sales_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_order_metrics.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_order_metrics()
