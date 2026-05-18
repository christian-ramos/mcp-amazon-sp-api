"""Cliente de Fulfillment Inbound API — envíos a FBA."""

import logging
from datetime import UTC, datetime, timedelta

from sp_api.api import FulfillmentInbound
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class FulfillmentInboundClient(BaseClient):

    def _inbound_api(self) -> FulfillmentInbound:
        return FulfillmentInbound(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def list_inbound_shipments(
        self, status: str | None = None, shipment_ids: list[str] | None = None,
        last_updated_after: str | None = None, last_updated_before: str | None = None,
    ) -> list[dict]:
        """Lista envíos entrantes a FBA. Pagina automáticamente.

        Args:
            status: Filtrar por estado (ej: "WORKING", "SHIPPED", "IN_TRANSIT", "CLOSED").
            shipment_ids: Lista de IDs específicos a consultar.
            last_updated_after: ISO 8601 — solo envíos actualizados después de esta fecha.
            last_updated_before: ISO 8601 — solo envíos actualizados antes de esta fecha.
        """
        all_shipments: list[dict] = []
        next_token = None

        while True:
            try:
                if next_token:
                    resp = self._inbound_api().get_shipments(
                        QueryType="NEXT_TOKEN",
                        NextToken=next_token,
                        MarketplaceId=self._marketplace_id,
                    )
                elif shipment_ids:
                    resp = self._inbound_api().get_shipments(
                        QueryType="SHIPMENT",
                        ShipmentIdList=",".join(shipment_ids),
                        MarketplaceId=self._marketplace_id,
                    )
                else:
                    # DATE_RANGE requiere LastUpdatedAfter Y LastUpdatedBefore
                    after = last_updated_after or (
                        datetime.now(UTC) - timedelta(days=90)
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")
                    before = last_updated_before or (
                        datetime.now(UTC) - timedelta(minutes=3)
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")
                    kwargs: dict = {
                        "QueryType": "DATE_RANGE",
                        "MarketplaceId": self._marketplace_id,
                        "LastUpdatedAfter": after,
                        "LastUpdatedBefore": before,
                        "ShipmentStatusList": status or "WORKING,SHIPPED,RECEIVING,IN_TRANSIT,CHECKED_IN,CLOSED",
                    }
                    resp = self._inbound_api().get_shipments(**kwargs)

                payload = resp.payload or {}
                shipments = payload.get("ShipmentData", [])
                all_shipments.extend(shipments)
                next_token = payload.get("NextToken") or getattr(resp, "next_token", None)
                if not next_token:
                    break
            except SellingApiException as e:
                if getattr(e, "code", None) == 429:
                    raise
                logger.error("Error listando envíos inbound: %s", e)
                raise RuntimeError(f"Error SP-API al listar envíos inbound: {e}") from e

        return all_shipments

    @throttle_retry()
    def get_shipment_items(self, shipment_id: str) -> list[dict]:
        """Items de un envío específico a FBA. Pagina automáticamente."""
        all_items: list[dict] = []
        next_token = None

        while True:
            try:
                if next_token:
                    resp = self._inbound_api().shipment_items_by_shipment(
                        shipment_id, NextToken=next_token,
                    )
                else:
                    resp = self._inbound_api().shipment_items_by_shipment(shipment_id)

                payload = resp.payload or {}
                items = payload.get("ItemData", [])
                all_items.extend(items)
                next_token = payload.get("NextToken") or getattr(resp, "next_token", None)
                if not next_token:
                    break
            except SellingApiException as e:
                if getattr(e, "code", None) == 429:
                    raise
                logger.error("Error obteniendo items del envío %s: %s", shipment_id, e)
                raise RuntimeError(
                    f"Error SP-API al obtener items del envío {shipment_id}: {e}"
                ) from e

        return all_items

    @throttle_retry()
    def get_inbound_guidance(self, asin_list: list[str]) -> list[dict]:
        """Guía de envío por ASIN: elegibilidad, prep requerido."""
        try:
            resp = self._inbound_api().item_guidance(
                MarketplaceId=self._marketplace_id,
                ASINList=",".join(asin_list),
            )
            payload = resp.payload or {}
            return payload.get("ASINInboundGuidanceList", payload.get("SKUInboundGuidanceList", []))
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo guía inbound: %s", e)
            raise RuntimeError(f"Error SP-API al obtener guía inbound: {e}") from e
