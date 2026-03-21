"""Tools: inventario en tiempo real."""

from ..helpers import get_client, logger, to_json


def get_inventory(sku: str = "", marketplace: str = "") -> str:
    """Stock FBA en tiempo real por SKU."""
    try:
        client = get_client(marketplace)
        skus = [s.strip() for s in sku.split(",") if s.strip()] if sku else None
        summaries = client.get_inventory_summary(skus=skus)
        return to_json({
            "totalSkus": len(summaries),
            "inventory": summaries[:200],
        })
    except Exception as e:
        logger.error("Error en get_inventory: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(get_inventory)
