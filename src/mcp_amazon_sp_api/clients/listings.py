"""Cliente de Listings Items API y ProductTypeDefinitions API."""

import logging

from sp_api.api import ProductTypeDefinitions
from sp_api.api.listings_items.listings_items_2021_08_01 import ListingsItemsV20210801
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class ListingsClient(BaseClient):

    def _listings_api(self) -> ListingsItemsV20210801:
        return ListingsItemsV20210801(credentials=self._credentials, marketplace=self._marketplace)

    def _product_type_definitions_api(self) -> ProductTypeDefinitions:
        return ProductTypeDefinitions(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def get_listing_item(self, sku: str) -> dict:
        """Contenido completo de un listing: título, bullets, descripción, keywords, imágenes, ofertas, issues."""
        try:
            resp = self._listings_api().get_listings_item(
                self._seller_id,
                sku,
                marketplaceIds=[self._marketplace_id],
                includedData=["summaries", "attributes", "issues", "offers", "fulfillmentAvailability"],
            )
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo listing %s: %s", sku, e)
            raise RuntimeError(f"Error SP-API al obtener listing {sku}: {e}") from e

    @throttle_retry()
    def search_listings_items(
        self,
        page_size: int = 20,
        identifiers: list[str] | None = None,
        identifiers_type: str | None = None,
        with_status: str | None = None,
        with_issue_severity: str | None = None,
        max_pages: int = 50,
    ) -> list[dict]:
        """Busca listings del vendedor con filtros opcionales. Pagina automáticamente."""
        all_items: list[dict] = []
        page_token = None

        for _ in range(max_pages):
            try:
                kwargs: dict = {
                    "marketplaceIds": [self._marketplace_id],
                    "includedData": ["summaries", "issues"],
                    "pageSize": min(page_size, 20),
                }
                if identifiers:
                    kwargs["identifiers"] = identifiers
                    kwargs["identifiersType"] = identifiers_type or "SKU"
                if with_status:
                    kwargs["withStatus"] = with_status
                if with_issue_severity:
                    kwargs["withIssueSeverity"] = with_issue_severity
                if page_token:
                    kwargs["pageToken"] = page_token

                resp = self._listings_api().search_listings_items(self._seller_id, **kwargs)
                payload = resp.payload or {}
                items = payload.get("items", payload.get("listingsItems", []))
                all_items.extend(items)

                pagination = payload.get("pagination") or {}
                page_token = pagination.get("nextToken") or getattr(resp, "next_token", None)
                if not page_token:
                    break
            except SellingApiException as e:
                if getattr(e, "code", None) == 429:
                    raise
                logger.error("Error buscando listings: %s", e)
                raise RuntimeError(f"Error SP-API al buscar listings: {e}") from e

        return all_items

    @throttle_retry()
    def patch_listing_item(self, sku: str, product_type: str, patches: list[dict]) -> dict:
        """Actualiza atributos de un listing existente (PATCH parcial).

        Cada patch: {"op": "replace", "path": "/attributes/item_name",
                     "value": [{"value": "...", "language_tag": "es_ES", "marketplace_id": "A1RKKUPIHCS9HS"}]}
        """
        try:
            body = {
                "productType": product_type,
                "patches": patches,
            }
            resp = self._listings_api().patch_listings_item(
                self._seller_id,
                sku,
                marketplaceIds=[self._marketplace_id],
                body=body,
            )
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error actualizando listing %s: %s", sku, e)
            raise RuntimeError(f"Error SP-API al actualizar listing {sku}: {e}") from e

    @throttle_retry()
    def get_product_type_definition(self, product_type: str) -> dict:
        """Definición de un product type: atributos válidos, requeridos, schema."""
        try:
            resp = self._product_type_definitions_api().get_definitions_product_type(
                product_type,
                marketplaceIds=[self._marketplace_id],
                requirements="LISTING",
                requirementsEnforced="ENFORCED",
                locale=self._language_tag,
            )
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo definición de %s: %s", product_type, e)
            raise RuntimeError(f"Error SP-API al obtener definición de {product_type}: {e}") from e

    @throttle_retry()
    def search_product_types(self, keywords: str) -> list[dict]:
        """Busca product types por keywords."""
        try:
            resp = self._product_type_definitions_api().search_definitions_product_types(
                marketplaceIds=[self._marketplace_id],
                keywords=keywords,
            )
            payload = resp.payload or {}
            return payload.get("productTypes", [])
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error buscando product types: %s", e)
            raise RuntimeError(f"Error SP-API al buscar product types: {e}") from e
