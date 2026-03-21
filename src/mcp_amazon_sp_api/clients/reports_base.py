"""Cliente base de Reports API — infraestructura para crear, polling y descargar informes."""

import logging
import time

from sp_api.api import Reports
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)

# Estados terminales
_DONE = "DONE"
_FATAL = "FATAL"
_CANCELLED = "CANCELLED"
_TERMINAL = {_DONE, _FATAL, _CANCELLED}


class ReportsBaseClient(BaseClient):

    def _reports_api(self) -> Reports:
        return Reports(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def create_report(
        self,
        report_type: str,
        start_date: str,
        end_date: str | None = None,
        marketplace_ids: list[str] | None = None,
        report_options: dict | None = None,
    ) -> str:
        """Crea un informe y devuelve el reportId.

        Usa _request directo porque la librería envuelve el body en {"body": {...}}
        y Amazon no lo parsea correctamente en producción.
        """
        body = {
            "reportType": report_type,
            "marketplaceIds": marketplace_ids or [self._marketplace_id],
        }
        if start_date:
            body["dataStartTime"] = start_date
        if end_date:
            body["dataEndTime"] = end_date
        if report_options:
            body["reportOptions"] = report_options
        try:
            resp = self._reports_api()._request(
                "/reports/2021-06-30/reports",
                data={**body, "method": "POST"},
                add_marketplace=False,
            )
            payload = resp.payload or {}
            report_id = payload.get("reportId")
            if not report_id:
                raise RuntimeError("SP-API no devolvió reportId")
            return report_id
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error creando informe %s: %s", report_type, e)
            raise RuntimeError(f"Error SP-API al crear informe {report_type}: {e}") from e

    @throttle_retry()
    def get_report_status(self, report_id: str) -> dict:
        """Devuelve estado del informe: processingStatus, reportDocumentId (si DONE)."""
        try:
            resp = self._reports_api().get_report(report_id)
            payload = resp.payload or {}
            return {
                "reportId": payload.get("reportId", report_id),
                "processingStatus": payload.get("processingStatus"),
                "reportDocumentId": payload.get("reportDocumentId"),
            }
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo estado del informe %s: %s", report_id, e)
            raise RuntimeError(f"Error SP-API al obtener estado de {report_id}: {e}") from e

    @throttle_retry()
    def download_report(self, report_document_id: str) -> str:
        """Descarga y decodifica el contenido de un informe ya completado."""
        try:
            resp = self._reports_api().get_report_document(
                report_document_id, download=True
            )
            payload = resp.payload or {}
            document = payload.get("document")
            if document is None:
                raise RuntimeError(f"No se pudo descargar el documento {report_document_id}")
            return document
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error descargando documento %s: %s", report_document_id, e)
            raise RuntimeError(f"Error SP-API al descargar {report_document_id}: {e}") from e

    def request_and_download_report(
        self,
        report_type: str,
        start_date: str,
        end_date: str | None = None,
        poll_interval: float = 15,
        timeout: float = 300,
        report_options: dict | None = None,
    ) -> str:
        """Crea informe, hace polling hasta que esté listo y descarga el contenido.

        Returns:
            Contenido del informe como string (TSV o JSON según report type).

        Raises:
            RuntimeError: si el informe falla, se cancela o se agota el timeout.
        """
        report_id = self.create_report(
            report_type, start_date, end_date, report_options=report_options,
        )
        logger.info("Informe %s creado: %s", report_type, report_id)

        elapsed = 0.0
        while elapsed < timeout:
            status = self.get_report_status(report_id)
            processing = status["processingStatus"]

            if processing == _DONE:
                doc_id = status["reportDocumentId"]
                logger.info("Informe %s listo, descargando %s", report_id, doc_id)
                return self.download_report(doc_id)

            if processing in (_FATAL, _CANCELLED):
                raise RuntimeError(
                    f"Informe {report_id} terminó con estado {processing}"
                )

            time.sleep(poll_interval)
            elapsed += poll_interval

        raise RuntimeError(
            f"Timeout ({timeout}s) esperando informe {report_id} (estado: {processing})"
        )
