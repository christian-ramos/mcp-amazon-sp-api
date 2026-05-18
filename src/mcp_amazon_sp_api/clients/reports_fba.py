"""Cliente de Reports FBA — stock, devoluciones, tarifas almacenamiento."""

import logging
from datetime import UTC

from .reports_base import ReportsBaseClient
from .reports_brand_analytics import _parse_report

logger = logging.getLogger(__name__)

# Report types FBA
FBA_INVENTORY = "GET_FBA_MYI_UNSUPPRESSED_INVENTORY_DATA"
FBA_INVENTORY_HEALTH = "GET_FBA_FULFILLMENT_INVENTORY_HEALTH_DATA"
FBA_RETURNS = "GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA"
FBA_REIMBURSEMENTS = "GET_FBA_REIMBURSEMENTS_DATA"
FBA_STORAGE_FEES = "GET_FBA_STORAGE_FEE_CHARGES_DATA"
FBA_LONGTERM_STORAGE = "GET_FBA_FULFILLMENT_LONGTERM_STORAGE_FEE_CHARGES_DATA"
RESTOCK_RECOMMENDATIONS = "GET_RESTOCK_INVENTORY_RECOMMENDATIONS_REPORT"


class FbaReportsClient(ReportsBaseClient):

    def get_fba_inventory_report(
        self, poll_interval: float = 15, timeout: float = 600,
    ) -> list[dict]:
        """Stock actual en FBA por SKU."""
        content = self.request_and_download_report(
            FBA_INVENTORY, self._default_start_date(), None,
            poll_interval=poll_interval, timeout=timeout,
        )
        return _parse_report(content)

    def get_fba_inventory_health(
        self, poll_interval: float = 15, timeout: float = 600,
    ) -> list[dict]:
        """Salud del inventario: edad, exceso, restock."""
        content = self.request_and_download_report(
            FBA_INVENTORY_HEALTH, self._default_start_date(), None,
            poll_interval=poll_interval, timeout=timeout,
        )
        return _parse_report(content)

    def get_fba_returns_report(
        self, start_date: str, end_date: str,
        poll_interval: float = 15, timeout: float = 600,
    ) -> list[dict]:
        """Devoluciones FBA con motivo detallado."""
        content = self.request_and_download_report(
            FBA_RETURNS, start_date, end_date,
            poll_interval=poll_interval, timeout=timeout,
        )
        return _parse_report(content)

    def get_fba_reimbursements(
        self, start_date: str, end_date: str,
        poll_interval: float = 15, timeout: float = 600,
    ) -> list[dict]:
        """Reembolsos de Amazon FBA."""
        content = self.request_and_download_report(
            FBA_REIMBURSEMENTS, start_date, end_date,
            poll_interval=poll_interval, timeout=timeout,
        )
        return _parse_report(content)

    def get_fba_storage_fees(
        self, poll_interval: float = 15, timeout: float = 600,
    ) -> list[dict]:
        """Tarifas de almacenamiento actuales."""
        content = self.request_and_download_report(
            FBA_STORAGE_FEES, self._default_start_date(), None,
            poll_interval=poll_interval, timeout=timeout,
        )
        return _parse_report(content)

    def get_fba_longterm_storage_fees(
        self, poll_interval: float = 15, timeout: float = 600,
    ) -> list[dict]:
        """Tarifas de almacenamiento de largo plazo."""
        content = self.request_and_download_report(
            FBA_LONGTERM_STORAGE, self._default_start_date(), None,
            poll_interval=poll_interval, timeout=timeout,
        )
        return _parse_report(content)

    def get_restock_recommendations(
        self, poll_interval: float = 15, timeout: float = 600,
    ) -> list[dict]:
        """Recomendaciones de restock."""
        content = self.request_and_download_report(
            RESTOCK_RECOMMENDATIONS, self._default_start_date(), None,
            poll_interval=poll_interval, timeout=timeout,
        )
        return _parse_report(content)

    @staticmethod
    def _default_start_date() -> str:
        """Fecha por defecto para informes de inventario (snapshot actual)."""
        from datetime import datetime, timedelta
        return (datetime.now(UTC) - timedelta(days=1)).isoformat()
