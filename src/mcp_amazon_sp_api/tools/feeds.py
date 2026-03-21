"""Tools: actualizaciones masivas vía feeds."""

import json

from ..config import load_config
from ..helpers import get_client, logger, to_json


def bulk_update_prices(updates: str, marketplace: str = "", confirm: bool = False) -> str:
    """Actualizar precios en bulk vía feed. Requiere confirm=True."""
    try:
        data = json.loads(updates)
        mp = marketplace.upper() or load_config().marketplace

        if not confirm:
            return to_json({
                "action": "BULK_UPDATE_PRICES",
                "confirmed": False,
                "plan": {
                    "marketplace": mp,
                    "totalSkus": len(data),
                    "updates": data,
                },
                "message": f"Se van a actualizar los precios de {len(data)} SKUs en {mp}: {', '.join(u['sku'] + '→' + str(u['price']) for u in data[:5])}{'...' if len(data) > 5 else ''}. Llama de nuevo con confirm=True para ejecutar.",
            })

        client = get_client(marketplace)
        result = client.bulk_update_prices(data)
        result["totalUpdates"] = len(data)
        result["nextStep"] = "Usa check_feed(feed_id) para ver el estado del procesamiento."
        return to_json(result)
    except json.JSONDecodeError as e:
        return to_json({"error": f"JSON inválido: {e}"})
    except Exception as e:
        logger.error("Error en bulk_update_prices: %s", e)
        return to_json({"error": str(e)})

def check_feed(feed_id: str, marketplace: str = "") -> str:
    """Estado y resultado de un feed de actualización masiva."""
    try:
        client = get_client(marketplace)
        status = client.get_feed_status(feed_id)

        if status["processingStatus"] == "DONE" and status.get("resultFeedDocumentId"):
            try:
                result_content = client.get_feed_result(status["resultFeedDocumentId"])
                status["result"] = result_content
            except Exception as e:
                status["resultError"] = str(e)
        elif status["processingStatus"] in ("FATAL", "CANCELLED"):
            status["nextStep"] = "El feed falló. Revisa los datos y reintenta."
        else:
            status["nextStep"] = "Aún procesando. Espera unos segundos y vuelve a consultar."

        return to_json(status)
    except Exception as e:
        logger.error("Error en check_feed: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(bulk_update_prices)
    mcp.tool()(check_feed)
