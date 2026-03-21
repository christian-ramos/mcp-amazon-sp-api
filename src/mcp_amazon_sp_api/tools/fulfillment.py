"""Tools: Fulfillment Inbound (envíos FBA)."""

from ..helpers import get_client, logger, to_json


def list_fba_shipments(status: str = "", shipment_ids: str = "", marketplace: str = "") -> str:
    """Envíos a FBA y su estado."""
    try:
        client = get_client(marketplace)
        ids = [s.strip() for s in shipment_ids.split(",") if s.strip()] if shipment_ids else None
        shipments = client.list_inbound_shipments(
            status=status or None,
            shipment_ids=ids,
        )
        result = []
        for s in shipments:
            result.append({
                "shipmentId": s.get("ShipmentId"),
                "shipmentName": s.get("ShipmentName"),
                "status": s.get("ShipmentStatus"),
                "destination": s.get("DestinationFulfillmentCenterId"),
                "labelPrepType": s.get("LabelPrepType"),
            })
        return to_json({
            "totalShipments": len(result),
            "shipments": result,
        })
    except Exception as e:
        logger.error("Error en list_fba_shipments: %s", e)
        return to_json({"error": str(e)})

def get_fba_shipment_items(shipment_id: str, marketplace: str = "") -> str:
    """Items de un envío a FBA: enviado vs recibido."""
    try:
        client = get_client(marketplace)
        items = client.get_shipment_items(shipment_id)
        result = []
        for item in items:
            result.append({
                "sku": item.get("SellerSKU"),
                "fnSku": item.get("FulfillmentNetworkSKU"),
                "quantityShipped": item.get("QuantityShipped"),
                "quantityReceived": item.get("QuantityReceived"),
                "quantityInCase": item.get("QuantityInCase"),
            })
        return to_json({
            "shipmentId": shipment_id,
            "totalItems": len(result),
            "items": result,
        })
    except Exception as e:
        logger.error("Error en get_fba_shipment_items: %s", e)
        return to_json({"error": str(e)})

def get_inbound_guidance(asins: str, marketplace: str = "") -> str:
    """Guía de envío a FBA: elegibilidad y prep requerido."""
    try:
        client = get_client(marketplace)
        asin_list = [a.strip() for a in asins.split(",") if a.strip()]
        guidance = client.get_inbound_guidance(asin_list)
        return to_json({
            "totalAsins": len(guidance),
            "guidance": guidance,
        })
    except Exception as e:
        logger.error("Error en get_inbound_guidance: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(list_fba_shipments)
    mcp.tool()(get_fba_shipment_items)
    mcp.tool()(get_inbound_guidance)
