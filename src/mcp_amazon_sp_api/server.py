"""MCP Server — entry point. Expone tools de Amazon SP-API para Claude Desktop."""

import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import base64

from mcp.server.fastmcp import FastMCP
import mcp.types as mcp_types

from .config import load_config
from .sp_client import AmazonClient

# Logging a stderr (NUNCA stdout — corrompe el protocolo MCP stdio)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

TOOLS_PAGE_SIZE = 20
mcp = FastMCP("amazon-sp-api")


def _json(obj: object) -> str:
    """JSON formateado con soporte para caracteres españoles."""
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)


def _iso_now() -> str:
    """Timestamp actual en formato ISO8601 compatible con SP-API producción."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_days_ago(days: int) -> str:
    """Timestamp de hace N días en formato ISO8601 compatible con SP-API producción."""
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get_client(marketplace: str = "") -> AmazonClient:
    """Crea cliente SP-API. Se llama en cada tool para evitar estado global."""
    config = load_config()
    if marketplace:
        from dataclasses import replace
        config = replace(config, marketplace=marketplace.upper())
    return AmazonClient(config)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_products(keywords: str = "", marketplace: str = "") -> str:
    """Buscar productos en el catálogo de Amazon por keywords. Devuelve ASIN, título, marca."""
    try:
        client = _get_client(marketplace)
        if keywords:
            items = client.search_catalog_items(keywords=keywords)
        else:
            items = client.search_catalog_items(keywords="water bottle")
        result = []
        for item in items:
            summaries = item.get("summaries", [{}])
            summary = summaries[0] if summaries else {}
            result.append({
                "asin": item.get("asin"),
                "title": summary.get("itemName"),
                "brand": summary.get("brand"),
                "classification": summary.get("classification", {}).get("displayName"),
            })
        return _json(result)
    except Exception as e:
        logger.error("Error en list_products: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_product_details(asin: str, marketplace: str = "") -> str:
    """Detalle completo de un producto: título, marca, imágenes, rankings de ventas."""
    try:
        client = _get_client(marketplace)
        item = client.get_catalog_item(asin)

        summaries = item.get("summaries", [{}])
        summary = summaries[0] if summaries else {}
        relationships = item.get("relationships", [])
        images = item.get("images", [])
        sales_ranks = item.get("salesRanks", [])

        # Extraer parent/children de relationships
        parent_child = []
        for rel in relationships:
            for r in rel.get("relationships", []):
                parent_child.append({
                    "type": r.get("type"),
                    "childAsins": r.get("childAsins", []),
                    "parentAsins": r.get("parentAsins", []),
                    "variationTheme": r.get("variationTheme", {}),
                })

        result = {
            "asin": asin,
            "title": summary.get("itemName"),
            "brand": summary.get("brand"),
            "manufacturer": summary.get("manufacturer"),
            "classification": summary.get("classification"),
            "relationships": parent_child,
            "imageCount": sum(len(img.get("images", [])) for img in images),
            "salesRanks": sales_ranks,
        }
        return _json(result)
    except Exception as e:
        logger.error("Error en get_product_details: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_orders(days_back: int = 7, status: str = "", marketplace: str = "") -> str:
    """Obtener pedidos recientes. Solo usa CreatedAfter (no CreatedBefore) para evitar errores de timestamp."""
    try:
        client = _get_client(marketplace)
        created_after = _iso_days_ago(days_back)
        orders = client.get_orders(created_after=created_after)

        if status:
            orders = [o for o in orders if o.get("OrderStatus", "").lower() == status.lower()]

        result = []
        for order in orders:
            result.append({
                "orderId": order.get("AmazonOrderId"),
                "status": order.get("OrderStatus"),
                "date": order.get("PurchaseDate"),
                "total": order.get("OrderTotal", {}),
                "items": order.get("NumberOfItemsShipped", 0) + order.get("NumberOfItemsUnshipped", 0),
                "fulfillment": order.get("FulfillmentChannel"),
            })
        return _json(result)
    except Exception as e:
        logger.error("Error en get_orders: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_order_items(order_id: str, marketplace: str = "") -> str:
    """Obtener los items/productos de un pedido específico. Devuelve SKU, ASIN, título, precio, cantidad."""
    try:
        client = _get_client(marketplace)
        items = client.get_order_items(order_id)

        result = []
        for item in items:
            result.append({
                "asin": item.get("ASIN"),
                "sku": item.get("SellerSKU"),
                "title": item.get("Title"),
                "quantity": item.get("QuantityOrdered"),
                "price": item.get("ItemPrice", {}),
                "tax": item.get("ItemTax", {}),
            })
        return _json(result)
    except Exception as e:
        logger.error("Error en get_order_items: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_sales_summary(days_back: int = 30, marketplace: str = "") -> str:
    """Resumen agregado de ventas: revenue, unidades y top productos por ASIN."""
    try:
        client = _get_client(marketplace)
        created_after = _iso_days_ago(days_back)
        orders = client.get_orders(created_after=created_after, max_results=100)

        total_revenue = 0.0
        total_units = 0
        currency = "EUR"
        product_units: dict[str, int] = defaultdict(int)
        product_revenue: dict[str, float] = defaultdict(float)
        product_names: dict[str, str] = {}
        status_counts: dict[str, int] = defaultdict(int)

        for order in orders:
            status_counts[order.get("OrderStatus", "Unknown")] += 1
            order_total = order.get("OrderTotal", {})
            if order_total.get("Amount"):
                total_revenue += float(order_total["Amount"])
                currency = order_total.get("CurrencyCode", currency)

            units = order.get("NumberOfItemsShipped", 0) + order.get("NumberOfItemsUnshipped", 0)
            total_units += units

            # Obtener items para desglose por producto
            order_id = order.get("AmazonOrderId")
            if order_id:
                try:
                    items = client.get_order_items(order_id)
                    for item in items:
                        asin = item.get("ASIN", "Unknown")
                        qty = item.get("QuantityOrdered", 0)
                        product_units[asin] += qty
                        product_names[asin] = item.get("Title", asin)
                        price = item.get("ItemPrice", {})
                        if price.get("Amount"):
                            product_revenue[asin] += float(price["Amount"])
                except Exception as item_err:
                    logger.warning("No se pudo obtener items de %s: %s", order_id, item_err)

        # Top productos por unidades
        top_products = sorted(product_units.items(), key=lambda x: x[1], reverse=True)[:10]

        result = {
            "period": f"Últimos {days_back} días",
            "totalOrders": len(orders),
            "totalUnits": total_units,
            "totalRevenue": f"{total_revenue:.2f} {currency}",
            "ordersByStatus": dict(status_counts),
            "topProducts": [
                {
                    "asin": asin,
                    "title": product_names.get(asin, asin),
                    "unitsSold": units,
                    "revenue": f"{product_revenue.get(asin, 0):.2f} {currency}",
                }
                for asin, units in top_products
            ],
        }
        return _json(result)
    except Exception as e:
        logger.error("Error en get_sales_summary: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 2: Análisis (devoluciones, rentabilidad, rankings)
# ---------------------------------------------------------------------------


@mcp.tool()
def get_returns_summary(days_back: int = 30, marketplace: str = "") -> str:
    """Resumen de devoluciones y reembolsos en un periodo. Pagina automáticamente."""
    try:
        client = _get_client(marketplace)
        posted_after = _iso_days_ago(days_back)
        events = client.get_financial_events(posted_after=posted_after)

        refund_events = events.get("RefundEventList", [])

        total_refunds = 0
        total_refund_amount = 0.0
        currency = "EUR"
        refunds_by_asin: dict[str, dict] = defaultdict(lambda: {"count": 0, "amount": 0.0, "title": ""})

        for refund in refund_events:
            for item in refund.get("ShipmentItemList", []):
                asin = item.get("SellerSKU", item.get("ASIN", "Unknown"))
                total_refunds += item.get("QuantityShipped", 1)
                for charge in item.get("ItemChargeList", []):
                    if charge.get("ChargeType") == "Principal":
                        amount = float(charge.get("ChargeAmount", {}).get("Amount", 0))
                        currency = charge.get("ChargeAmount", {}).get("CurrencyCode", currency)
                        total_refund_amount += abs(amount)
                        refunds_by_asin[asin]["amount"] += abs(amount)
                refunds_by_asin[asin]["count"] += 1

        top_refunded = sorted(refunds_by_asin.items(), key=lambda x: x[1]["count"], reverse=True)[:10]

        result = {
            "period": f"Últimos {days_back} días",
            "totalRefunds": total_refunds,
            "totalRefundAmount": f"{total_refund_amount:.2f} {currency}",
            "refundEvents": len(refund_events),
            "topRefundedProducts": [
                {"sku": sku, "count": data["count"], "amount": f"{data['amount']:.2f} {currency}"}
                for sku, data in top_refunded
            ],
        }
        return _json(result)
    except Exception as e:
        logger.error("Error en get_returns_summary: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_order_finances(order_id: str, marketplace: str = "") -> str:
    """Desglose financiero completo de un pedido: ingresos, fees, refunds, neto, margen."""
    try:
        client = _get_client(marketplace)
        events = client.get_financial_events_for_order(order_id)

        shipments = events.get("ShipmentEventList", [])
        refunds = events.get("RefundEventList", [])

        items_breakdown = []
        total_revenue = 0.0
        total_fees = 0.0
        total_refunded = 0.0
        currency = "EUR"

        for shipment in shipments:
            for item in shipment.get("ShipmentItemList", []):
                item_revenue = 0.0
                item_fees = 0.0
                fee_details = {}

                for charge in item.get("ItemChargeList", []):
                    amount = float(charge.get("ChargeAmount", {}).get("Amount", 0))
                    currency = charge.get("ChargeAmount", {}).get("CurrencyCode", currency)
                    item_revenue += amount

                for fee in item.get("ItemFeeList", []):
                    amount = float(fee.get("FeeAmount", {}).get("Amount", 0))
                    item_fees += abs(amount)
                    fee_details[fee.get("FeeType", "Unknown")] = f"{amount:.2f}"

                net = item_revenue - item_fees
                items_breakdown.append({
                    "sku": item.get("SellerSKU"),
                    "quantity": item.get("QuantityShipped"),
                    "revenue": f"{item_revenue:.2f}",
                    "fees": f"{item_fees:.2f}",
                    "net": f"{net:.2f}",
                    "margin": f"{(net / item_revenue * 100):.1f}%" if item_revenue else "N/A",
                    "feeDetails": fee_details,
                })
                total_revenue += item_revenue
                total_fees += item_fees

        for refund in refunds:
            for item in refund.get("ShipmentItemList", []):
                for charge in item.get("ItemChargeList", []):
                    amount = float(charge.get("ChargeAmount", {}).get("Amount", 0))
                    total_refunded += abs(amount)

        total_net = total_revenue - total_fees - total_refunded
        result = {
            "orderId": order_id,
            "totalRevenue": f"{total_revenue:.2f} {currency}",
            "totalFees": f"{total_fees:.2f} {currency}",
            "totalRefunded": f"{total_refunded:.2f} {currency}",
            "totalNet": f"{total_net:.2f} {currency}",
            "margin": f"{(total_net / total_revenue * 100):.1f}%" if total_revenue else "N/A",
            "items": items_breakdown,
        }
        return _json(result)
    except Exception as e:
        logger.error("Error en get_order_finances: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def estimate_fees(asin: str, price: float, is_fba: bool = True, marketplace: str = "") -> str:
    """Estimar fees de Amazon para un producto a un precio dado. Devuelve desglose de fees y margen neto."""
    try:
        client = _get_client(marketplace)
        fees_data = client.get_fees_estimate(asin=asin, price=price, is_fba=is_fba)

        fees_result = fees_data.get("FeesEstimateResult", {})
        fees_estimate = fees_result.get("FeesEstimate", {})
        total_fees = float(fees_estimate.get("TotalFeesEstimate", {}).get("Amount", 0))
        currency = fees_estimate.get("TotalFeesEstimate", {}).get("CurrencyCode", "EUR")

        fee_details = {}
        for fee in fees_estimate.get("FeeDetailList", []):
            fee_type = fee.get("FeeType", "Unknown")
            amount = float(fee.get("FeeAmount", {}).get("Amount", 0))
            fee_details[fee_type] = f"{amount:.2f}"

        net = price - total_fees
        result = {
            "asin": asin,
            "price": f"{price:.2f} {currency}",
            "isFba": is_fba,
            "totalFees": f"{total_fees:.2f} {currency}",
            "netRevenue": f"{net:.2f} {currency}",
            "margin": f"{(net / price * 100):.1f}%",
            "feeBreakdown": fee_details,
        }
        return _json(result)
    except Exception as e:
        logger.error("Error en estimate_fees: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_profitability_report(days_back: int = 30, max_orders: int = 20, marketplace: str = "") -> str:
    """Informe de rentabilidad real por SKU: ingresos, fees, devoluciones, margen neto."""
    try:
        client = _get_client(marketplace)
        max_orders = min(max_orders, 50)
        created_after = _iso_days_ago(days_back)
        orders = client.get_orders(created_after=created_after, max_results=max_orders)

        product_data: dict[str, dict] = defaultdict(lambda: {
            "revenue": 0.0, "fees": 0.0, "refunds": 0.0, "units": 0, "title": "",
        })
        currency = "EUR"
        orders_analyzed = 0

        for order in orders:
            order_id = order.get("AmazonOrderId")
            if not order_id:
                continue
            try:
                events = client.get_financial_events_for_order(order_id)
            except Exception as fin_err:
                logger.warning("No se pudo obtener finanzas de %s: %s", order_id, fin_err)
                continue

            orders_analyzed += 1

            for shipment in events.get("ShipmentEventList", []):
                for item in shipment.get("ShipmentItemList", []):
                    sku = item.get("SellerSKU", "Unknown")
                    qty = item.get("QuantityShipped", 1)
                    product_data[sku]["units"] += qty

                    for charge in item.get("ItemChargeList", []):
                        amount = float(charge.get("ChargeAmount", {}).get("Amount", 0))
                        currency = charge.get("ChargeAmount", {}).get("CurrencyCode", currency)
                        product_data[sku]["revenue"] += amount

                    for fee in item.get("ItemFeeList", []):
                        amount = float(fee.get("FeeAmount", {}).get("Amount", 0))
                        product_data[sku]["fees"] += abs(amount)

            for refund in events.get("RefundEventList", []):
                for item in refund.get("ShipmentItemList", []):
                    sku = item.get("SellerSKU", "Unknown")
                    for charge in item.get("ItemChargeList", []):
                        amount = float(charge.get("ChargeAmount", {}).get("Amount", 0))
                        product_data[sku]["refunds"] += abs(amount)

        # Calcular neto y ordenar por rentabilidad
        products = []
        total_revenue = 0.0
        total_fees = 0.0
        total_refunds = 0.0
        for sku, data in product_data.items():
            net = data["revenue"] - data["fees"] - data["refunds"]
            margin = (net / data["revenue"] * 100) if data["revenue"] else 0
            products.append({
                "sku": sku,
                "units": data["units"],
                "revenue": f"{data['revenue']:.2f}",
                "fees": f"{data['fees']:.2f}",
                "refunds": f"{data['refunds']:.2f}",
                "net": f"{net:.2f}",
                "margin": f"{margin:.1f}%",
            })
            total_revenue += data["revenue"]
            total_fees += data["fees"]
            total_refunds += data["refunds"]

        products.sort(key=lambda x: float(x["net"]), reverse=True)
        total_net = total_revenue - total_fees - total_refunds

        result = {
            "period": f"Últimos {days_back} días",
            "ordersAnalyzed": orders_analyzed,
            "totalRevenue": f"{total_revenue:.2f} {currency}",
            "totalFees": f"{total_fees:.2f} {currency}",
            "totalRefunds": f"{total_refunds:.2f} {currency}",
            "totalNet": f"{total_net:.2f} {currency}",
            "overallMargin": f"{(total_net / total_revenue * 100):.1f}%" if total_revenue else "N/A",
            "productBreakdown": products,
        }
        return _json(result)
    except Exception as e:
        logger.error("Error en get_profitability_report: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_sales_rankings(asin: str, marketplace: str = "") -> str:
    """Obtener rankings de ventas (BSR) de un producto por categoría."""
    try:
        client = _get_client(marketplace)
        item = client.get_catalog_item(asin)

        sales_ranks = item.get("salesRanks", [])
        summaries = item.get("summaries", [{}])
        title = summaries[0].get("itemName") if summaries else None

        rankings = []
        for rank_group in sales_ranks:
            marketplace_id = rank_group.get("marketplaceId")
            for rank in rank_group.get("ranks", []):
                rankings.append({
                    "category": rank.get("title"),
                    "rank": rank.get("rank"),
                    "link": rank.get("link"),
                })

        result = {
            "asin": asin,
            "title": title,
            "rankings": rankings,
        }
        return _json(result)
    except Exception as e:
        logger.error("Error en get_sales_rankings: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 4: Listings (leer contenido, actualizar optimizaciones)
# ---------------------------------------------------------------------------


@mcp.tool()
def get_listing_content(sku: str, marketplace: str = "") -> str:
    """Leer el contenido completo de TU listing: título, bullets, descripción, keywords, ofertas e issues."""
    try:
        client = _get_client(marketplace)
        listing = client.get_listing_item(sku)

        summaries = listing.get("summaries", [{}])
        summary = summaries[0] if summaries else {}
        attributes = listing.get("attributes", {})
        issues = listing.get("issues", [])
        offers = listing.get("offers", [])

        # Extraer atributos principales
        title = attributes.get("item_name", [{}])
        title = title[0].get("value") if title else None

        bullets = [b.get("value") for b in attributes.get("bullet_point", [])]

        description = attributes.get("product_description", [{}])
        description = description[0].get("value") if description else None

        keywords = [k.get("value") for k in attributes.get("generic_keyword", [])]

        result = {
            "sku": sku,
            "asin": summary.get("asin"),
            "status": summary.get("status"),
            "productType": summary.get("productType"),
            "title": title,
            "bulletPoints": bullets,
            "description": description,
            "backendKeywords": keywords,
            "offers": [
                {
                    "price": o.get("buyingPrice", {}).get("listingPrice", {}),
                    "condition": o.get("offerType"),
                    "fulfillment": o.get("fulfillmentChannel"),
                }
                for o in offers
            ],
            "issues": [
                {
                    "severity": i.get("severity"),
                    "code": i.get("code"),
                    "message": i.get("message"),
                    "attributeNames": i.get("attributeNames", []),
                }
                for i in issues
            ],
            "issueCount": len(issues),
        }
        return _json(result)
    except Exception as e:
        logger.error("Error en get_listing_content: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def list_my_listings(status: str = "", issue_severity: str = "", page_size: int = 10, marketplace: str = "") -> str:
    """Listar MIS listings (solo productos de mi cuenta). Pagina automáticamente."""
    try:
        client = _get_client(marketplace)
        items = client.search_listings_items(
            page_size=page_size,
            with_status=status or None,
            with_issue_severity=issue_severity or None,
        )

        result = []
        for item in items:
            summaries = item.get("summaries", [{}])
            summary = summaries[0] if summaries else {}
            issues = item.get("issues", [])
            result.append({
                "sku": item.get("sku"),
                "asin": summary.get("asin"),
                "title": summary.get("itemName"),
                "status": summary.get("status"),
                "productType": summary.get("productType"),
                "issueCount": len(issues),
                "issueSeverities": list({i.get("severity") for i in issues}),
            })
        return _json(result)
    except Exception as e:
        logger.error("Error en list_my_listings: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_listing_issues(sku: str, marketplace: str = "") -> str:
    """Ver issues de calidad de un listing: errores, warnings, atributos afectados."""
    try:
        client = _get_client(marketplace)
        listing = client.get_listing_item(sku)
        issues = listing.get("issues", [])

        result = {
            "sku": sku,
            "issueCount": len(issues),
            "issues": [
                {
                    "severity": i.get("severity"),
                    "code": i.get("code"),
                    "message": i.get("message"),
                    "attributeNames": i.get("attributeNames", []),
                }
                for i in issues
            ],
        }
        return _json(result)
    except Exception as e:
        logger.error("Error en get_listing_issues: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_product_type_info(product_type: str = "", keywords: str = "", marketplace: str = "") -> str:
    """Buscar product types o ver atributos válidos para un tipo de producto."""
    try:
        client = _get_client(marketplace)
        if product_type:
            definition = client.get_product_type_definition(product_type)
            schema = definition.get("schema", {})

            # El schema puede ser inline o un link externo a S3
            properties = schema.get("properties", {}).get("attributes", {}).get("properties", {})
            required = schema.get("properties", {}).get("attributes", {}).get("required", [])

            if not properties:
                # Schema como link externo a S3 — descargar
                schema_link = schema.get("link", {}).get("resource")
                if schema_link:
                    import httpx
                    resp = httpx.get(schema_link, timeout=60)
                    if resp.status_code == 200:
                        schema_data = resp.json()
                        # En el schema externo, los atributos están en properties directamente
                        properties = schema_data.get("properties", {})
                        required = schema_data.get("required", [])

            attrs = []
            for name, prop in list(properties.items())[:50]:
                attrs.append({
                    "name": name,
                    "title": prop.get("title", name),
                    "required": name in required,
                })

            result = {
                "productType": product_type,
                "displayName": definition.get("displayName"),
                "totalAttributes": len(properties),
                "requiredAttributes": required,
                "attributes": attrs,
            }
        else:
            types = client.search_product_types(keywords=keywords or "water bottle")
            result = [
                {
                    "name": t.get("name"),
                    "displayName": t.get("displayName"),
                    "marketplaceIds": t.get("marketplaceIds", []),
                }
                for t in types
            ]
        return _json(result)
    except Exception as e:
        logger.error("Error en get_product_type_info: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def update_listing_attribute(
    sku: str,
    product_type: str,
    attribute_name: str,
    value: str,
    language_tag: str = "",
    marketplace: str = "",
    confirm: bool = False,
) -> str:
    """Actualizar un atributo de un listing (título, bullets, descripción, keywords)."""
    try:
        config = load_config()
        if marketplace:
            from dataclasses import replace as dc_replace
            config = dc_replace(config, marketplace=marketplace.upper())
        lang = language_tag or config.language_tag
        mp = marketplace.upper() or config.marketplace

        if not confirm:
            return _json({
                "action": "UPDATE_LISTING_ATTRIBUTE",
                "confirmed": False,
                "plan": {
                    "sku": sku,
                    "marketplace": mp,
                    "productType": product_type,
                    "attribute": attribute_name,
                    "newValue": value,
                    "language": lang,
                },
                "message": f"Se va a actualizar el atributo '{attribute_name}' del SKU '{sku}' en {mp}. Llama de nuevo con confirm=True para ejecutar.",
            })

        client = _get_client(marketplace)
        marketplace_id = config.marketplace_id

        # Si el valor es un JSON array (para bullets), parsear
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                patch_value = [
                    {"value": v, "language_tag": lang, "marketplace_id": marketplace_id}
                    for v in parsed
                ]
            else:
                patch_value = [{"value": value, "language_tag": lang, "marketplace_id": marketplace_id}]
        except (json.JSONDecodeError, TypeError):
            patch_value = [{"value": value, "language_tag": lang, "marketplace_id": marketplace_id}]

        patches = [{
            "op": "replace",
            "path": f"/attributes/{attribute_name}",
            "value": patch_value,
        }]

        resp = client.patch_listing_item(sku, product_type, patches)

        result = {
            "sku": resp.get("sku", sku),
            "status": resp.get("status"),
            "submissionId": resp.get("submissionId"),
            "issues": resp.get("issues", []),
        }
        return _json(result)
    except Exception as e:
        logger.error("Error en update_listing_attribute: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def update_listing_batch(sku: str, product_type: str, updates: str, marketplace: str = "", confirm: bool = False) -> str:
    """Actualizar múltiples atributos de un listing de una vez."""
    try:
        attrs = json.loads(updates)
        config = load_config()
        if marketplace:
            from dataclasses import replace as dc_replace
            config = dc_replace(config, marketplace=marketplace.upper())
        mp = marketplace.upper() or config.marketplace

        if not confirm:
            return _json({
                "action": "UPDATE_LISTING_BATCH",
                "confirmed": False,
                "plan": {
                    "sku": sku,
                    "marketplace": mp,
                    "productType": product_type,
                    "attributesToUpdate": list(attrs.keys()),
                    "values": attrs,
                },
                "message": f"Se van a actualizar {len(attrs)} atributos ({', '.join(attrs.keys())}) del SKU '{sku}' en {mp}. Llama de nuevo con confirm=True para ejecutar.",
            })

        client = _get_client(marketplace)
        lang = config.language_tag
        marketplace_id = config.marketplace_id

        patches = []
        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, list):
                patch_value = [
                    {"value": v, "language_tag": lang, "marketplace_id": marketplace_id}
                    for v in attr_value
                ]
            else:
                patch_value = [{"value": attr_value, "language_tag": lang, "marketplace_id": marketplace_id}]

            patches.append({
                "op": "replace",
                "path": f"/attributes/{attr_name}",
                "value": patch_value,
            })

        resp = client.patch_listing_item(sku, product_type, patches)

        result = {
            "sku": resp.get("sku", sku),
            "status": resp.get("status"),
            "submissionId": resp.get("submissionId"),
            "attributesUpdated": list(attrs.keys()),
            "issues": resp.get("issues", []),
        }
        return _json(result)
    except json.JSONDecodeError as e:
        return _json({"error": f"JSON inválido en updates: {e}"})
    except Exception as e:
        logger.error("Error en update_listing_batch: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 5: Reports (infraestructura base)
# ---------------------------------------------------------------------------


@mcp.tool()
def request_report(report_type: str, days_back: int = 30, marketplace: str = "") -> str:
    """Solicitar la generación de un informe de Amazon. Proceso asíncrono: devuelve reportId."""
    try:
        client = _get_client(marketplace)
        end_date = _iso_now()
        start_date = _iso_days_ago(days_back)
        report_id = client.create_report(report_type, start_date, end_date)
        result = {
            "reportId": report_id,
            "reportType": report_type,
            "period": f"Últimos {days_back} días",
            "status": "IN_QUEUE",
            "nextStep": "Usa check_report(report_id) para ver el estado. Cuando esté DONE, usa download_report(report_id) para descargar.",
        }
        return _json(result)
    except Exception as e:
        logger.error("Error en request_report: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def check_report(report_id: str, marketplace: str = "") -> str:
    """Consultar el estado de un informe solicitado (IN_QUEUE, IN_PROGRESS, DONE, FATAL)."""
    try:
        client = _get_client(marketplace)
        status = client.get_report_status(report_id)
        if status["processingStatus"] == "DONE":
            status["nextStep"] = "Usa download_report(report_id) para descargar el contenido."
        elif status["processingStatus"] in ("FATAL", "CANCELLED"):
            status["nextStep"] = "El informe falló. Intenta solicitarlo de nuevo con request_report."
        else:
            status["nextStep"] = "Aún procesando. Espera unos segundos y vuelve a consultar."
        return _json(status)
    except Exception as e:
        logger.error("Error en check_report: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def download_report(report_id: str, marketplace: str = "") -> str:
    """Descargar el contenido de un informe completado. Primero verifica que esté en DONE."""
    try:
        client = _get_client(marketplace)
        status = client.get_report_status(report_id)
        if status["processingStatus"] != "DONE":
            return _json({
                "error": f"El informe no está listo. Estado actual: {status['processingStatus']}",
                "reportId": report_id,
            })
        document = client.download_report(status["reportDocumentId"])
        return _json({
            "reportId": report_id,
            "content": document,
        })
    except Exception as e:
        logger.error("Error en download_report: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 5: Brand Analytics
# ---------------------------------------------------------------------------


@mcp.tool()
def get_search_terms(days_back: int = 30, marketplace: str = "") -> str:
    """Top keywords de búsqueda con click share y conversion share (Brand Analytics)."""
    try:
        client = _get_client(marketplace)
        end_date = _iso_now()
        start_date = _iso_days_ago(days_back)
        data = client.get_search_terms_report(start_date, end_date)
        return _json({
            "period": f"Últimos {days_back} días",
            "totalTerms": len(data),
            "searchTerms": data[:100],
        })
    except Exception as e:
        logger.error("Error en get_search_terms: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_search_performance(asins: str, marketplace: str = "") -> str:
    """Rendimiento de tus ASINs en búsquedas: impresiones, clics, carrito, compras (Brand Analytics)."""
    try:
        client = _get_client(marketplace)
        asin_list = [a.strip() for a in asins.split(",") if a.strip()]
        data = client.get_search_query_performance(asin_list)
        return _json({
            "totalEntries": len(data),
            "performance": data[:100],
        })
    except Exception as e:
        logger.error("Error en get_search_performance: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_market_basket(days_back: int = 30, marketplace: str = "") -> str:
    """Productos que los clientes compran junto con los tuyos — análisis cross-sell (Brand Analytics)."""
    try:
        client = _get_client(marketplace)
        end_date = _iso_now()
        start_date = _iso_days_ago(days_back)
        data = client.get_market_basket_report(start_date, end_date)
        return _json({
            "period": f"Últimos {days_back} días",
            "totalEntries": len(data),
            "marketBasket": data[:100],
        })
    except Exception as e:
        logger.error("Error en get_market_basket: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_repeat_purchases(days_back: int = 30, marketplace: str = "") -> str:
    """Tasa de recompra por ASIN — fidelización de clientes (Brand Analytics)."""
    try:
        client = _get_client(marketplace)
        end_date = _iso_now()
        start_date = _iso_days_ago(days_back)
        data = client.get_repeat_purchase_report(start_date, end_date)
        return _json({
            "period": f"Últimos {days_back} días",
            "totalEntries": len(data),
            "repeatPurchases": data[:100],
        })
    except Exception as e:
        logger.error("Error en get_repeat_purchases: %s", e)
        return _json({"error": str(e)})


# get_competitor_comparison eliminado — ITEM_COMPARISON y ALTERNATE_PURCHASE
# no están documentados en la API oficial y devuelven FATAL en producción.


# ---------------------------------------------------------------------------
# Tools — Fase 6: Reports FBA e Inventario
# ---------------------------------------------------------------------------


@mcp.tool()
def get_fba_inventory(marketplace: str = "") -> str:
    """Stock en FBA por SKU (vía report asíncrono, tarda 1-5 min)."""
    try:
        client = _get_client(marketplace)
        data = client.get_fba_inventory_report()
        return _json({
            "totalSkus": len(data),
            "inventory": data[:200],
        })
    except Exception as e:
        logger.error("Error en get_fba_inventory: %s", e)
        return _json({"error": str(e)})


# get_fba_inventory_health eliminado — GET_FBA_FULFILLMENT_INVENTORY_HEALTH_DATA
# no aparece en la documentación oficial y devuelve FATAL en producción (deprecado).


@mcp.tool()
def get_fba_returns(days_back: int = 30, marketplace: str = "") -> str:
    """Devoluciones FBA con motivo detallado (DEFECTIVE, CUSTOMER_RETURN, etc.) vía report asíncrono."""
    try:
        client = _get_client(marketplace)
        end_date = _iso_now()
        start_date = _iso_days_ago(days_back)
        data = client.get_fba_returns_report(start_date, end_date)
        return _json({
            "period": f"Últimos {days_back} días",
            "totalReturns": len(data),
            "returns": data[:200],
        })
    except Exception as e:
        logger.error("Error en get_fba_returns: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_fba_fees_report(marketplace: str = "") -> str:
    """Tarifas de almacenamiento FBA: actuales y de largo plazo (2 reports asíncronos, 2-10 min)."""
    try:
        client = _get_client(marketplace)
        storage = client.get_fba_storage_fees()
        longterm = client.get_fba_longterm_storage_fees()
        return _json({
            "storageFees": {
                "totalSkus": len(storage),
                "data": storage[:200],
            },
            "longtermStorageFees": {
                "totalSkus": len(longterm),
                "data": longterm[:200],
            },
        })
    except Exception as e:
        logger.error("Error en get_fba_fees_report: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_restock_suggestions(marketplace: str = "") -> str:
    """Recomendaciones de restock: qué SKUs reabastecer y cuántas unidades enviar (report asíncrono, 1-5 min)."""
    try:
        client = _get_client(marketplace)
        data = client.get_restock_recommendations()
        return _json({
            "totalSkus": len(data),
            "recommendations": data[:200],
        })
    except Exception as e:
        logger.error("Error en get_restock_suggestions: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 7: Reports Ventas y Tráfico
# ---------------------------------------------------------------------------


@mcp.tool()
def get_sales_and_traffic(days_back: int = 30, marketplace: str = "") -> str:
    """Métricas de rendimiento por ASIN: sesiones, page views, conversión, Buy Box %. Report asíncrono."""
    try:
        client = _get_client(marketplace)
        end_date = _iso_now()
        start_date = _iso_days_ago(days_back)
        data = client.get_sales_and_traffic_report(start_date, end_date)
        return _json({
            "period": f"Últimos {days_back} días",
            "totalEntries": len(data),
            "salesAndTraffic": data[:200],
        })
    except Exception as e:
        logger.error("Error en get_sales_and_traffic: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 8: Inventario en tiempo real
# ---------------------------------------------------------------------------


@mcp.tool()
def get_inventory(sku: str = "", marketplace: str = "") -> str:
    """Stock actual en FBA en tiempo real: disponible, inbound, reserved. Pagina automáticamente."""
    try:
        client = _get_client(marketplace)
        skus = [s.strip() for s in sku.split(",") if s.strip()] if sku else None
        summaries = client.get_inventory_summary(skus=skus)
        return _json({
            "totalSkus": len(summaries),
            "inventory": summaries[:200],
        })
    except Exception as e:
        logger.error("Error en get_inventory: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 9: Precios y competencia
# ---------------------------------------------------------------------------


@mcp.tool()
def get_competitive_pricing(asins: str, marketplace: str = "") -> str:
    """Precios competitivos, Buy Box y rankings de ventas por ASIN. Máximo 20 ASINs por llamada."""
    try:
        client = _get_client(marketplace)
        asin_list = [a.strip() for a in asins.split(",") if a.strip()][:20]
        data = client.get_competitive_pricing(asin_list)

        result = []
        for item in data:
            product = item.get("Product", {})
            competitive = product.get("CompetitivePricing", {})
            prices = competitive.get("CompetitivePrices", [])
            rankings = competitive.get("NumberOfOfferListings", [])
            sales_ranks = product.get("SalesRankings", [])

            pricing_info = []
            for p in prices:
                price_data = p.get("Price", {})
                pricing_info.append({
                    "condition": p.get("condition"),
                    "belongsToRequester": p.get("belongsToRequester"),
                    "landedPrice": price_data.get("LandedPrice", {}),
                    "listingPrice": price_data.get("ListingPrice", {}),
                    "shipping": price_data.get("Shipping", {}),
                })

            result.append({
                "asin": item.get("ASIN"),
                "status": item.get("status"),
                "competitivePrices": pricing_info,
                "numberOfOffers": rankings,
                "salesRankings": sales_ranks,
            })
        return _json(result)
    except Exception as e:
        logger.error("Error en get_competitive_pricing: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_competitor_offers(asin: str, marketplace: str = "") -> str:
    """Ver TODAS las ofertas de vendedores para un ASIN: precio, condición, FBA/FBM, quién tiene Buy Box."""
    try:
        client = _get_client(marketplace)
        data = client.get_item_offers(asin)

        summary = data.get("Summary", {})
        offers = data.get("Offers", [])

        result = {
            "asin": asin,
            "totalOffers": summary.get("TotalOfferCount", 0),
            "lowestPrices": summary.get("LowestPrices", []),
            "buyBoxPrices": summary.get("BuyBoxPrices", []),
            "buyBoxEligibleOffers": summary.get("BuyBoxEligibleOfferCounts", []),
            "offers": [
                {
                    "sellerId": o.get("SellerId"),
                    "condition": o.get("SubCondition"),
                    "listingPrice": o.get("ListingPrice", {}),
                    "shipping": o.get("Shipping", {}),
                    "isFba": o.get("IsFulfilledByAmazon"),
                    "isBuyBoxWinner": o.get("IsBuyBoxWinner"),
                    "isFeaturedMerchant": o.get("IsFeaturedMerchant"),
                }
                for o in offers[:20]
            ],
        }
        return _json(result)
    except Exception as e:
        logger.error("Error en get_competitor_offers: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 10: A+ Content
# ---------------------------------------------------------------------------


@mcp.tool()
def list_aplus_content(marketplace: str = "") -> str:
    """Listar todos los documentos A+ Content de tu cuenta. Pagina automáticamente."""
    try:
        client = _get_client(marketplace)
        docs = client.search_content_documents()
        result = []
        for doc in docs:
            metadata = doc.get("contentMetadata", {})
            result.append({
                "contentReferenceKey": doc.get("contentReferenceKey"),
                "name": metadata.get("name"),
                "status": metadata.get("status"),
                "badgeSet": metadata.get("badgeSet", []),
                "updateTime": metadata.get("updateTime"),
            })
        return _json({
            "totalDocuments": len(result),
            "documents": result,
        })
    except Exception as e:
        logger.error("Error en list_aplus_content: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_aplus_content(content_key: str, marketplace: str = "") -> str:
    """Leer el detalle de un documento A+ Content: módulos, textos, imágenes."""
    try:
        client = _get_client(marketplace)
        doc = client.get_content_document(content_key)
        return _json(doc)
    except Exception as e:
        logger.error("Error en get_aplus_content: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_aplus_asin_relations(content_key: str, marketplace: str = "") -> str:
    """Ver qué ASINs usan un documento A+ Content específico."""
    try:
        client = _get_client(marketplace)
        asins = client.get_content_asin_relations(content_key)
        return _json({
            "contentReferenceKey": content_key,
            "totalAsins": len(asins),
            "asins": asins,
        })
    except Exception as e:
        logger.error("Error en get_aplus_asin_relations: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 11: Precios cross-marketplace
# ---------------------------------------------------------------------------


@mcp.tool()
def get_cross_marketplace_prices(sku: str, marketplaces: str = "") -> str:
    """Ver el precio de un SKU en todos los marketplaces europeos."""
    try:
        client = _get_client()
        mp_list = [m.strip() for m in marketplaces.split(",") if m.strip()] if marketplaces else None
        prices = client.get_prices_all_marketplaces(sku, marketplaces=mp_list)
        return _json({
            "sku": sku,
            "prices": prices,
        })
    except Exception as e:
        logger.error("Error en get_cross_marketplace_prices: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def update_marketplace_price(sku: str, product_type: str, price: float, marketplace: str, confirm: bool = False) -> str:
    """Cambiar el precio de un SKU en un marketplace específico."""
    try:
        if not confirm:
            from .clients.pricing_cross import EU_MARKETPLACES
            mp = EU_MARKETPLACES.get(marketplace.upper(), {})
            currency = mp.get("currency", "EUR")
            return _json({
                "action": "UPDATE_PRICE",
                "confirmed": False,
                "plan": {
                    "sku": sku,
                    "marketplace": marketplace.upper(),
                    "productType": product_type,
                    "newPrice": f"{price:.2f} {currency}",
                },
                "message": f"Se va a cambiar el precio del SKU '{sku}' a {price:.2f} {currency} en {marketplace.upper()}. Llama de nuevo con confirm=True para ejecutar.",
            })

        client = _get_client(marketplace)
        resp = client.update_price(sku, product_type, price, marketplace)
        return _json({
            "sku": sku,
            "marketplace": marketplace,
            "price": price,
            "status": resp.get("status"),
            "submissionId": resp.get("submissionId"),
            "issues": resp.get("issues", []),
        })
    except Exception as e:
        logger.error("Error en update_marketplace_price: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def sync_marketplace_prices(
    sku: str,
    product_type: str,
    base_price: float,
    targets: str,
    adjustment_pct: float = 0.0,
    marketplace: str = "",
    confirm: bool = False,
) -> str:
    """Sincronizar precio a múltiples marketplaces (estilo BIL)."""
    try:
        target_list = [t.strip() for t in targets.split(",") if t.strip()]
        adjusted = round(base_price * (1 + adjustment_pct / 100), 2)

        if not confirm:
            return _json({
                "action": "SYNC_PRICES",
                "confirmed": False,
                "plan": {
                    "sku": sku,
                    "productType": product_type,
                    "basePrice": base_price,
                    "adjustmentPct": adjustment_pct,
                    "adjustedPrice": adjusted,
                    "targetMarketplaces": target_list,
                },
                "message": f"Se va a sincronizar el precio del SKU '{sku}' a {adjusted:.2f} EUR en {', '.join(target_list)} (base {base_price:.2f}, ajuste {adjustment_pct:+.1f}%). Llama de nuevo con confirm=True para ejecutar.",
            })

        client = _get_client(marketplace)
        results = client.sync_prices(
            sku, product_type, base_price, target_list, adjustment_pct,
        )
        return _json({
            "sku": sku,
            "basePrice": base_price,
            "adjustmentPct": adjustment_pct,
            "adjustedPrice": adjusted,
            "results": results,
        })
    except Exception as e:
        logger.error("Error en sync_marketplace_prices: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 12: Análisis de competencia
# ---------------------------------------------------------------------------


@mcp.tool()
def analyze_competitor_prices(keywords: str, max_results: int = 10, marketplace: str = "") -> str:
    """Buscar productos similares de la competencia y comparar precios, rankings y fulfillment."""
    try:
        client = _get_client(marketplace)
        results = client.analyze_competitor_prices(keywords, max_results)
        return _json({
            "keywords": keywords,
            "totalResults": len(results),
            "competitors": results,
        })
    except Exception as e:
        logger.error("Error en analyze_competitor_prices: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def compare_with_competitors(my_asin: str, keywords: str, max_results: int = 10, marketplace: str = "") -> str:
    """Comparar tu producto con competidores similares: precio, ranking, número de ofertas."""
    try:
        client = _get_client(marketplace)
        result = client.compare_with_competitors(my_asin, keywords, max_results)
        return _json(result)
    except Exception as e:
        logger.error("Error en compare_with_competitors: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 13: Listings Restrictions
# ---------------------------------------------------------------------------


@mcp.tool()
def check_listing_restrictions(asin: str, condition: str = "", marketplace: str = "") -> str:
    """Ver si puedes vender un ASIN en tu marketplace actual."""
    try:
        client = _get_client(marketplace)
        restrictions = client.get_listings_restrictions(
            asin, condition_type=condition or None,
        )
        return _json({
            "asin": asin,
            "restricted": len(restrictions) > 0,
            "restrictions": restrictions,
        })
    except Exception as e:
        logger.error("Error en check_listing_restrictions: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def check_expansion_eligibility(asin: str, marketplaces: str) -> str:
    """Verificar si puedes vender un ASIN en otros marketplaces europeos."""
    try:
        client = _get_client()
        targets = [m.strip() for m in marketplaces.split(",") if m.strip()]
        results = client.check_expansion_eligibility(asin, targets)
        eligible = [r["marketplace"] for r in results if not r.get("restricted") and "error" not in r]
        restricted = [r["marketplace"] for r in results if r.get("restricted")]
        return _json({
            "asin": asin,
            "eligible": eligible,
            "restricted": restricted,
            "details": results,
        })
    except Exception as e:
        logger.error("Error en check_expansion_eligibility: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 14: Feeds (actualizaciones masivas)
# ---------------------------------------------------------------------------


@mcp.tool()
def bulk_update_prices(updates: str, marketplace: str = "", confirm: bool = False) -> str:
    """Actualizar precios de múltiples SKUs de una vez mediante feed asíncrono."""
    try:
        data = json.loads(updates)
        mp = marketplace.upper() or load_config().marketplace

        if not confirm:
            return _json({
                "action": "BULK_UPDATE_PRICES",
                "confirmed": False,
                "plan": {
                    "marketplace": mp,
                    "totalSkus": len(data),
                    "updates": data,
                },
                "message": f"Se van a actualizar los precios de {len(data)} SKUs en {mp}: {', '.join(u['sku'] + '→' + str(u['price']) for u in data[:5])}{'...' if len(data) > 5 else ''}. Llama de nuevo con confirm=True para ejecutar.",
            })

        client = _get_client(marketplace)
        result = client.bulk_update_prices(data)
        result["totalUpdates"] = len(data)
        result["nextStep"] = "Usa check_feed(feed_id) para ver el estado del procesamiento."
        return _json(result)
    except json.JSONDecodeError as e:
        return _json({"error": f"JSON inválido: {e}"})
    except Exception as e:
        logger.error("Error en bulk_update_prices: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def check_feed(feed_id: str, marketplace: str = "") -> str:
    """Consultar el estado y resultado de un feed (actualización masiva). Si DONE, descarga el resultado."""
    try:
        client = _get_client(marketplace)
        status = client.get_feed_status(feed_id)

        if status["processingStatus"] == "DONE" and status.get("resultFeedDocumentId"):
            try:
                result_content = client.get_feed_result(status["resultFeedDocumentId"])
                status["result"] = result_content
            except Exception as e:
                status["resultError"] = str(e)
        elif status["processingStatus"] in ("FATAL", "CANCELLED"):
            status["nextStep"] = "El feed falló. Revisa los datos y reintenta."
        else:
            status["nextStep"] = "Aún procesando. Espera unos segundos y vuelve a consultar."

        return _json(status)
    except Exception as e:
        logger.error("Error en check_feed: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 15: Fulfillment Inbound
# ---------------------------------------------------------------------------


@mcp.tool()
def list_fba_shipments(status: str = "", shipment_ids: str = "", marketplace: str = "") -> str:
    """Ver envíos a FBA y su estado. Pagina automáticamente."""
    try:
        client = _get_client(marketplace)
        ids = [s.strip() for s in shipment_ids.split(",") if s.strip()] if shipment_ids else None
        shipments = client.list_inbound_shipments(
            status=status or None,
            shipment_ids=ids,
        )
        result = []
        for s in shipments:
            result.append({
                "shipmentId": s.get("ShipmentId"),
                "shipmentName": s.get("ShipmentName"),
                "status": s.get("ShipmentStatus"),
                "destination": s.get("DestinationFulfillmentCenterId"),
                "labelPrepType": s.get("LabelPrepType"),
            })
        return _json({
            "totalShipments": len(result),
            "shipments": result,
        })
    except Exception as e:
        logger.error("Error en list_fba_shipments: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_fba_shipment_items(shipment_id: str, marketplace: str = "") -> str:
    """Detalle de items en un envío a FBA: SKU, cantidad enviada vs recibida. Pagina automáticamente."""
    try:
        client = _get_client(marketplace)
        items = client.get_shipment_items(shipment_id)
        result = []
        for item in items:
            result.append({
                "sku": item.get("SellerSKU"),
                "fnSku": item.get("FulfillmentNetworkSKU"),
                "quantityShipped": item.get("QuantityShipped"),
                "quantityReceived": item.get("QuantityReceived"),
                "quantityInCase": item.get("QuantityInCase"),
            })
        return _json({
            "shipmentId": shipment_id,
            "totalItems": len(result),
            "items": result,
        })
    except Exception as e:
        logger.error("Error en get_fba_shipment_items: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def get_inbound_guidance(asins: str, marketplace: str = "") -> str:
    """Guía de envío a FBA por ASIN: elegibilidad FBA, preparación requerida."""
    try:
        client = _get_client(marketplace)
        asin_list = [a.strip() for a in asins.split(",") if a.strip()]
        guidance = client.get_inbound_guidance(asin_list)
        return _json({
            "totalAsins": len(guidance),
            "guidance": guidance,
        })
    except Exception as e:
        logger.error("Error en get_inbound_guidance: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 16: Messaging
# ---------------------------------------------------------------------------


@mcp.tool()
def get_messaging_options(order_id: str, marketplace: str = "") -> str:
    """Ver qué tipos de mensaje puedes enviar al comprador de un pedido."""
    try:
        client = _get_client(marketplace)
        actions = client.get_messaging_actions(order_id)
        return _json({
            "orderId": order_id,
            "actions": actions,
        })
    except Exception as e:
        logger.error("Error en get_messaging_options: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def send_buyer_message(order_id: str, message_type: str, body: str, marketplace: str = "", confirm: bool = False) -> str:
    """Enviar mensaje al comprador de un pedido."""
    try:
        body_data = json.loads(body)

        if not confirm:
            return _json({
                "action": "SEND_BUYER_MESSAGE",
                "confirmed": False,
                "plan": {
                    "orderId": order_id,
                    "messageType": message_type,
                    "body": body_data,
                },
                "message": f"Se va a enviar un mensaje de tipo '{message_type}' al comprador del pedido '{order_id}'. Llama de nuevo con confirm=True para ejecutar.",
            })

        client = _get_client(marketplace)
        result = client.send_message(order_id, message_type, body_data)
        return _json({"orderId": order_id, "messageType": message_type, "result": result})
    except json.JSONDecodeError as e:
        return _json({"error": f"JSON inválido en body: {e}"})
    except Exception as e:
        logger.error("Error en send_buyer_message: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 17: Solicitations
# ---------------------------------------------------------------------------


@mcp.tool()
def check_review_eligibility(order_id: str, marketplace: str = "") -> str:
    """Ver si puedes solicitar review para un pedido."""
    try:
        client = _get_client(marketplace)
        actions = client.get_solicitation_actions(order_id)
        return _json({"orderId": order_id, "actions": actions})
    except Exception as e:
        logger.error("Error en check_review_eligibility: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def request_review(order_id: str, marketplace: str = "", confirm: bool = False) -> str:
    """Solicitar review de producto y feedback del vendedor al comprador."""
    try:
        if not confirm:
            return _json({
                "action": "REQUEST_REVIEW",
                "confirmed": False,
                "plan": {
                    "orderId": order_id,
                },
                "message": f"Se va a solicitar review de producto y feedback del vendedor al comprador del pedido '{order_id}'. Esta acción solo se puede hacer 1 vez por pedido (entre 5-30 días post-entrega). Llama de nuevo con confirm=True para ejecutar.",
            })

        client = _get_client(marketplace)
        result = client.request_review(order_id)
        return _json({"orderId": order_id, "result": result})
    except Exception as e:
        logger.error("Error en request_review: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 18: Invoices
# ---------------------------------------------------------------------------


@mcp.tool()
def get_invoices(order_id: str = "", days_back: int = 30, marketplace: str = "") -> str:
    """Obtener facturas, opcionalmente filtradas por pedido."""
    try:
        client = _get_client(marketplace)
        end_date = _iso_now()
        start_date = _iso_days_ago(days_back)
        invoices = client.get_invoices(
            order_id=order_id or None,
            date_from=start_date if not order_id else None,
            date_to=end_date if not order_id else None,
        )
        return _json({
            "totalInvoices": len(invoices),
            "invoices": invoices[:100],
        })
    except Exception as e:
        logger.error("Error en get_invoices: %s", e)
        return _json({"error": str(e)})


@mcp.tool()
def download_invoice(invoice_id: str, marketplace: str = "") -> str:
    """Descargar documento de factura."""
    try:
        client = _get_client(marketplace)
        doc = client.get_invoice_document(invoice_id)
        return _json(doc)
    except Exception as e:
        logger.error("Error en download_invoice: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Tools — Fase 19: Sales API
# ---------------------------------------------------------------------------


@mcp.tool()
def get_order_metrics(days_back: int = 30, granularity: str = "Day", marketplace: str = "") -> str:
    """Métricas de ventas agregadas SIN esperar informes: unidades, revenue por periodo. Respuesta inmediata."""
    try:
        client = _get_client(marketplace)
        metrics = client.get_order_metrics(days_back=days_back, granularity=granularity)
        return _json({
            "period": f"Últimos {days_back} días",
            "granularity": granularity,
            "totalEntries": len(metrics),
            "metrics": metrics[:100],
        })
    except Exception as e:
        logger.error("Error en get_order_metrics: %s", e)
        return _json({"error": str(e)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _install_paginated_tools_list():
    """Reemplaza el handler de ListToolsRequest con uno que pagina."""

    async def paginated_handler(req: mcp_types.ListToolsRequest):
        infos = mcp._tool_manager.list_tools()
        all_tools = [
            mcp_types.Tool(
                name=i.name, title=i.title, description=i.description,
                inputSchema=i.parameters, outputSchema=i.output_schema,
                annotations=i.annotations,
            )
            for i in infos
        ]
        cursor = req.params.cursor if req.params and req.params.cursor else None
        start = int(base64.b64decode(cursor).decode()) if cursor else 0
        end = start + TOOLS_PAGE_SIZE
        page = all_tools[start:end]
        next_cursor = base64.b64encode(str(end).encode()).decode() if end < len(all_tools) else None
        return mcp_types.ServerResult(mcp_types.ListToolsResult(tools=page, nextCursor=next_cursor))

    mcp._mcp_server.request_handlers[mcp_types.ListToolsRequest] = paginated_handler


def main():
    _install_paginated_tools_list()
    mcp.run()


if __name__ == "__main__":
    main()
