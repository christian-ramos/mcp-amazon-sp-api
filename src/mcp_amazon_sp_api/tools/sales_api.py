"""Tools: métricas de ventas agregadas."""

from ..helpers import get_client, logger, to_json


def get_order_metrics(days_back: int = 30, granularity: str = "Day", marketplace: str = "") -> str:
    """Métricas de ventas agregadas. Respuesta inmediata."""
    try:
        client = get_client(marketplace)
        metrics = client.get_order_metrics(days_back=days_back, granularity=granularity)
        return to_json({
            "period": f"Últimos {days_back} días",
            "granularity": granularity,
            "totalEntries": len(metrics),
            "metrics": metrics[:100],
        })
    except Exception as e:
        logger.error("Error en get_order_metrics: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(get_order_metrics)
