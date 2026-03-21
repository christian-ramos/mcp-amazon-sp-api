"""Cliente de CatalogItems API."""

import logging

from sp_api.api import CatalogItems
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class CatalogClient(BaseClient):

    def _catalog_api(self) -> CatalogItems:
        return CatalogItems(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def get_catalog_item(self, asin: str) -> dict:
        """Detalle de un producto con relationships (parent/child)."""
        try:
            resp = self._catalog_api().get_catalog_item(
                asin,
                includedData=[
                    "summaries",
                    "attributes",
                    "images",
                    "salesRanks",
                ],
            )
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo catálogo para %s: %s", asin, e)
            raise RuntimeError(f"Error SP-API al obtener catálogo de {asin}: {e}") from e

    @throttle_retry()
    def search_catalog_items(
        self,
        keywords: str | None = None,
        identifiers: list[str] | None = None,
        max_pages: int = 5,
    ) -> list[dict]:
        """Busca productos en el catálogo por keywords o identificadores. Pagina automáticamente."""
        all_items: list[dict] = []
        page_token = None

        for _ in range(max_pages):
            try:
                kwargs: dict = {
                    "includedData": ["summaries", "salesRanks"],
                }
                if keywords:
                    kwargs["keywords"] = keywords
                if identifiers:
                    kwargs["identifiers"] = identifiers
                    kwargs["identifiersType"] = "ASIN"
                if page_token:
                    kwargs["pageToken"] = page_token

                resp = self._catalog_api().search_catalog_items(**kwargs)
                payload = resp.payload or {}
                items = payload.get("items", [])
                all_items.extend(items)

                pagination = payload.get("pagination") or {}
                page_token = pagination.get("nextToken") or getattr(resp, "next_token", None)
                if not page_token:
                    break
            except SellingApiException as e:
                if getattr(e, "code", None) == 429:
                    raise
                logger.error("Error buscando catálogo: %s", e)
                raise RuntimeError(f"Error SP-API al buscar catálogo: {e}") from e

        return all_items
