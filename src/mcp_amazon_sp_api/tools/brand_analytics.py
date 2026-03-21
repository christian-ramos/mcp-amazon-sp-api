"""Tools: Brand Analytics."""

from ..helpers import get_client, iso_days_ago, iso_now, logger, to_json


def get_search_terms(days_back: int = 30, marketplace: str = "") -> str:
    """Top keywords con click/conversion share (Brand Analytics)."""
    try:
        client = get_client(marketplace)
        end_date = iso_now()
        start_date = iso_days_ago(days_back)
        data = client.get_search_terms_report(start_date, end_date)
        return to_json({
            "period": f"Últimos {days_back} días",
            "totalTerms": len(data),
            "searchTerms": data[:100],
        })
    except Exception as e:
        logger.error("Error en get_search_terms: %s", e)
        return to_json({"error": str(e)})

def get_search_performance(asins: str, marketplace: str = "") -> str:
    """Rendimiento de tus ASINs en búsquedas (Brand Analytics)."""
    try:
        client = get_client(marketplace)
        asin_list = [a.strip() for a in asins.split(",") if a.strip()]
        data = client.get_search_query_performance(asin_list)
        return to_json({
            "totalEntries": len(data),
            "performance": data[:100],
        })
    except Exception as e:
        logger.error("Error en get_search_performance: %s", e)
        return to_json({"error": str(e)})

def get_market_basket(days_back: int = 30, marketplace: str = "") -> str:
    """Productos comprados junto con los tuyos (Brand Analytics)."""
    try:
        client = get_client(marketplace)
        end_date = iso_now()
        start_date = iso_days_ago(days_back)
        data = client.get_market_basket_report(start_date, end_date)
        return to_json({
            "period": f"Últimos {days_back} días",
            "totalEntries": len(data),
            "marketBasket": data[:100],
        })
    except Exception as e:
        logger.error("Error en get_market_basket: %s", e)
        return to_json({"error": str(e)})

def get_repeat_purchases(days_back: int = 30, marketplace: str = "") -> str:
    """Tasa de recompra por ASIN (Brand Analytics)."""
    try:
        client = get_client(marketplace)
        end_date = iso_now()
        start_date = iso_days_ago(days_back)
        data = client.get_repeat_purchase_report(start_date, end_date)
        return to_json({
            "period": f"Últimos {days_back} días",
            "totalEntries": len(data),
            "repeatPurchases": data[:100],
        })
    except Exception as e:
        logger.error("Error en get_repeat_purchases: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(get_search_terms)
    mcp.tool()(get_search_performance)
    mcp.tool()(get_market_basket)
    mcp.tool()(get_repeat_purchases)
