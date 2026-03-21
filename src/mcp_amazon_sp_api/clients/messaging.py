"""Cliente de Messaging API — mensajes a compradores."""

import logging

from sp_api.api import Messaging
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class MessagingClient(BaseClient):

    def _messaging_api(self) -> Messaging:
        return Messaging(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def get_messaging_actions(self, order_id: str) -> dict:
        """Acciones de mensajería disponibles para un pedido."""
        try:
            resp = self._messaging_api().get_messaging_actions_for_order(
                order_id, marketplaceIds=[self._marketplace_id],
            )
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo acciones de mensajería para %s: %s", order_id, e)
            raise RuntimeError(
                f"Error SP-API al obtener acciones de mensajería para {order_id}: {e}"
            ) from e

    @throttle_retry()
    def send_message(self, order_id: str, message_type: str, body: dict) -> dict:
        """Envía un mensaje al comprador.

        Args:
            order_id: ID del pedido.
            message_type: Tipo de mensaje (ej: "confirm_delivery", "unexpected_problem").
            body: Cuerpo del mensaje con los campos requeridos.
        """
        method_map = {
            "confirm_delivery": "create_confirm_delivery_details",
            "confirm_order": "create_confirm_order_details",
            "unexpected_problem": "create_unexpected_problem",
            "legal_disclosure": "create_legal_disclosure",
            "negative_feedback_removal": "create_negative_feedback_removal",
            "confirm_service": "create_confirm_service_details",
            "send_invoice": "send_invoice",
        }

        method_name = method_map.get(message_type)
        if not method_name:
            raise RuntimeError(
                f"Tipo de mensaje '{message_type}' no soportado. "
                f"Tipos válidos: {list(method_map.keys())}"
            )

        try:
            api = self._messaging_api()
            method = getattr(api, method_name)
            resp = method(order_id, body=body, marketplaceIds=[self._marketplace_id])
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error enviando mensaje %s para %s: %s", message_type, order_id, e)
            raise RuntimeError(
                f"Error SP-API al enviar mensaje {message_type} para {order_id}: {e}"
            ) from e
