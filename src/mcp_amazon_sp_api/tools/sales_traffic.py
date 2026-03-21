"""Tools: report de ventas y tráfico."""

from ..helpers import get_client, iso_days_ago, iso_now, logger, to_json


def get_sales_and_traffic(days_back: int = 30, marketplace: str = "") -> str:
    """Sesiones, conversión, Buy Box % por ASIN vía report."""
    try:
        client = get_client(marketplace)
        end_date = iso_now()
        start_date = iso_days_ago(days_back)
        data = client.get_sales_and_traffic_report(start_date, end_date)
        return to_json({
            "period": f"Últimos {days_back} días",
            "totalEntries": len(data),
            "salesAndTraffic": data[:200],
        })
    except Exception as e:
        logger.error("Error en get_sales_and_traffic: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(get_sales_and_traffic)
