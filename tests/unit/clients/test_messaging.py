"""Tests unitarios para MessagingClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient

from .conftest import make_api_error, make_response


class TestGetMessagingActions:
    @patch.object(AmazonClient, "_messaging_api")
    def test_returns_actions(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_messaging_actions_for_order.return_value = make_response({
            "_links": {"actions": [{"name": "confirmDeliveryDetails"}]},
        })
        result = client.get_messaging_actions("111-222-333")
        assert "_links" in result

    @patch.object(AmazonClient, "_messaging_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_messaging_actions_for_order.side_effect = make_api_error(403)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_messaging_actions("BAD")


class TestSendMessage:
    @patch.object(AmazonClient, "_messaging_api")
    def test_sends_confirm_delivery(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.create_confirm_delivery_details.return_value = make_response({})
        result = client.send_message("111", "confirm_delivery", {"text": "Delivered"})
        assert isinstance(result, dict)
        mock_api.create_confirm_delivery_details.assert_called_once()

    @patch.object(AmazonClient, "_messaging_api")
    def test_sends_unexpected_problem(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.create_unexpected_problem.return_value = make_response({})
        client.send_message("111", "unexpected_problem", {"text": "Issue"})
        mock_api.create_unexpected_problem.assert_called_once()

    def test_raises_for_invalid_type(self, client):
        with pytest.raises(RuntimeError, match="no soportado"):
            client.send_message("111", "invalid_type", {})

    @patch.object(AmazonClient, "_messaging_api")
    def test_raises_on_api_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.create_confirm_delivery_details.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.send_message("111", "confirm_delivery", {})
