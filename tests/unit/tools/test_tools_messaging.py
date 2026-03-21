"""Tests de tools MCP: Messaging."""

from mcp_amazon_sp_api.server import get_messaging_options, send_buyer_message
from .conftest import parse


class TestGetMessagingOptions:
    def test_returns_actions(self, mock_client):
        mock_client.get_messaging_actions.return_value = {
            "_links": {"actions": [{"name": "confirmDelivery"}]},
        }
        result = parse(get_messaging_options(order_id="111"))
        assert result["orderId"] == "111"
        assert "actions" in result

    def test_error_handling(self, mock_client):
        mock_client.get_messaging_actions.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_messaging_options(order_id="BAD"))


class TestSendBuyerMessage:
    def test_without_confirm_returns_plan(self, mock_client):
        result = parse(send_buyer_message(
            order_id="111", message_type="confirm_delivery",
            body='{"text": "Your order has been delivered"}',
        ))
        assert result["confirmed"] is False
        assert result["plan"]["messageType"] == "confirm_delivery"
        mock_client.send_message.assert_not_called()

    def test_sends_message_with_confirm(self, mock_client):
        mock_client.send_message.return_value = {}
        result = parse(send_buyer_message(
            order_id="111", message_type="confirm_delivery",
            body='{"text": "Your order has been delivered"}', confirm=True,
        ))
        assert result["orderId"] == "111"
        assert result["messageType"] == "confirm_delivery"

    def test_invalid_json(self, mock_client):
        result = parse(send_buyer_message(
            order_id="111", message_type="confirm_delivery", body="not json",
        ))
        assert "error" in result

    def test_error_handling(self, mock_client):
        mock_client.send_message.side_effect = RuntimeError("Fail")
        result = parse(send_buyer_message(
            order_id="111", message_type="confirm_delivery", body="{}", confirm=True,
        ))
        assert "error" in result
