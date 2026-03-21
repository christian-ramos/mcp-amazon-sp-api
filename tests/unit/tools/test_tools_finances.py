"""Tests de tools MCP: finances (returns_summary, order_finances, profitability_report)."""

from mcp_amazon_sp_api.tools.analysis import get_order_finances, get_profitability_report, get_returns_summary
from .conftest import parse


class TestGetReturnsSummary:
    def test_aggregates_refunds(self, mock_client):
        mock_client.get_financial_events.return_value = {
            "RefundEventList": [
                {"ShipmentItemList": [{"SellerSKU": "SKU-001", "QuantityShipped": 1, "ItemChargeList": [{"ChargeType": "Principal", "ChargeAmount": {"Amount": "-19.99", "CurrencyCode": "EUR"}}]}]},
                {"ShipmentItemList": [{"SellerSKU": "SKU-001", "QuantityShipped": 1, "ItemChargeList": [{"ChargeType": "Principal", "ChargeAmount": {"Amount": "-9.99", "CurrencyCode": "EUR"}}]}]},
            ],
        }
        result = parse(get_returns_summary(days_back=30))
        assert result["totalRefunds"] == 2
        assert result["totalRefundAmount"] == "29.98 EUR"
        assert result["topRefundedProducts"][0]["count"] == 2

    def test_empty_refunds(self, mock_client):
        mock_client.get_financial_events.return_value = {"RefundEventList": []}
        result = parse(get_returns_summary(days_back=7))
        assert result["totalRefunds"] == 0

    def test_error_handling(self, mock_client):
        mock_client.get_financial_events.side_effect = RuntimeError("API error")
        assert "error" in parse(get_returns_summary(days_back=7))


class TestGetOrderFinances:
    def test_calculates_breakdown(self, mock_client):
        mock_client.get_financial_events_for_order.return_value = {
            "ShipmentEventList": [{"ShipmentItemList": [{
                "SellerSKU": "SKU-001", "QuantityShipped": 1,
                "ItemChargeList": [
                    {"ChargeType": "Principal", "ChargeAmount": {"Amount": "19.99", "CurrencyCode": "EUR"}},
                    {"ChargeType": "Tax", "ChargeAmount": {"Amount": "4.20", "CurrencyCode": "EUR"}},
                ],
                "ItemFeeList": [
                    {"FeeType": "Commission", "FeeAmount": {"Amount": "-3.00", "CurrencyCode": "EUR"}},
                    {"FeeType": "FBAPerUnitFulfillmentFee", "FeeAmount": {"Amount": "-2.50", "CurrencyCode": "EUR"}},
                ],
            }]}],
            "RefundEventList": [],
        }
        result = parse(get_order_finances(order_id="111-222-333"))
        assert result["totalRevenue"] == "24.19 EUR"
        assert result["totalFees"] == "5.50 EUR"
        assert result["items"][0]["sku"] == "SKU-001"

    def test_includes_refunds(self, mock_client):
        mock_client.get_financial_events_for_order.return_value = {
            "ShipmentEventList": [{"ShipmentItemList": [{"SellerSKU": "SKU-001", "QuantityShipped": 1, "ItemChargeList": [{"ChargeType": "Principal", "ChargeAmount": {"Amount": "19.99", "CurrencyCode": "EUR"}}], "ItemFeeList": []}]}],
            "RefundEventList": [{"ShipmentItemList": [{"SellerSKU": "SKU-001", "ItemChargeList": [{"ChargeType": "Principal", "ChargeAmount": {"Amount": "-19.99", "CurrencyCode": "EUR"}}]}]}],
        }
        assert parse(get_order_finances(order_id="111"))["totalRefunded"] == "19.99 EUR"

    def test_error_handling(self, mock_client):
        mock_client.get_financial_events_for_order.side_effect = RuntimeError("Not found")
        assert "error" in parse(get_order_finances(order_id="INVALID"))


class TestGetProfitabilityReport:
    def test_aggregates_by_sku(self, mock_client):
        mock_client.get_orders.return_value = [{"AmazonOrderId": "111"}, {"AmazonOrderId": "222"}]
        mock_client.get_financial_events_for_order.side_effect = [
            {"ShipmentEventList": [{"ShipmentItemList": [{"SellerSKU": "SKU-001", "QuantityShipped": 1, "ItemChargeList": [{"ChargeType": "Principal", "ChargeAmount": {"Amount": "19.99", "CurrencyCode": "EUR"}}], "ItemFeeList": [{"FeeType": "Commission", "FeeAmount": {"Amount": "-3.00", "CurrencyCode": "EUR"}}]}]}], "RefundEventList": []},
            {"ShipmentEventList": [{"ShipmentItemList": [{"SellerSKU": "SKU-001", "QuantityShipped": 2, "ItemChargeList": [{"ChargeType": "Principal", "ChargeAmount": {"Amount": "39.98", "CurrencyCode": "EUR"}}], "ItemFeeList": [{"FeeType": "Commission", "FeeAmount": {"Amount": "-6.00", "CurrencyCode": "EUR"}}]}]}], "RefundEventList": []},
        ]
        result = parse(get_profitability_report(days_back=30, max_orders=10))
        assert result["ordersAnalyzed"] == 2
        assert result["productBreakdown"][0]["units"] == 3

    def test_handles_finance_errors_gracefully(self, mock_client):
        mock_client.get_orders.return_value = [{"AmazonOrderId": "111"}, {"AmazonOrderId": "222"}]
        mock_client.get_financial_events_for_order.side_effect = [
            RuntimeError("API down"),
            {"ShipmentEventList": [{"ShipmentItemList": [{"SellerSKU": "SKU-001", "QuantityShipped": 1, "ItemChargeList": [{"ChargeType": "Principal", "ChargeAmount": {"Amount": "10.00", "CurrencyCode": "EUR"}}], "ItemFeeList": []}]}], "RefundEventList": []},
        ]
        assert parse(get_profitability_report(days_back=7))["ordersAnalyzed"] == 1

    def test_caps_max_orders(self, mock_client):
        mock_client.get_orders.return_value = []
        get_profitability_report(days_back=7, max_orders=100)
        assert mock_client.get_orders.call_args[1]["max_results"] == 50

    def test_error_handling(self, mock_client):
        mock_client.get_orders.side_effect = RuntimeError("Connection error")
        assert "error" in parse(get_profitability_report(days_back=7))
