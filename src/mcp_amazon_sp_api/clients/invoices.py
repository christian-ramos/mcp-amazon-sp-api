"""Cliente de Invoices API — facturación."""

import logging

from sp_api.api import Invoices
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class InvoicesClient(BaseClient):

    def _invoices_api(self) -> Invoices:
        return Invoices(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def get_invoices(
        self, order_id: str | None = None, date_from: str | None = None, date_to: str | None = None,
    ) -> list[dict]:
        """Obtener facturas, opcionalmente filtradas por pedido o fecha."""
        kwargs: dict = {"marketplaceId": self._marketplace_id}
        if order_id:
            kwargs["orderId"] = order_id
        if date_from:
            kwargs["dateStart"] = date_from
        if date_to:
            kwargs["dateEnd"] = date_to

        try:
            resp = self._invoices_api().get_invoices(**kwargs)
            payload = resp.payload or {}
            return payload.get("invoices", [])
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo facturas: %s", e)
            raise RuntimeError(f"Error SP-API al obtener facturas: {e}") from e

    @throttle_retry()
    def get_invoice_document(self, invoice_id: str) -> dict:
        """Obtener documento de factura."""
        try:
            resp = self._invoices_api().get_invoices_document(invoice_id)
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo factura %s: %s", invoice_id, e)
            raise RuntimeError(f"Error SP-API al obtener factura {invoice_id}: {e}") from e
