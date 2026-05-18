"""Tests unitarios para SolicitationsClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient

from .conftest import make_api_error, make_response


class TestGetSolicitationActions:
    @patch.object(AmazonClient, "_solicitations_api")
    def test_returns_actions(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_solicitation_actions_for_order.return_value = make_response({
            "_links": {"actions": [{"name": "productReviewAndSellerFeedback"}]},
        })
        result = client.get_solicitation_actions("111-222-333")
        assert "_links" in result

    @patch.object(AmazonClient, "_solicitations_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_solicitation_actions_for_order.side_effect = make_api_error(403)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_solicitation_actions("BAD")


class TestRequestReview:
    @patch.object(AmazonClient, "_solicitations_api")
    def test_sends_solicitation(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.create_product_review_and_seller_feedback_solicitation.return_value = make_response({})
        result = client.request_review("111-222-333")
        assert isinstance(result, dict)

    @patch.object(AmazonClient, "_solicitations_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.create_product_review_and_seller_feedback_solicitation.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.request_review("BAD")
