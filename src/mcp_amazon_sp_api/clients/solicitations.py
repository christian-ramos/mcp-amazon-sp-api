"""Cliente de Solicitations API — solicitar reviews."""

import logging

from sp_api.api import Solicitations
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class SolicitationsClient(BaseClient):

    def _solicitations_api(self) -> Solicitations:
        return Solicitations(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def get_solicitation_actions(self, order_id: str) -> dict:
        """Acciones de solicitud disponibles para un pedido."""
        try:
            resp = self._solicitations_api().get_solicitation_actions_for_order(
                order_id, marketplaceIds=[self._marketplace_id],
            )
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo acciones de solicitud para %s: %s", order_id, e)
            raise RuntimeError(
                f"Error SP-API al obtener acciones de solicitud para {order_id}: {e}"
            ) from e

    @throttle_retry()
    def request_review(self, order_id: str) -> dict:
        """Solicita review de producto y feedback del vendedor.

        Amazon limita a 1 solicitud por pedido, entre 5 y 30 días después de la entrega.
        """
        try:
            resp = self._solicitations_api().create_product_review_and_seller_feedback_solicitation(
                order_id, marketplaceIds=[self._marketplace_id],
            )
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error solicitando review para %s: %s", order_id, e)
            raise RuntimeError(
                f"Error SP-API al solicitar review para {order_id}: {e}"
            ) from e
