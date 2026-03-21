"""Tools: solicitar reviews."""

from ..helpers import get_client, logger, to_json


def check_review_eligibility(order_id: str, marketplace: str = "") -> str:
    """Ver si puedes solicitar review para un pedido."""
    try:
        client = get_client(marketplace)
        actions = client.get_solicitation_actions(order_id)
        return to_json({"orderId": order_id, "actions": actions})
    except Exception as e:
        logger.error("Error en check_review_eligibility: %s", e)
        return to_json({"error": str(e)})

def request_review(order_id: str, marketplace: str = "", confirm: bool = False) -> str:
    """Solicitar review al comprador. Requiere confirm=True."""
    try:
        if not confirm:
            return to_json({
                "action": "REQUEST_REVIEW",
                "confirmed": False,
                "plan": {
                    "orderId": order_id,
                },
                "message": f"Se va a solicitar review de producto y feedback del vendedor al comprador del pedido '{order_id}'. Esta acción solo se puede hacer 1 vez por pedido (entre 5-30 días post-entrega). Llama de nuevo con confirm=True para ejecutar.",
            })

        client = get_client(marketplace)
        result = client.request_review(order_id)
        return to_json({"orderId": order_id, "result": result})
    except Exception as e:
        logger.error("Error en request_review: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(check_review_eligibility)
    mcp.tool()(request_review)
