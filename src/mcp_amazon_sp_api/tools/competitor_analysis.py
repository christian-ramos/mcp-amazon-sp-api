"""Tools: análisis de competencia."""

from ..helpers import get_client, logger, to_json


def analyze_competitor_prices(keywords: str, max_results: int = 10, marketplace: str = "") -> str:
    """Buscar competidores y comparar precios y rankings."""
    try:
        client = get_client(marketplace)
        results = client.analyze_competitor_prices(keywords, max_results)
        return to_json({
            "keywords": keywords,
            "totalResults": len(results),
            "competitors": results,
        })
    except Exception as e:
        logger.error("Error en analyze_competitor_prices: %s", e)
        return to_json({"error": str(e)})

def compare_with_competitors(my_asin: str, keywords: str, max_results: int = 10, marketplace: str = "") -> str:
    """Comparar tu producto vs competidores similares."""
    try:
        client = get_client(marketplace)
        result = client.compare_with_competitors(my_asin, keywords, max_results)
        return to_json(result)
    except Exception as e:
        logger.error("Error en compare_with_competitors: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(analyze_competitor_prices)
    mcp.tool()(compare_with_competitors)
