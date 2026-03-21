"""Tools: facturas."""

from ..helpers import get_client, iso_days_ago, iso_now, logger, to_json


def get_invoices(order_id: str = "", days_back: int = 30, marketplace: str = "") -> str:
    """Obtener facturas por pedido o periodo."""
    try:
        client = get_client(marketplace)
        end_date = iso_now()
        start_date = iso_days_ago(days_back)
        invoices = client.get_invoices(
            order_id=order_id or None,
            date_from=start_date if not order_id else None,
            date_to=end_date if not order_id else None,
        )
        return to_json({
            "totalInvoices": len(invoices),
            "invoices": invoices[:100],
        })
    except Exception as e:
        logger.error("Error en get_invoices: %s", e)
        return to_json({"error": str(e)})

def download_invoice(invoice_id: str, marketplace: str = "") -> str:
    """Descargar documento de factura."""
    try:
        client = get_client(marketplace)
        doc = client.get_invoice_document(invoice_id)
        return to_json(doc)
    except Exception as e:
        logger.error("Error en download_invoice: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(get_invoices)
    mcp.tool()(download_invoice)
