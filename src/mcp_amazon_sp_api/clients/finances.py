"""Cliente de Finances API."""

import logging

from sp_api.api.finances.finances_v0 import FinancesV0
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class FinancesClient(BaseClient):

    def _finances_api(self) -> FinancesV0:
        return FinancesV0(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def get_financial_events(
        self,
        posted_after: str,
        posted_before: str | None = None,
        max_results: int = 100,
    ) -> dict:
        """Eventos financieros (ventas, devoluciones, fees) en un rango de fechas. Pagina automáticamente.

        Nota: excluye las últimas 48h por política de Amazon.
        """
        all_events: dict = {}
        next_token = None

        while True:
            try:
                kwargs: dict = {"MaxResultsPerPage": min(max_results, 100)}
                if next_token:
                    kwargs["NextToken"] = next_token
                else:
                    kwargs["PostedAfter"] = posted_after
                    if posted_before:
                        kwargs["PostedBefore"] = posted_before

                resp = self._finances_api().list_financial_events(**kwargs)
                payload = resp.payload or {}
                events = payload.get("FinancialEvents", {})

                # Merge event lists
                for key, value in events.items():
                    if isinstance(value, list):
                        all_events.setdefault(key, []).extend(value)
                    elif key not in all_events:
                        all_events[key] = value

                next_token = payload.get("NextToken") or getattr(resp, "next_token", None)
                if not next_token:
                    break
            except SellingApiException as e:
                if getattr(e, "code", None) == 429:
                    raise
                logger.error("Error obteniendo eventos financieros: %s", e)
                raise RuntimeError(f"Error SP-API al obtener eventos financieros: {e}") from e

        return all_events

    @throttle_retry()
    def get_financial_events_for_order(self, order_id: str, max_results: int = 100) -> dict:
        """Eventos financieros de un pedido específico (ingresos, fees, devoluciones)."""
        try:
            resp = self._finances_api().get_financial_events_for_order(
                order_id, MaxResultsPerPage=min(max_results, 100),
            )
            return (resp.payload or {}).get("FinancialEvents", {})
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo finanzas del pedido %s: %s", order_id, e)
            raise RuntimeError(f"Error SP-API al obtener finanzas de {order_id}: {e}") from e
