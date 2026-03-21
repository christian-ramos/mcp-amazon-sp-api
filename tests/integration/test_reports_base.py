"""Tests de integración para Reports API (sandbox SP-API).

Sandbox test cases de reports_2021-06-30.json:
- createReport: reportType=GET_MERCHANT_LISTINGS_ALL_DATA, dataStartTime=2024-03-10T20:11:24.000Z,
  marketplaceIds=[A1PA6795UKMFR9, ATVPDKIKX0DER] → reportId=ID323
- getReport: reportId=ID323 → processingStatus=IN_PROGRESS
- getReportDocument: reportDocumentId=0356cf79-b8b0-4226-b4b9-0ee058ea5760 → URL con contenido

Limitación sandbox: la librería envuelve el body de create_report en {"body": {...}}
y add_marketplaces añade marketplaceIds al nivel raíz. El sandbox no matchea.
Usamos _request directo para create_report. En producción el wrapper funciona.
"""

import pytest

from sp_api.api import Reports

from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestReportsBaseSandbox:

    def test_create_report(self, client):
        """createReport con _request directo — sandbox requiere body plano."""
        api = Reports(
            credentials=client._credentials,
            marketplace=client._marketplace,
        )
        resp = api._request(
            "/reports/2021-06-30/reports",
            data={
                "reportType": "GET_MERCHANT_LISTINGS_ALL_DATA",
                "dataStartTime": "2024-03-10T20:11:24.000Z",
                "marketplaceIds": ["A1PA6795UKMFR9", "ATVPDKIKX0DER"],
            },
            params={"method": "POST"},
            add_marketplace=False,
        )
        assert resp.payload["reportId"] == "ID323"

    def test_get_report(self, client):
        """getReport con reportId=ID323 → IN_PROGRESS."""
        status = client.get_report_status("ID323")
        assert status["reportId"] == "ReportId1"
        assert status["processingStatus"] == "IN_PROGRESS"

    def test_get_report_document(self, client):
        """getReportDocument con doc ID exacto → URL del documento."""
        api = Reports(
            credentials=client._credentials,
            marketplace=client._marketplace,
        )
        doc_id = "0356cf79-b8b0-4226-b4b9-0ee058ea5760"
        resp = api.get_report_document(doc_id)
        payload = resp.payload
        assert payload["reportDocumentId"] == doc_id
        assert "url" in payload
