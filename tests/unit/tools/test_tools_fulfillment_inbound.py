"""Tests de tools MCP: Fulfillment Inbound."""

from mcp_amazon_sp_api.tools.fulfillment import get_fba_shipment_items, get_inbound_guidance, list_fba_shipments
from .conftest import parse


class TestListFbaShipments:
    def test_returns_shipments(self, mock_client):
        mock_client.list_inbound_shipments.return_value = [
            {"ShipmentId": "SHP-1", "ShipmentName": "Envío 1", "ShipmentStatus": "SHIPPED",
             "DestinationFulfillmentCenterId": "MAD1", "LabelPrepType": "SELLER_LABEL"},
        ]
        result = parse(list_fba_shipments())
        assert result["totalShipments"] == 1
        assert result["shipments"][0]["shipmentId"] == "SHP-1"

    def test_filters_by_status(self, mock_client):
        mock_client.list_inbound_shipments.return_value = []
        parse(list_fba_shipments(status="SHIPPED"))
        mock_client.list_inbound_shipments.assert_called_once_with(status="SHIPPED", shipment_ids=None)

    def test_filters_by_ids(self, mock_client):
        mock_client.list_inbound_shipments.return_value = []
        parse(list_fba_shipments(shipment_ids="SHP-1,SHP-2"))
        mock_client.list_inbound_shipments.assert_called_once_with(status=None, shipment_ids=["SHP-1", "SHP-2"])

    def test_error_handling(self, mock_client):
        mock_client.list_inbound_shipments.side_effect = RuntimeError("Fail")
        assert "error" in parse(list_fba_shipments())


class TestGetFbaShipmentItems:
    def test_returns_items(self, mock_client):
        mock_client.get_shipment_items.return_value = [
            {"SellerSKU": "SKU-1", "QuantityShipped": 50, "QuantityReceived": 50},
        ]
        result = parse(get_fba_shipment_items(shipment_id="SHP-1"))
        assert result["totalItems"] == 1
        assert result["items"][0]["sku"] == "SKU-1"
        assert result["items"][0]["quantityShipped"] == 50

    def test_error_handling(self, mock_client):
        mock_client.get_shipment_items.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_fba_shipment_items(shipment_id="BAD"))


class TestGetInboundGuidance:
    def test_returns_guidance(self, mock_client):
        mock_client.get_inbound_guidance.return_value = [
            {"ASIN": "B001", "InboundGuidance": "InboundOK"},
        ]
        result = parse(get_inbound_guidance(asins="B001"))
        assert result["totalAsins"] == 1
        mock_client.get_inbound_guidance.assert_called_once_with(["B001"])

    def test_multiple_asins(self, mock_client):
        mock_client.get_inbound_guidance.return_value = []
        parse(get_inbound_guidance(asins="B001, B002, B003"))
        mock_client.get_inbound_guidance.assert_called_once_with(["B001", "B002", "B003"])

    def test_error_handling(self, mock_client):
        mock_client.get_inbound_guidance.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_inbound_guidance(asins="B001"))
