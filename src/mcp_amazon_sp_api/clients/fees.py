"""Cliente de ProductFees API."""

import logging

from sp_api.api import ProductFees
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class FeesClient(BaseClient):

    def _product_fees_api(self) -> ProductFees:
        return ProductFees(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def get_fees_estimate(
        self,
        asin: str,
        price: float,
        is_fba: bool = True,
        shipping_price: float | None = None,
    ) -> dict:
        """Estimación de fees de Amazon para un ASIN a un precio dado."""
        try:
            resp = self._product_fees_api().get_product_fees_estimate_for_asin(
                asin,
                price=price,
                currency=self._currency,
                is_fba=is_fba,
                shipping_price=shipping_price,
            )
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error estimando fees para %s: %s", asin, e)
            raise RuntimeError(f"Error SP-API al estimar fees de {asin}: {e}") from e

    @throttle_retry()
    def get_my_fees_estimates(self, estimate_requests: list[dict]) -> list[dict]:
        """Estimación de fees en batch para múltiples productos."""
        try:
            resp = self._product_fees_api().get_my_fees_estimates(estimate_requests)
            return resp.payload or []
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error estimando fees en batch: %s", e)
            raise RuntimeError(f"Error SP-API al estimar fees en batch: {e}") from e
