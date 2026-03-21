"""Tests de tools MCP: fees (estimate_fees)."""

from mcp_amazon_sp_api.tools.analysis import estimate_fees
from .conftest import parse


class TestEstimateFees:
    def test_returns_fee_breakdown(self, mock_client):
        mock_client.get_fees_estimate.return_value = {
            "FeesEstimateResult": {"FeesEstimate": {
                "TotalFeesEstimate": {"Amount": "5.50", "CurrencyCode": "EUR"},
                "FeeDetailList": [
                    {"FeeType": "ReferralFee", "FeeAmount": {"Amount": "3.00"}},
                    {"FeeType": "FBAFees", "FeeAmount": {"Amount": "2.50"}},
                ],
            }}
        }
        result = parse(estimate_fees(asin="B001", price=19.99))
        assert result["totalFees"] == "5.50 EUR"
        assert result["netRevenue"] == "14.49 EUR"
        assert "ReferralFee" in result["feeBreakdown"]

    def test_passes_is_fba(self, mock_client):
        mock_client.get_fees_estimate.return_value = {
            "FeesEstimateResult": {"FeesEstimate": {"TotalFeesEstimate": {"Amount": "3.00", "CurrencyCode": "EUR"}, "FeeDetailList": []}}
        }
        estimate_fees(asin="B001", price=10.0, is_fba=False)
        mock_client.get_fees_estimate.assert_called_once_with(asin="B001", price=10.0, is_fba=False)

    def test_error_handling(self, mock_client):
        mock_client.get_fees_estimate.side_effect = RuntimeError("Bad request")
        assert "error" in parse(estimate_fees(asin="B001", price=10.0))
