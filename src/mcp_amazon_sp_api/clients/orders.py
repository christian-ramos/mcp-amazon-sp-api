"""Cliente de Orders API."""

import logging

from sp_api.api import Orders
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class OrdersClient(BaseClient):

    def _orders_api(self) -> Orders:
        return Orders(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def get_orders(
        self,
        created_after: str,
        created_before: str | None = None,
        max_results: int = 100,
    ) -> list[dict]:
        """Obtiene pedidos en un rango de fechas. Pagina automáticamente."""
        all_orders: list[dict] = []
        next_token = None

        while True:
            kwargs: dict = {
                "CreatedAfter": created_after,
                "MaxResultsPerPage": min(max_results, 100),
                "MarketplaceIds": [self._marketplace_id],
            }
            if created_before:
                kwargs["CreatedBefore"] = created_before
            if next_token:
                kwargs["NextToken"] = next_token

            try:
                resp = self._orders_api().get_orders(**kwargs)
                payload = resp.payload or {}
                orders = payload.get("Orders", [])
                all_orders.extend(orders)
                next_token = payload.get("NextToken")
                if not next_token or len(all_orders) >= max_results:
                    break
            except SellingApiException as e:
                if getattr(e, "code", None) == 429:
                    raise
                logger.error("Error obteniendo pedidos: %s", e)
                raise RuntimeError(f"Error SP-API al obtener pedidos: {e}") from e

        return all_orders[:max_results]

    @throttle_retry()
    def get_order_items(self, order_id: str) -> list[dict]:
        """Obtiene los items de un pedido específico."""
        try:
            resp = self._orders_api().get_order_items(order_id)
            payload = resp.payload or {}
            return payload.get("OrderItems", [])
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo items del pedido %s: %s", order_id, e)
            raise RuntimeError(f"Error SP-API al obtener items de {order_id}: {e}") from e
