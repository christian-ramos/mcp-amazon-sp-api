"""Cliente de Products Pricing API — precios competitivos y ofertas."""

import logging

from sp_api.api import Products
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class PricingClient(BaseClient):

    def _products_api(self) -> Products:
        return Products(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def get_competitive_pricing(self, asin_list: list[str]) -> list[dict]:
        """Precios competitivos + Buy Box + sales rankings por ASIN."""
        try:
            resp = self._products_api().get_competitive_pricing_for_asins(asin_list)
            payload = resp.payload
            if isinstance(payload, list):
                return payload
            return [payload] if payload else []
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo precios competitivos: %s", e)
            raise RuntimeError(f"Error SP-API al obtener precios competitivos: {e}") from e

    @throttle_retry()
    def get_item_offers(self, asin: str, item_condition: str = "New") -> dict:
        """Todas las ofertas de vendedores para un ASIN."""
        try:
            resp = self._products_api().get_item_offers(asin, item_condition)
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo ofertas de %s: %s", asin, e)
            raise RuntimeError(f"Error SP-API al obtener ofertas de {asin}: {e}") from e

    @throttle_retry()
    def get_product_pricing(self, asin_list: list[str]) -> list[dict]:
        """Tu precio vs competencia por ASIN."""
        try:
            resp = self._products_api().get_product_pricing_for_asins(asin_list)
            payload = resp.payload
            if isinstance(payload, list):
                return payload
            return [payload] if payload else []
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo pricing: %s", e)
            raise RuntimeError(f"Error SP-API al obtener pricing: {e}") from e
