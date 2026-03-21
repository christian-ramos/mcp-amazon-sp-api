"""Tools: mensajes al comprador."""

import json

from ..helpers import get_client, logger, to_json


def get_messaging_options(order_id: str, marketplace: str = "") -> str:
    """Tipos de mensaje disponibles para un pedido."""
    try:
        client = get_client(marketplace)
        actions = client.get_messaging_actions(order_id)
        return to_json({
            "orderId": order_id,
            "actions": actions,
        })
    except Exception as e:
        logger.error("Error en get_messaging_options: %s", e)
        return to_json({"error": str(e)})

def send_buyer_message(order_id: str, message_type: str, body: str, marketplace: str = "", confirm: bool = False) -> str:
    """Enviar mensaje al comprador. Requiere confirm=True."""
    try:
        body_data = json.loads(body)

        if not confirm:
            return to_json({
                "action": "SEND_BUYER_MESSAGE",
                "confirmed": False,
                "plan": {
                    "orderId": order_id,
                    "messageType": message_type,
                    "body": body_data,
                },
                "message": f"Se va a enviar un mensaje de tipo '{message_type}' al comprador del pedido '{order_id}'. Llama de nuevo con confirm=True para ejecutar.",
            })

        client = get_client(marketplace)
        result = client.send_message(order_id, message_type, body_data)
        return to_json({"orderId": order_id, "messageType": message_type, "result": result})
    except json.JSONDecodeError as e:
        return to_json({"error": f"JSON inválido en body: {e}"})
    except Exception as e:
        logger.error("Error en send_buyer_message: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(get_messaging_options)
    mcp.tool()(send_buyer_message)
