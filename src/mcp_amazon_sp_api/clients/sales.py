"""Cliente de Sales API — métricas de ventas agregadas."""

import logging
from datetime import datetime, timedelta, timezone

from sp_api.api import Sales
from sp_api.base import SellingApiException, Granularity

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class SalesApiClient(BaseClient):

    def _sales_api(self) -> Sales:
        return Sales(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def get_order_metrics(
        self,
        days_back: int = 30,
        granularity: str = "Day",
    ) -> list[dict]:
        """Métricas de ventas agregadas por día/semana/mes.

        Args:
            days_back: Número de días hacia atrás.
            granularity: "Day", "Week" o "Month".
        """
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days_back)

        gran = Granularity[granularity.upper()] if hasattr(Granularity, granularity.upper()) else Granularity.DAY

        try:
            resp = self._sales_api().get_order_metrics(
                interval=(start, end),
                granularity=gran,
            )
            payload = resp.payload
            if isinstance(payload, list):
                return payload
            return [payload] if payload else []
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo métricas de ventas: %s", e)
            raise RuntimeError(f"Error SP-API al obtener métricas de ventas: {e}") from e
