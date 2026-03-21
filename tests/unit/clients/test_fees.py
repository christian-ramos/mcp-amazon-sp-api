"""Tests unitarios para FeesClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient
from .conftest import make_response, make_api_error


class TestGetFeesEstimate:
    @patch.object(AmazonClient, "_product_fees_api")
    def test_returns_fees(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_product_fees_estimate_for_asin.return_value = make_response({
            "FeesEstimateResult": {"FeesEstimate": {"TotalFeesEstimate": {"Amount": "5.50", "CurrencyCode": "EUR"}, "FeeDetailList": []}}
        })
        result = client.get_fees_estimate(asin="B001", price=19.99)
        assert "FeesEstimateResult" in result

    @patch.object(AmazonClient, "_product_fees_api")
    def test_passes_currency_and_fba(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_product_fees_estimate_for_asin.return_value = make_response({})
        client.get_fees_estimate(asin="B001", price=10.0, is_fba=False)
        assert mock_api.get_product_fees_estimate_for_asin.call_args[1]["is_fba"] is False

    @patch.object(AmazonClient, "_product_fees_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_product_fees_estimate_for_asin.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="fees de B001"):
            client.get_fees_estimate(asin="B001", price=10.0)


class TestGetMyFeesEstimates:
    @patch.object(AmazonClient, "_product_fees_api")
    def test_returns_list(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_my_fees_estimates.return_value = make_response([{"FeesEstimateResult": {"Status": "Success"}}])
        result = client.get_my_fees_estimates([{"IdType": "ASIN", "IdValue": "B001"}])
        assert isinstance(result, list)

    @patch.object(AmazonClient, "_product_fees_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_my_fees_estimates.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="fees en batch"):
            client.get_my_fees_estimates([])
