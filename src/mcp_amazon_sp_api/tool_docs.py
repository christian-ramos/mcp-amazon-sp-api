"""Documentación detallada de cada MCP tool para el resource tool-docs://."""

TOOL_DOCS: dict[str, str] = {
    # --- Fase 1: Catálogo y Pedidos ---
    "list_products": """Buscar productos en el catálogo de Amazon por keywords.

Busca en TODO el catálogo de Amazon, no solo tus productos. Para ver solo tus listings usa list_my_listings.
Pagina automáticamente (puede devolver más de 10 resultados).

Parámetros:
- keywords: Términos de búsqueda (ej: "Acme water bottle 16"). Si vacío, busca "water bottle".
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_product_details": """Detalle completo de un producto: título, marca, imágenes, rankings de ventas.

Busca en el catálogo de Amazon (cualquier producto, no solo tuyos).
Para ver el contenido de TU listing (bullets, keywords, offers, issues) usa get_listing_content.

Parámetros:
- asin: ASIN del producto (ej: "B0XXXXXXX1")
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_orders": """Obtener pedidos recientes. Solo usa CreatedAfter (no CreatedBefore) para evitar errores.

Cada pedido es solo la cabecera. Para ver los productos de un pedido usa get_order_items.
Para obtener muchos pedidos con items, considerar get_sales_summary o get_order_metrics que son más eficientes.

Parámetros:
- days_back: Días hacia atrás (default 7, máx recomendado 30)
- status: "Shipped", "Unshipped", "Cancelled". Vacío = todos.
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_order_items": """Items/productos de un pedido específico. Devuelve SKU, ASIN, título, precio, cantidad.

NOTA: Rate limit estricto (~1 req/seg). Evitar llamar en bucle para muchos pedidos.
Para análisis de ventas masivo, preferir get_sales_summary o get_order_metrics.

Parámetros:
- order_id: ID del pedido (ej: "403-1234567-8901234")
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    # --- Fase 2: Análisis ---
    "get_sales_summary": """Resumen agregado de ventas: revenue, unidades y top productos por ASIN.

Hace 1 llamada por pedido para obtener items — lento con muchos pedidos.
Para >50 pedidos considerar get_order_metrics (más rápido, sin desglose por producto).

Parámetros:
- days_back: Días hacia atrás (default 30)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_returns_summary": """Resumen de devoluciones y reembolsos. Pagina automáticamente.

Datos financieros tienen retraso de ~48h respecto al momento actual.
Para devoluciones con motivo detallado (DEFECTIVE, CUSTOMER_RETURN) usar get_fba_returns.

Parámetros:
- days_back: Días hacia atrás (default 30)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_order_finances": """Desglose financiero completo de un pedido: ingresos, fees, refunds, neto, margen.

Parámetros:
- order_id: ID del pedido (ej: "403-1234567-8901234")
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "estimate_fees": """Estimar fees de Amazon para un producto a un precio dado. Desglose de fees y margen neto.

Parámetros:
- asin: ASIN del producto
- price: Precio de venta (en moneda del marketplace)
- is_fba: Si usa Fulfillment by Amazon (default True)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_profitability_report": """Rentabilidad real por SKU: ingresos, fees, devoluciones, margen neto.

Hace 1 llamada API por pedido (finanzas) — lento. Usar max_orders para limitar.
Rate limit estricto en Finances API (~0.5 req/seg).

Parámetros:
- days_back: Días hacia atrás (default 30)
- max_orders: Máximo pedidos a analizar (default 20, máx 50)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_sales_rankings": """Rankings de ventas (BSR) de un producto por categoría.

Parámetros:
- asin: ASIN del producto
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    # --- Fase 4: Listings ---
    "get_listing_content": """Contenido completo de TU listing: título, bullets, descripción, keywords, ofertas, issues.

Solo funciona con SKUs de tu cuenta. Para productos de otros vendedores usa get_product_details.

Parámetros:
- sku: SKU del producto (ej: "WB-500-SLV")
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "list_my_listings": """Listar MIS listings (solo productos de mi cuenta). Pagina automáticamente.

A diferencia de list_products (catálogo general), esto solo devuelve tus propios productos.
Cada listing incluye: SKU, ASIN, título, estado (BUYABLE/DISCOVERABLE), issues.

Parámetros:
- status: "BUYABLE", "DISCOVERABLE". Vacío = todos.
- issue_severity: "ERROR", "WARNING". Vacío = todos.
- page_size: Resultados por página (max 20). Pagina automáticamente.
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_listing_issues": """Issues de calidad de un listing: errores, warnings, atributos afectados.

Parámetros:
- sku: SKU del producto (ej: "WB-500-SLV")
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_product_type_info": """Buscar product types o ver atributos válidos para un tipo de producto.

Si se da un product_type, descarga el schema JSON externo y extrae los atributos.
Si se dan keywords, busca tipos de producto que coincidan.

Parámetros:
- product_type: Tipo exacto (ej: "WATER_BOTTLE") para ver definición. Vacío = buscar.
- keywords: Palabras clave (ej: "water bottle", "water bottle")
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "update_listing_attribute": """Actualizar un atributo de un listing (título, bullets, descripción, keywords).

REQUIERE confirm=True para ejecutar. Sin confirmación devuelve un plan detallado.

Parámetros:
- sku: SKU del producto (ej: "WB-500-SLV")
- product_type: Tipo (ej: "WATER_BOTTLE"). Usar get_product_type_info para encontrarlo.
- attribute_name: "item_name", "bullet_point", "product_description", "generic_keyword"
- value: Nuevo valor. Para bullet_point usar JSON array: '["bullet1", "bullet2"]'
- language_tag: Idioma (default según marketplace, ej: "es_ES")
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.
- confirm: True para ejecutar. False = solo plan.""",

    "update_listing_batch": """Actualizar múltiples atributos de un listing de una vez.

REQUIERE confirm=True para ejecutar. Sin confirmación devuelve un plan detallado.

Parámetros:
- sku: SKU del producto (ej: "WB-500-SLV")
- product_type: Tipo (ej: "WATER_BOTTLE")
- updates: JSON con atributos. Ejemplo: {"item_name": "Título", "bullet_point": ["b1", "b2"]}
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.
- confirm: True para ejecutar. False = solo plan.""",

    # --- Fase 5: Reports ---
    "request_report": """Solicitar generación de un informe de Amazon. Proceso asíncrono.

Flujo: request_report → check_report (polling) → download_report.
Los informes tardan entre 30 seg y 10 min dependiendo del tipo.

Parámetros:
- report_type: Tipo (ej: "GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT", "GET_FBA_MYI_UNSUPPRESSED_INVENTORY_DATA")
- days_back: Días hacia atrás (default 30)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "check_report": """Estado de un informe solicitado: IN_QUEUE, IN_PROGRESS, DONE, FATAL.

Parámetros:
- report_id: ID devuelto por request_report
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "download_report": """Descargar contenido de un informe completado. Primero verifica que esté en DONE.

Parámetros:
- report_id: ID del informe (debe estar en estado DONE)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_search_terms": """Top keywords de búsqueda con click share y conversion share (Brand Analytics).

Requiere Brand Registry. Report asíncrono (1-5 min). Usa última semana completa.

Parámetros:
- days_back: Días hacia atrás (default 30). Se ajusta a última semana completa.
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_search_performance": """Rendimiento de tus ASINs en búsquedas: impresiones, clics, carrito, compras (Brand Analytics).

Requiere Brand Registry y lista de ASINs. Report asíncrono (1-5 min).

Parámetros:
- asins: ASINs separados por coma (ej: "B0XXXXXXX1,B0XXXXXXX2"). Máx ~10.
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_market_basket": """Productos que los clientes compran junto con los tuyos — cross-sell (Brand Analytics).

Requiere Brand Registry. Report asíncrono. Usa último mes completo.

Parámetros:
- days_back: Días hacia atrás (default 30). Se ajusta a último mes completo.
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_repeat_purchases": """Tasa de recompra por ASIN — fidelización (Brand Analytics).

Requiere Brand Registry. Report asíncrono. Usa último mes completo.

Parámetros:
- days_back: Días hacia atrás (default 30). Se ajusta a último mes completo.
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    # --- Fase 6: FBA Reports ---
    "get_fba_inventory": """Stock en FBA por SKU (vía report asíncrono, tarda 1-5 min).

Para datos en tiempo real sin espera, usar get_inventory.

Parámetros:
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_fba_returns": """Devoluciones FBA con motivo detallado (DEFECTIVE, CUSTOMER_RETURN) vía report asíncrono.

Complementa get_returns_summary (Finances) que solo da importes. Tarda 1-5 min.

Parámetros:
- days_back: Días hacia atrás (default 30)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_fba_fees_report": """Tarifas de almacenamiento FBA: actuales y de largo plazo (2 reports, 2-10 min).

Puede devolver CANCELLED si no hay datos de tarifas o si se solicita con menos de 4h de intervalo.

Parámetros:
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_restock_suggestions": """Recomendaciones de restock: qué SKUs reabastecer y cuántas unidades (report, 1-5 min).

Parámetros:
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    # --- Fase 7: Sales & Traffic ---
    "get_sales_and_traffic": """Métricas por ASIN: sesiones, page views, conversión, Buy Box %. Report asíncrono (1-5 min).

Para métricas rápidas sin desglose por ASIN, usar get_order_metrics.

Parámetros:
- days_back: Días hacia atrás (default 30)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    # --- Fase 8: Inventario ---
    "get_inventory": """Stock actual en FBA en tiempo real. Pagina automáticamente (devuelve TODOS los SKUs).

A diferencia de get_fba_inventory (report asíncrono), esto responde inmediatamente.

Parámetros:
- sku: SKU específico (ej: "WB-500-SLV"). Vacío = todos. Múltiples con coma (máx 50).
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    # --- Fase 9: Pricing ---
    "get_competitive_pricing": """Precios competitivos, Buy Box y rankings por ASIN. Máximo 20 ASINs.

Para ver TODAS las ofertas de vendedores de un ASIN individual, usar get_competitor_offers.

Parámetros:
- asins: ASINs separados por coma (ej: "B0XXXXXXX1,B0XXXXXXX2"). Máx 20.
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_competitor_offers": """TODAS las ofertas de vendedores para un ASIN: precio, FBA/FBM, quién tiene Buy Box.

Para análisis por keywords (buscar productos similares), usar analyze_competitor_prices.

Parámetros:
- asin: ASIN del producto
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    # --- Fase 10: A+ Content ---
    "list_aplus_content": """Listar documentos A+ Content de tu cuenta. Pagina automáticamente. Requiere Brand Registry.

Parámetros:
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_aplus_content": """Detalle de un documento A+ Content: módulos, textos, imágenes.

Parámetros:
- content_key: Content reference key (obtenido de list_aplus_content)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_aplus_asin_relations": """Ver qué ASINs usan un documento A+ Content específico.

Parámetros:
- content_key: Content reference key (obtenido de list_aplus_content)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    # --- Fase 11: Cross-marketplace ---
    "get_cross_marketplace_prices": """Ver precio de un SKU en todos los marketplaces europeos (estilo BIL).

Parámetros:
- sku: SKU del producto
- marketplaces: Códigos separados por coma (ej: "ES,DE,FR"). Vacío = todos EU.""",

    "update_marketplace_price": """Cambiar precio de un SKU en un marketplace específico.

REQUIERE confirm=True. Sin confirmación devuelve plan detallado.

Parámetros:
- sku: SKU del producto
- product_type: Tipo (ej: "WATER_BOTTLE")
- price: Nuevo precio (en moneda local del marketplace)
- marketplace: Código del marketplace destino (ej: "DE", "FR")
- confirm: True para ejecutar. False = solo plan.""",

    "sync_marketplace_prices": """Sincronizar precio a múltiples marketplaces (estilo BIL).

REQUIERE confirm=True. Aplica precio base con ajuste porcentual opcional.

Parámetros:
- sku: SKU del producto
- product_type: Tipo (ej: "WATER_BOTTLE")
- base_price: Precio base en EUR
- targets: Marketplaces destino (ej: "DE,FR,IT")
- adjustment_pct: Ajuste % (ej: 5.0 = +5%, -3.0 = -3%). Default 0.
- confirm: True para ejecutar. False = solo plan.""",

    # --- Fase 12: Competencia ---
    "analyze_competitor_prices": """Buscar productos similares y comparar precios, rankings y fulfillment.

Busca por keywords, obtiene precios competitivos, ordena por precio.

Parámetros:
- keywords: Términos (ej: "stainless steel water bottle 500ml")
- max_results: Máx productos (default 10, máx 20)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "compare_with_competitors": """Comparar tu producto con competidores: precio, ranking, ofertas.

Tu ASIN se excluye de la lista de competidores.

Parámetros:
- my_asin: Tu ASIN de referencia (ej: "B0XXXXXXX1")
- keywords: Términos para encontrar competidores (ej: "insulated water bottle 1L")
- max_results: Máx competidores (default 10, máx 20)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    # --- Fase 13: Restrictions ---
    "check_listing_restrictions": """Ver si puedes vender un ASIN en tu marketplace actual.

Parámetros:
- asin: ASIN del producto
- condition: "new_new", "used_acceptable". Vacío = todas.
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "check_expansion_eligibility": """Verificar si puedes vender un ASIN en otros marketplaces europeos.

Parámetros:
- asin: ASIN del producto
- marketplaces: Códigos separados por coma (ej: "DE,FR,IT,GB")""",

    # --- Fase 14: Feeds ---
    "bulk_update_prices": """Actualizar precios de múltiples SKUs via JSON_LISTINGS_FEED asíncrono.

REQUIERE confirm=True. El feed se procesa en 5-15 min. Usar check_feed para resultado.
Para 1 SKU en 1 marketplace, usar update_marketplace_price (más rápido).

Parámetros:
- updates: JSON array. Ejemplo: [{"sku": "WB-500-SLV", "price": 14.99, "product_type": "WATER_BOTTLE"}]
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.
- confirm: True para ejecutar. False = solo plan.""",

    "check_feed": """Estado y resultado de un feed (actualización masiva). Si DONE, descarga resultado.

Parámetros:
- feed_id: ID devuelto por bulk_update_prices
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    # --- Fase 15: Fulfillment Inbound ---
    "list_fba_shipments": """Ver envíos a FBA y su estado. Pagina automáticamente.

Parámetros:
- status: "WORKING", "SHIPPED", "RECEIVING", "IN_TRANSIT", "CLOSED". Vacío = todos.
- shipment_ids: IDs específicos separados por coma. Vacío = busca por fecha.
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_fba_shipment_items": """Items en un envío a FBA: SKU, cantidad enviada vs recibida. Pagina automáticamente.

Parámetros:
- shipment_id: ID del envío (ej: "FBA15LGQZWR2")
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "get_inbound_guidance": """Guía de envío a FBA por ASIN: elegibilidad, preparación requerida.

Parámetros:
- asins: ASINs separados por coma (ej: "B0XXXXXXX1,B0XXXXXXX2")
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    # --- Fase 16: Messaging ---
    "get_messaging_options": """Ver qué tipos de mensaje puedes enviar al comprador de un pedido.

Parámetros:
- order_id: ID del pedido (ej: "406-1234567-8901234")
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "send_buyer_message": """Enviar mensaje al comprador de un pedido.

REQUIERE confirm=True.

Parámetros:
- order_id: ID del pedido
- message_type: "confirm_delivery", "confirm_order", "unexpected_problem", "legal_disclosure", "negative_feedback_removal", "send_invoice"
- body: JSON con contenido del mensaje
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.
- confirm: True para ejecutar. False = solo plan.""",

    # --- Fase 17: Solicitations ---
    "check_review_eligibility": """Ver si puedes solicitar review para un pedido.

Amazon limita a 1 solicitud por pedido, entre 5 y 30 días después de la entrega.

Parámetros:
- order_id: ID del pedido
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "request_review": """Solicitar review de producto y feedback del vendedor.

REQUIERE confirm=True. IRREVERSIBLE: solo 1 vez por pedido (entre 5-30 días post-entrega).

Parámetros:
- order_id: ID del pedido
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.
- confirm: True para ejecutar. False = solo plan.""",

    # --- Fase 18: Invoices ---
    "get_invoices": """Obtener facturas, opcionalmente filtradas por pedido.

NOTA: Requiere rol de facturación especial. Puede devolver Unauthorized.

Parámetros:
- order_id: ID del pedido. Vacío = todas las facturas del periodo.
- days_back: Días hacia atrás (default 30)
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    "download_invoice": """Descargar documento de factura. Requiere acceso a Invoices API.

Parámetros:
- invoice_id: ID de la factura
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",

    # --- Fase 19: Sales API ---
    "get_order_metrics": """Métricas de ventas agregadas SIN esperar informes. Respuesta inmediata.

Alternativa rápida a get_sales_and_traffic (reports, minutos) y get_sales_summary (1 call/pedido).
No desglosa por producto — solo totales por intervalo.

Parámetros:
- days_back: Días hacia atrás (default 30)
- granularity: "Day", "Week" o "Month" (default "Day")
- marketplace: ES, DE, FR, IT, GB. Vacío = default .env.""",
}
