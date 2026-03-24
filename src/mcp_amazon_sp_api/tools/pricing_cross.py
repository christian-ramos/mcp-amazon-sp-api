"""Tools: precios cross-marketplace."""

from ..helpers import get_client, logger, to_json


def get_cross_marketplace_prices(sku: str, marketplaces: str = "") -> str:
    """Ver precio de un SKU en todos los marketplaces EU."""
    try:
        client = get_client()
        mp_list = (
            [m.strip() for m in marketplaces.split(",") if m.strip()]
            if marketplaces
            else None
        )
        prices = client.get_prices_all_marketplaces(sku, marketplaces=mp_list)
        return to_json(
            {
                "sku": sku,
                "prices": prices,
            }
        )
    except Exception as e:
        logger.error("Error en get_cross_marketplace_prices: %s", e)
        return to_json({"error": str(e)})


def update_marketplace_price(
    sku: str, product_type: str, price: float, marketplace: str, confirm: bool = False
) -> str:
    """Cambiar precio en un marketplace. Requiere confirm=True."""
    try:
        if not confirm:
            from ..config import EU_MARKETPLACES

            mp = EU_MARKETPLACES.get(marketplace.upper(), {})
            currency = mp.get("currency", "EUR")
            return to_json(
                {
                    "action": "UPDATE_PRICE",
                    "confirmed": False,
                    "plan": {
                        "sku": sku,
                        "marketplace": marketplace.upper(),
                        "productType": product_type,
                        "newPrice": f"{price:.2f} {currency}",
                    },
                    "message": f"Se va a cambiar el precio del SKU '{sku}' a {price:.2f} {currency} en {marketplace.upper()}. Llama de nuevo con confirm=True para ejecutar.",
                }
            )

        client = get_client(marketplace)
        resp = client.update_price(sku, product_type, price, marketplace)
        return to_json(
            {
                "sku": sku,
                "marketplace": marketplace,
                "price": price,
                "status": resp.get("status"),
                "submissionId": resp.get("submissionId"),
                "issues": resp.get("issues", []),
            }
        )
    except Exception as e:
        logger.error("Error en update_marketplace_price: %s", e)
        return to_json({"error": str(e)})


def sync_marketplace_prices(
    sku: str,
    product_type: str,
    base_price: float,
    targets: str,
    adjustment_pct: float = 0.0,
    marketplace: str = "",
    confirm: bool = False,
) -> str:
    """Sincronizar precios a varios marketplaces. Requiere confirm=True."""
    try:
        target_list = [t.strip() for t in targets.split(",") if t.strip()]
        adjusted = round(base_price * (1 + adjustment_pct / 100), 2)

        if not confirm:
            return to_json(
                {
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
                }
            )

        client = get_client(marketplace)
        results = client.sync_prices(
            sku,
            product_type,
            base_price,
            target_list,
            adjustment_pct,
        )
        return to_json(
            {
                "sku": sku,
                "basePrice": base_price,
                "adjustmentPct": adjustment_pct,
                "adjustedPrice": adjusted,
                "results": results,
            }
        )
    except Exception as e:
        logger.error("Error en sync_marketplace_prices: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(get_cross_marketplace_prices)
    mcp.tool()(update_marketplace_price)
    mcp.tool()(sync_marketplace_prices)
