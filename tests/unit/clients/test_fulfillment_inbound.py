"""Tests unitarios para FulfillmentInboundClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient
from .conftest import make_response, make_api_error


class TestListInboundShipments:
    @patch.object(AmazonClient, "_inbound_api")
    def test_returns_shipments(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_shipments.return_value = make_response({
            "ShipmentData": [
                {"ShipmentId": "SHP-1", "ShipmentStatus": "SHIPPED"},
                {"ShipmentId": "SHP-2", "ShipmentStatus": "CLOSED"},
            ],
        })
        result = client.list_inbound_shipments()
        assert len(result) == 2
        assert result[0]["ShipmentId"] == "SHP-1"

    @patch.object(AmazonClient, "_inbound_api")
    def test_filters_by_status(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_shipments.return_value = make_response({"ShipmentData": []})
        client.list_inbound_shipments(status="SHIPPED")
        kwargs = mock_api.get_shipments.call_args[1]
        assert kwargs["ShipmentStatusList"] == "SHIPPED"
        assert kwargs["QueryType"] == "DATE_RANGE"

    @patch.object(AmazonClient, "_inbound_api")
    def test_filters_by_ids(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_shipments.return_value = make_response({"ShipmentData": []})
        client.list_inbound_shipments(shipment_ids=["SHP-1", "SHP-2"])
        kwargs = mock_api.get_shipments.call_args[1]
        assert kwargs["QueryType"] == "SHIPMENT"
        assert "SHP-1,SHP-2" == kwargs["ShipmentIdList"]

    @patch.object(AmazonClient, "_inbound_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_shipments.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.list_inbound_shipments()


class TestGetShipmentItems:
    @patch.object(AmazonClient, "_inbound_api")
    def test_returns_items(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.shipment_items_by_shipment.return_value = make_response({
            "ItemData": [
                {"SellerSKU": "SKU-1", "QuantityShipped": 50, "QuantityReceived": 50},
                {"SellerSKU": "SKU-2", "QuantityShipped": 30, "QuantityReceived": 25},
            ],
        })
        result = client.get_shipment_items("SHP-1")
        assert len(result) == 2
        assert result[0]["SellerSKU"] == "SKU-1"

    @patch.object(AmazonClient, "_inbound_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.shipment_items_by_shipment.side_effect = make_api_error(404)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_shipment_items("BAD-SHP")


class TestGetInboundGuidance:
    @patch.object(AmazonClient, "_inbound_api")
    def test_returns_guidance(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.item_guidance.return_value = make_response({
            "ASINInboundGuidanceList": [
                {"ASIN": "B001", "InboundGuidance": "InboundOK"},
                {"ASIN": "B002", "InboundGuidance": "InboundNotRecommended",
                 "GuidanceReasonList": ["SlowMovingASIN"]},
            ],
        })
        result = client.get_inbound_guidance(["B001", "B002"])
        assert len(result) == 2
        assert result[0]["InboundGuidance"] == "InboundOK"

    @patch.object(AmazonClient, "_inbound_api")
    def test_passes_asin_list(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.item_guidance.return_value = make_response({"ASINInboundGuidanceList": []})
        client.get_inbound_guidance(["B001", "B002"])
        kwargs = mock_api.item_guidance.call_args[1]
        assert kwargs["ASINList"] == "B001,B002"

    @patch.object(AmazonClient, "_inbound_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.item_guidance.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_inbound_guidance(["BAD"])
