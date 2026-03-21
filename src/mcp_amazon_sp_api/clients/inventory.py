"""Cliente de Inventories API — stock en tiempo real."""

import logging

from sp_api.api import Inventories
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class InventoryClient(BaseClient):

    def _inventories_api(self) -> Inventories:
        return Inventories(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def get_inventory_summary(
        self,
        skus: list[str] | None = None,
        start_date_time: str | None = None,
    ) -> list[dict]:
        """Stock disponible, inbound, reserved por SKU.

        Args:
            skus: Lista de SKUs a consultar (máx 50). None = todos (pagina automáticamente).
            start_date_time: Solo inventario modificado después de esta fecha (ISO 8601).
        """
        all_items: list[dict] = []
        next_token = None

        while True:
            kwargs: dict = {}
            if start_date_time and not next_token:
                kwargs["startDateTime"] = start_date_time
            elif skus and not next_token:
                kwargs["sellerSkus"] = ",".join(skus)
            if next_token:
                kwargs["nextToken"] = next_token

            try:
                resp = self._inventories_api().get_inventory_summary_marketplace(**kwargs)
                payload = resp.payload or {}
                summaries = payload.get("inventorySummaries", [])
                all_items.extend(summaries)
                # nextToken puede estar en payload.pagination o en resp.next_token
                pagination = payload.get("pagination") or {}
                next_token = (
                    pagination.get("nextToken")
                    or payload.get("nextToken")
                    or getattr(resp, "next_token", None)
                )
                if not next_token:
                    break
            except SellingApiException as e:
                if getattr(e, "code", None) == 429:
                    raise
                logger.error("Error obteniendo inventario: %s", e)
                raise RuntimeError(f"Error SP-API al obtener inventario: {e}") from e

        return all_items
