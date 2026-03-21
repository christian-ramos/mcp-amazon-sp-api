"""Tools: reports FBA e inventario."""

from ..helpers import get_client, iso_days_ago, iso_now, logger, to_json


def get_fba_inventory(marketplace: str = "") -> str:
    """Stock FBA por SKU vía report asíncrono."""
    try:
        client = get_client(marketplace)
        data = client.get_fba_inventory_report()
        return to_json({
            "totalSkus": len(data),
            "inventory": data[:200],
        })
    except Exception as e:
        logger.error("Error en get_fba_inventory: %s", e)
        return to_json({"error": str(e)})

def get_fba_returns(days_back: int = 30, marketplace: str = "") -> str:
    """Devoluciones FBA con motivo detallado vía report."""
    try:
        client = get_client(marketplace)
        end_date = iso_now()
        start_date = iso_days_ago(days_back)
        data = client.get_fba_returns_report(start_date, end_date)
        return to_json({
            "period": f"Últimos {days_back} días",
            "totalReturns": len(data),
            "returns": data[:200],
        })
    except Exception as e:
        logger.error("Error en get_fba_returns: %s", e)
        return to_json({"error": str(e)})

def get_fba_fees_report(marketplace: str = "") -> str:
    """Tarifas de almacenamiento FBA actuales y largo plazo."""
    try:
        client = get_client(marketplace)
        storage = client.get_fba_storage_fees()
        longterm = client.get_fba_longterm_storage_fees()
        return to_json({
            "storageFees": {
                "totalSkus": len(storage),
                "data": storage[:200],
            },
            "longtermStorageFees": {
                "totalSkus": len(longterm),
                "data": longterm[:200],
            },
        })
    except Exception as e:
        logger.error("Error en get_fba_fees_report: %s", e)
        return to_json({"error": str(e)})

def get_restock_suggestions(marketplace: str = "") -> str:
    """Recomendaciones de restock: qué y cuánto reabastecer."""
    try:
        client = get_client(marketplace)
        data = client.get_restock_recommendations()
        return to_json({
            "totalSkus": len(data),
            "recommendations": data[:200],
        })
    except Exception as e:
        logger.error("Error en get_restock_suggestions: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(get_fba_inventory)
    mcp.tool()(get_fba_returns)
    mcp.tool()(get_fba_fees_report)
    mcp.tool()(get_restock_suggestions)
