"""Tools: catálogo y pedidos."""

from ..helpers import get_client, iso_days_ago, logger, to_json


def list_products(keywords: str = "", marketplace: str = "") -> str:
    """Buscar productos en el catálogo de Amazon por keywords."""
    try:
        client = get_client(marketplace)
        if keywords:
            items = client.search_catalog_items(keywords=keywords)
        else:
            items = client.search_catalog_items(keywords="water bottle")
        result = []
        for item in items:
            summaries = item.get("summaries", [{}])
            summary = summaries[0] if summaries else {}
            result.append({
                "asin": item.get("asin"),
                "title": summary.get("itemName"),
                "brand": summary.get("brand"),
                "classification": summary.get("classification", {}).get("displayName"),
            })
        return to_json(result)
    except Exception as e:
        logger.error("Error en list_products: %s", e)
        return to_json({"error": str(e)})

def get_product_details(asin: str, marketplace: str = "") -> str:
    """Detalle de un producto: título, marca, imágenes, rankings."""
    try:
        client = get_client(marketplace)
        item = client.get_catalog_item(asin)

        summaries = item.get("summaries", [{}])
        summary = summaries[0] if summaries else {}
        relationships = item.get("relationships", [])
        images = item.get("images", [])
        sales_ranks = item.get("salesRanks", [])

        parent_child = []
        for rel in relationships:
            for r in rel.get("relationships", []):
                parent_child.append({
                    "type": r.get("type"),
                    "childAsins": r.get("childAsins", []),
                    "parentAsins": r.get("parentAsins", []),
                    "variationTheme": r.get("variationTheme", {}),
                })

        result = {
            "asin": asin,
            "title": summary.get("itemName"),
            "brand": summary.get("brand"),
            "manufacturer": summary.get("manufacturer"),
            "classification": summary.get("classification"),
            "relationships": parent_child,
            "imageCount": sum(len(img.get("images", [])) for img in images),
            "salesRanks": sales_ranks,
        }
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_product_details: %s", e)
        return to_json({"error": str(e)})

def get_orders(days_back: int = 7, status: str = "", marketplace: str = "") -> str:
    """Pedidos recientes por fecha y estado."""
    try:
        client = get_client(marketplace)
        created_after = iso_days_ago(days_back)
        orders = client.get_orders(created_after=created_after)

        if status:
            orders = [o for o in orders if o.get("OrderStatus", "").lower() == status.lower()]

        result = []
        for order in orders:
            result.append({
                "orderId": order.get("AmazonOrderId"),
                "status": order.get("OrderStatus"),
                "date": order.get("PurchaseDate"),
                "total": order.get("OrderTotal", {}),
                "items": order.get("NumberOfItemsShipped", 0) + order.get("NumberOfItemsUnshipped", 0),
                "fulfillment": order.get("FulfillmentChannel"),
            })
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_orders: %s", e)
        return to_json({"error": str(e)})

def get_order_items(order_id: str, marketplace: str = "") -> str:
    """Items de un pedido: SKU, ASIN, precio, cantidad."""
    try:
        client = get_client(marketplace)
        items = client.get_order_items(order_id)

        result = []
        for item in items:
            result.append({
                "asin": item.get("ASIN"),
                "sku": item.get("SellerSKU"),
                "title": item.get("Title"),
                "quantity": item.get("QuantityOrdered"),
                "price": item.get("ItemPrice", {}),
                "tax": item.get("ItemTax", {}),
            })
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_order_items: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(list_products)
    mcp.tool()(get_product_details)
    mcp.tool()(get_orders)
    mcp.tool()(get_order_items)
