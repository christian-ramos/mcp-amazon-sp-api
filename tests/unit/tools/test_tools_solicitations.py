"""Tests de tools MCP: Solicitations."""

from mcp_amazon_sp_api.server import check_review_eligibility, request_review
from .conftest import parse


class TestCheckReviewEligibility:
    def test_returns_actions(self, mock_client):
        mock_client.get_solicitation_actions.return_value = {
            "_links": {"actions": [{"name": "productReviewAndSellerFeedback"}]},
        }
        result = parse(check_review_eligibility(order_id="111"))
        assert result["orderId"] == "111"

    def test_error_handling(self, mock_client):
        mock_client.get_solicitation_actions.side_effect = RuntimeError("Fail")
        assert "error" in parse(check_review_eligibility(order_id="BAD"))


class TestRequestReview:
    def test_without_confirm_returns_plan(self, mock_client):
        result = parse(request_review(order_id="111"))
        assert result["confirmed"] is False
        assert result["plan"]["orderId"] == "111"
        assert "1 vez por pedido" in result["message"]
        mock_client.request_review.assert_not_called()

    def test_sends_solicitation_with_confirm(self, mock_client):
        mock_client.request_review.return_value = {}
        result = parse(request_review(order_id="111", confirm=True))
        assert result["orderId"] == "111"

    def test_error_handling(self, mock_client):
        mock_client.request_review.side_effect = RuntimeError("Fail")
        assert "error" in parse(request_review(order_id="BAD", confirm=True))
