"""Cliente de Feeds API — actualizaciones masivas de precios, stock y listings."""

import io
import json
import logging
import time

from sp_api.api import Feeds
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)

_DONE = "DONE"
_FATAL = "FATAL"
_CANCELLED = "CANCELLED"
_TERMINAL = {_DONE, _FATAL, _CANCELLED}


class FeedsClient(BaseClient):

    def _feeds_api(self) -> Feeds:
        return Feeds(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def submit_feed(
        self, feed_type: str, content: str, content_type: str = "text/tsv",
    ) -> dict:
        """Sube contenido y crea un feed. Devuelve feedId y feedDocumentId.

        Args:
            feed_type: Tipo de feed (ej: "POST_FLAT_FILE_PRICEANDQUANTITYONLY_UPDATE_DATA").
            content: Contenido del feed (TSV, XML o JSON).
            content_type: MIME type (default "text/tsv").
        """
        try:
            file = io.BytesIO(content.encode("utf-8"))
            doc_resp, feed_resp = self._feeds_api().submit_feed(
                feed_type, file, content_type,
                marketplaceIds=[self._marketplace_id],
            )
            doc_payload = doc_resp.payload or {}
            feed_payload = feed_resp.payload or {}
            return {
                "feedId": feed_payload.get("feedId"),
                "feedDocumentId": doc_payload.get("feedDocumentId"),
            }
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error enviando feed %s: %s", feed_type, e)
            raise RuntimeError(f"Error SP-API al enviar feed {feed_type}: {e}") from e

    @throttle_retry()
    def get_feed_status(self, feed_id: str) -> dict:
        """Estado de un feed: processingStatus, resultFeedDocumentId."""
        try:
            resp = self._feeds_api().get_feed(feed_id)
            payload = resp.payload or {}
            return {
                "feedId": payload.get("feedId", feed_id),
                "feedType": payload.get("feedType"),
                "processingStatus": payload.get("processingStatus"),
                "resultFeedDocumentId": payload.get("resultFeedDocumentId"),
            }
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo estado del feed %s: %s", feed_id, e)
            raise RuntimeError(f"Error SP-API al obtener estado de feed {feed_id}: {e}") from e

    @throttle_retry()
    def get_feed_result(self, feed_document_id: str) -> str:
        """Descarga el resultado de un feed procesado."""
        try:
            result = self._feeds_api().get_feed_document(feed_document_id)
            return result if isinstance(result, str) else str(result)
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error descargando resultado del feed %s: %s", feed_document_id, e)
            raise RuntimeError(
                f"Error SP-API al descargar resultado de feed {feed_document_id}: {e}"
            ) from e

    def bulk_update_prices(self, updates: list[dict]) -> dict:
        """Actualiza precios de múltiples SKUs mediante JSON_LISTINGS_FEED.

        Usa PATCH con purchasable_offer para cada SKU.

        Args:
            updates: Lista de {"sku": str, "price": float, "product_type": str (optional)}.
        """
        messages = []
        for i, u in enumerate(updates, 1):
            messages.append({
                "messageId": i,
                "sku": u["sku"],
                "operationType": "PATCH",
                "productType": u.get("product_type", "PRODUCT"),
                "patches": [{
                    "op": "replace",
                    "path": "/attributes/purchasable_offer",
                    "value": [{
                        "marketplace_id": self._marketplace_id,
                        "currency": u.get("currency", self._currency),
                        "our_price": [{"schedule": [{"value_with_tax": u["price"]}]}],
                    }],
                }],
            })

        feed_body = json.dumps({
            "header": {"sellerId": self._seller_id, "version": "2.0"},
            "messages": messages,
        })
        return self.submit_feed("JSON_LISTINGS_FEED", feed_body, "application/json")

    def bulk_update_inventory(self, updates: list[dict]) -> dict:
        """Actualiza stock de múltiples SKUs mediante JSON_LISTINGS_FEED.

        Usa PATCH con fulfillment_availability para cada SKU.

        Args:
            updates: Lista de {"sku": str, "quantity": int}.
        """
        messages = []
        for i, u in enumerate(updates, 1):
            messages.append({
                "messageId": i,
                "sku": u["sku"],
                "operationType": "PATCH",
                "productType": u.get("product_type", "PRODUCT"),
                "patches": [{
                    "op": "replace",
                    "path": "/attributes/fulfillment_availability",
                    "value": [{
                        "fulfillment_channel_code": "DEFAULT",
                        "quantity": u["quantity"],
                    }],
                }],
            })

        feed_body = json.dumps({
            "header": {"sellerId": self._seller_id, "version": "2.0"},
            "messages": messages,
        })
        return self.submit_feed("JSON_LISTINGS_FEED", feed_body, "application/json")
