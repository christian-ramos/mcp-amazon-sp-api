"""Tools: infraestructura de informes asíncronos."""

from ..helpers import get_client, iso_days_ago, iso_now, logger, to_json


def request_report(report_type: str, days_back: int = 30, marketplace: str = "") -> str:
    """Solicitar generación de un informe de Amazon (asíncrono)."""
    try:
        client = get_client(marketplace)
        end_date = iso_now()
        start_date = iso_days_ago(days_back)
        report_id = client.create_report(report_type, start_date, end_date)
        result = {
            "reportId": report_id,
            "reportType": report_type,
            "period": f"Últimos {days_back} días",
            "status": "IN_QUEUE",
            "nextStep": "Usa check_report(report_id) para ver el estado. Cuando esté DONE, usa download_report(report_id) para descargar.",
        }
        return to_json(result)
    except Exception as e:
        logger.error("Error en request_report: %s", e)
        return to_json({"error": str(e)})

def check_report(report_id: str, marketplace: str = "") -> str:
    """Estado de un informe: IN_QUEUE, IN_PROGRESS, DONE, FATAL."""
    try:
        client = get_client(marketplace)
        status = client.get_report_status(report_id)
        if status["processingStatus"] == "DONE":
            status["nextStep"] = "Usa download_report(report_id) para descargar el contenido."
        elif status["processingStatus"] in ("FATAL", "CANCELLED"):
            status["nextStep"] = "El informe falló. Intenta solicitarlo de nuevo con request_report."
        else:
            status["nextStep"] = "Aún procesando. Espera unos segundos y vuelve a consultar."
        return to_json(status)
    except Exception as e:
        logger.error("Error en check_report: %s", e)
        return to_json({"error": str(e)})

def download_report(report_id: str, marketplace: str = "") -> str:
    """Descargar contenido de un informe completado."""
    try:
        client = get_client(marketplace)
        status = client.get_report_status(report_id)
        if status["processingStatus"] != "DONE":
            return to_json({
                "error": f"El informe no está listo. Estado actual: {status['processingStatus']}",
                "reportId": report_id,
            })
        document = client.download_report(status["reportDocumentId"])
        return to_json({
            "reportId": report_id,
            "content": document,
        })
    except Exception as e:
        logger.error("Error en download_report: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(request_report)
    mcp.tool()(check_report)
    mcp.tool()(download_report)
