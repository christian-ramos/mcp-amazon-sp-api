"""Tools: gestión de listings."""

import json

from ..config import load_config
from ..helpers import get_client, logger, to_json


def _catalog_fallback(client, asin: str) -> dict | None:
    """Obtiene attributes del Catalog API. Devuelve None si no disponible."""
    try:
        catalog = client.get_catalog_item(asin, include_data=["summaries", "attributes"])
        return {
            "attributes": catalog.get("attributes", {}),
            "summaries": catalog.get("summaries", []),
        }
    except Exception as e:
        logger.debug("Catalog fallback para %s no disponible: %s", asin, e)
        return None


def _extract_attr_value(attrs: dict, key: str) -> str | None:
    """Extrae el primer valor de un atributo de tipo [{value, language_tag, ...}]."""
    values = attrs.get(key, [])
    return values[0].get("value") if values else None


def _extract_attr_values(attrs: dict, key: str) -> list[str]:
    """Extrae todos los valores de un atributo de tipo [{value, ...}]."""
    return [v.get("value") for v in attrs.get(key, []) if v.get("value")]


def get_listing_content(sku: str, marketplace: str = "") -> str:
    """Contenido de tu listing: título, bullets, keywords, offers y atributos.

    Busca primero en Listings API (datos del seller). Si faltan atributos,
    hace fallback a Catalog API (datos del catálogo, incluye traducciones BIL).
    """
    try:
        client = get_client(marketplace)
        listing = client.get_listing_item(sku)

        summaries = listing.get("summaries", [{}])
        summary = summaries[0] if summaries else {}
        attributes = listing.get("attributes", {})
        issues = listing.get("issues", [])
        offers = listing.get("offers", [])
        asin = summary.get("asin")

        # Extraer atributos del listing (seller)
        title = _extract_attr_value(attributes, "item_name") or summary.get("itemName")
        bullets = _extract_attr_values(attributes, "bullet_point")
        description = _extract_attr_value(attributes, "product_description")
        keywords = _extract_attr_values(attributes, "generic_keyword")
        brand = _extract_attr_value(attributes, "brand")
        color = _extract_attr_value(attributes, "color")
        size = _extract_attr_value(attributes, "size")
        material = _extract_attr_value(attributes, "material")
        compatible_models = _extract_attr_values(attributes, "compatible_phone_models")
        special_features = _extract_attr_values(attributes, "special_feature")

        # Fallback a Catalog API si faltan atributos
        catalog_fields = []
        if asin:
            catalog = _catalog_fallback(client, asin)
            if catalog:
                cat_attrs = catalog["attributes"]
                cat_summary = (catalog["summaries"] or [{}])[0]

                def _fill_single(field_name, attr_key, current):
                    if current:
                        return current
                    value = _extract_attr_value(cat_attrs, attr_key)
                    if not value and attr_key == "item_name":
                        value = cat_summary.get("itemName")
                    if value:
                        catalog_fields.append(field_name)
                    return value or current

                def _fill_list(field_name, attr_key, current):
                    if current:
                        return current
                    values = _extract_attr_values(cat_attrs, attr_key)
                    if values:
                        catalog_fields.append(field_name)
                    return values or current

                title = _fill_single("title", "item_name", title)
                description = _fill_single("description", "product_description", description)
                brand = _fill_single("brand", "brand", brand)
                color = _fill_single("color", "color", color)
                size = _fill_single("size", "size", size)
                material = _fill_single("material", "material", material)
                bullets = _fill_list("bulletPoints", "bullet_point", bullets)
                keywords = _fill_list("backendKeywords", "generic_keyword", keywords)
                compatible_models = _fill_list("compatibleModels", "compatible_phone_models", compatible_models)
                special_features = _fill_list("specialFeatures", "special_feature", special_features)

        result = {
            "sku": sku,
            "asin": asin,
            "status": summary.get("status"),
            "productType": summary.get("productType"),
            "title": title,
            "bulletPoints": bullets,
            "description": description,
            "backendKeywords": keywords,
            "brand": brand,
            "color": color,
            "size": size,
            "material": material,
            "compatibleModels": compatible_models,
            "specialFeatures": special_features,
            "catalogFallbackFields": catalog_fields if catalog_fields else None,
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
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_listing_content: %s", e)
        return to_json({"error": str(e)})

def list_my_listings(status: str = "", issue_severity: str = "", page_size: int = 10, marketplace: str = "") -> str:
    """Listar todos tus listings con estado e issues."""
    try:
        client = get_client(marketplace)
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
        return to_json(result)
    except Exception as e:
        logger.error("Error en list_my_listings: %s", e)
        return to_json({"error": str(e)})

def get_listing_issues(sku: str, marketplace: str = "") -> str:
    """Issues de calidad de un listing."""
    try:
        client = get_client(marketplace)
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
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_listing_issues: %s", e)
        return to_json({"error": str(e)})

def get_product_type_info(product_type: str = "", keywords: str = "", marketplace: str = "") -> str:
    """Atributos válidos de un product type o buscar tipos."""
    try:
        client = get_client(marketplace)
        if product_type:
            definition = client.get_product_type_definition(product_type)
            schema = definition.get("schema", {})

            properties = schema.get("properties", {}).get("attributes", {}).get("properties", {})
            required = schema.get("properties", {}).get("attributes", {}).get("required", [])

            if not properties:
                schema_link = schema.get("link", {}).get("resource")
                if schema_link:
                    import httpx
                    resp = httpx.get(schema_link, timeout=60)
                    if resp.status_code == 200:
                        schema_data = resp.json()
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
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_product_type_info: %s", e)
        return to_json({"error": str(e)})

def update_listing_attribute(
    sku: str,
    product_type: str,
    attribute_name: str,
    value: str,
    language_tag: str = "",
    marketplace: str = "",
    confirm: bool = False,
) -> str:
    """Actualizar un atributo de un listing. Requiere confirm=True."""
    try:
        config = load_config()
        if marketplace:
            from dataclasses import replace as dc_replace
            config = dc_replace(config, marketplace=marketplace.upper())
        lang = language_tag or config.language_tag
        mp = marketplace.upper() or config.marketplace

        if not confirm:
            return to_json({
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

        client = get_client(marketplace)
        marketplace_id = config.marketplace_id

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
        return to_json(result)
    except Exception as e:
        logger.error("Error en update_listing_attribute: %s", e)
        return to_json({"error": str(e)})

def update_listing_batch(sku: str, product_type: str, updates: str, marketplace: str = "", confirm: bool = False) -> str:
    """Actualizar múltiples atributos de un listing. Requiere confirm=True."""
    try:
        attrs = json.loads(updates)
        config = load_config()
        if marketplace:
            from dataclasses import replace as dc_replace
            config = dc_replace(config, marketplace=marketplace.upper())
        mp = marketplace.upper() or config.marketplace

        if not confirm:
            return to_json({
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

        client = get_client(marketplace)
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
        return to_json(result)
    except json.JSONDecodeError as e:
        return to_json({"error": f"JSON inválido en updates: {e}"})
    except Exception as e:
        logger.error("Error en update_listing_batch: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(get_listing_content)
    mcp.tool()(list_my_listings)
    mcp.tool()(get_listing_issues)
    mcp.tool()(get_product_type_info)
    mcp.tool()(update_listing_attribute)
    mcp.tool()(update_listing_batch)
