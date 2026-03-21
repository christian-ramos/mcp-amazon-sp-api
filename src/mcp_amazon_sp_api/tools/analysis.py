"""Tools: análisis de ventas, devoluciones, rentabilidad y rankings."""

from collections import defaultdict

from ..helpers import get_client, iso_days_ago, logger, to_json


def get_sales_summary(days_back: int = 30, marketplace: str = "") -> str:
    """Resumen de ventas: revenue, unidades, top productos."""
    try:
        client = get_client(marketplace)
        created_after = iso_days_ago(days_back)
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
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_sales_summary: %s", e)
        return to_json({"error": str(e)})

def get_returns_summary(days_back: int = 30, marketplace: str = "") -> str:
    """Resumen de devoluciones y reembolsos."""
    try:
        client = get_client(marketplace)
        posted_after = iso_days_ago(days_back)
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
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_returns_summary: %s", e)
        return to_json({"error": str(e)})

def get_order_finances(order_id: str, marketplace: str = "") -> str:
    """Desglose financiero de un pedido: fees, neto, margen."""
    try:
        client = get_client(marketplace)
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
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_order_finances: %s", e)
        return to_json({"error": str(e)})

def estimate_fees(asin: str, price: float, is_fba: bool = True, marketplace: str = "") -> str:
    """Estimar fees de Amazon para un producto y precio."""
    try:
        client = get_client(marketplace)
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
        return to_json(result)
    except Exception as e:
        logger.error("Error en estimate_fees: %s", e)
        return to_json({"error": str(e)})

def get_profitability_report(days_back: int = 30, max_orders: int = 20, marketplace: str = "") -> str:
    """Rentabilidad por SKU: ingresos, fees, margen neto."""
    try:
        client = get_client(marketplace)
        max_orders = min(max_orders, 50)
        created_after = iso_days_ago(days_back)
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
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_profitability_report: %s", e)
        return to_json({"error": str(e)})

def get_sales_rankings(asin: str, marketplace: str = "") -> str:
    """Rankings de ventas (BSR) por categoría."""
    try:
        client = get_client(marketplace)
        item = client.get_catalog_item(asin)

        sales_ranks = item.get("salesRanks", [])
        summaries = item.get("summaries", [{}])
        title = summaries[0].get("itemName") if summaries else None

        rankings = []
        for rank_group in sales_ranks:
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
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_sales_rankings: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(get_sales_summary)
    mcp.tool()(get_returns_summary)
    mcp.tool()(get_order_finances)
    mcp.tool()(estimate_fees)
    mcp.tool()(get_profitability_report)
    mcp.tool()(get_sales_rankings)
