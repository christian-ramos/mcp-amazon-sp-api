"""Tools: restricciones de listings y elegibilidad."""

from ..helpers import get_client, logger, to_json


def check_listing_restrictions(asin: str, condition: str = "", marketplace: str = "") -> str:
    """Ver restricciones para vender un ASIN."""
    try:
        client = get_client(marketplace)
        restrictions = client.get_listings_restrictions(
            asin, condition_type=condition or None,
        )
        return to_json({
            "asin": asin,
            "restricted": len(restrictions) > 0,
            "restrictions": restrictions,
        })
    except Exception as e:
        logger.error("Error en check_listing_restrictions: %s", e)
        return to_json({"error": str(e)})

def check_expansion_eligibility(asin: str, marketplaces: str) -> str:
    """Elegibilidad para vender en otros marketplaces EU."""
    try:
        client = get_client()
        targets = [m.strip() for m in marketplaces.split(",") if m.strip()]
        results = client.check_expansion_eligibility(asin, targets)
        eligible = [r["marketplace"] for r in results if not r.get("restricted") and "error" not in r]
        restricted = [r["marketplace"] for r in results if r.get("restricted")]
        return to_json({
            "asin": asin,
            "eligible": eligible,
            "restricted": restricted,
            "details": results,
        })
    except Exception as e:
        logger.error("Error en check_expansion_eligibility: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(check_listing_restrictions)
    mcp.tool()(check_expansion_eligibility)
