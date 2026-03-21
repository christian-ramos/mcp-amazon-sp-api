"""Registry de paquetes de tools para carga bajo demanda."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PackageInfo:
    module: str
    description: str
    tool_names: list[str]


PACKAGE_REGISTRY: dict[str, PackageInfo] = {
    "catalog_orders": PackageInfo(
        module="mcp_amazon_sp_api.tools.catalog_orders",
        description="Buscar productos en catálogo y consultar pedidos",
        tool_names=["list_products", "get_product_details", "get_orders", "get_order_items"],
    ),
    "analysis": PackageInfo(
        module="mcp_amazon_sp_api.tools.analysis",
        description="Resúmenes de ventas, devoluciones, rentabilidad y rankings",
        tool_names=["get_sales_summary", "get_returns_summary", "get_order_finances", "estimate_fees", "get_profitability_report", "get_sales_rankings"],
    ),
    "listings": PackageInfo(
        module="mcp_amazon_sp_api.tools.listings",
        description="Gestión de listings: contenido, issues, actualización",
        tool_names=["get_listing_content", "list_my_listings", "get_listing_issues", "get_product_type_info", "update_listing_attribute", "update_listing_batch"],
    ),
    "reports": PackageInfo(
        module="mcp_amazon_sp_api.tools.reports",
        description="Infraestructura de informes asíncronos",
        tool_names=["request_report", "check_report", "download_report"],
    ),
    "brand_analytics": PackageInfo(
        module="mcp_amazon_sp_api.tools.brand_analytics",
        description="Brand Analytics: keywords, rendimiento, market basket, recompras",
        tool_names=["get_search_terms", "get_search_performance", "get_market_basket", "get_repeat_purchases"],
    ),
    "fba_inventory": PackageInfo(
        module="mcp_amazon_sp_api.tools.fba_inventory",
        description="Reports FBA: stock, devoluciones, fees almacenamiento, restock",
        tool_names=["get_fba_inventory", "get_fba_returns", "get_fba_fees_report", "get_restock_suggestions"],
    ),
    "sales_traffic": PackageInfo(
        module="mcp_amazon_sp_api.tools.sales_traffic",
        description="Report de ventas y tráfico por ASIN",
        tool_names=["get_sales_and_traffic"],
    ),
    "inventory_realtime": PackageInfo(
        module="mcp_amazon_sp_api.tools.inventory_realtime",
        description="Stock FBA en tiempo real",
        tool_names=["get_inventory"],
    ),
    "pricing": PackageInfo(
        module="mcp_amazon_sp_api.tools.pricing",
        description="Precios competitivos y ofertas de competidores",
        tool_names=["get_competitive_pricing", "get_competitor_offers"],
    ),
    "aplus_content": PackageInfo(
        module="mcp_amazon_sp_api.tools.aplus_content",
        description="Gestión de A+ Content",
        tool_names=["list_aplus_content", "get_aplus_content", "get_aplus_asin_relations"],
    ),
    "pricing_cross": PackageInfo(
        module="mcp_amazon_sp_api.tools.pricing_cross",
        description="Precios cross-marketplace y sincronización",
        tool_names=["get_cross_marketplace_prices", "update_marketplace_price", "sync_marketplace_prices"],
    ),
    "competitor_analysis": PackageInfo(
        module="mcp_amazon_sp_api.tools.competitor_analysis",
        description="Análisis de competencia: precios y comparativas",
        tool_names=["analyze_competitor_prices", "compare_with_competitors"],
    ),
    "listings_restrictions": PackageInfo(
        module="mcp_amazon_sp_api.tools.listings_restrictions",
        description="Restricciones de listings y elegibilidad de expansión",
        tool_names=["check_listing_restrictions", "check_expansion_eligibility"],
    ),
    "feeds": PackageInfo(
        module="mcp_amazon_sp_api.tools.feeds",
        description="Actualizaciones masivas vía feeds",
        tool_names=["bulk_update_prices", "check_feed"],
    ),
    "fulfillment": PackageInfo(
        module="mcp_amazon_sp_api.tools.fulfillment",
        description="Envíos FBA: shipments, items, guía de inbound",
        tool_names=["list_fba_shipments", "get_fba_shipment_items", "get_inbound_guidance"],
    ),
    "messaging": PackageInfo(
        module="mcp_amazon_sp_api.tools.messaging",
        description="Mensajes al comprador",
        tool_names=["get_messaging_options", "send_buyer_message"],
    ),
    "solicitations": PackageInfo(
        module="mcp_amazon_sp_api.tools.solicitations",
        description="Solicitar reviews de producto",
        tool_names=["check_review_eligibility", "request_review"],
    ),
    "invoices": PackageInfo(
        module="mcp_amazon_sp_api.tools.invoices",
        description="Facturas: consulta y descarga",
        tool_names=["get_invoices", "download_invoice"],
    ),
    "sales_api": PackageInfo(
        module="mcp_amazon_sp_api.tools.sales_api",
        description="Métricas de ventas agregadas (respuesta inmediata)",
        tool_names=["get_order_metrics"],
    ),
}
