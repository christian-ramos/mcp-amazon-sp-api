"""Tools: A+ Content."""

from ..helpers import get_client, logger, to_json


def list_aplus_content(marketplace: str = "") -> str:
    """Listar documentos A+ Content de tu cuenta."""
    try:
        client = get_client(marketplace)
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
        return to_json({
            "totalDocuments": len(result),
            "documents": result,
        })
    except Exception as e:
        logger.error("Error en list_aplus_content: %s", e)
        return to_json({"error": str(e)})

def get_aplus_content(content_key: str, marketplace: str = "") -> str:
    """Detalle de un documento A+ Content."""
    try:
        client = get_client(marketplace)
        doc = client.get_content_document(content_key)
        return to_json(doc)
    except Exception as e:
        logger.error("Error en get_aplus_content: %s", e)
        return to_json({"error": str(e)})

def get_aplus_asin_relations(content_key: str, marketplace: str = "") -> str:
    """ASINs asociados a un documento A+ Content."""
    try:
        client = get_client(marketplace)
        asins = client.get_content_asin_relations(content_key)
        return to_json({
            "contentReferenceKey": content_key,
            "totalAsins": len(asins),
            "asins": asins,
        })
    except Exception as e:
        logger.error("Error en get_aplus_asin_relations: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(list_aplus_content)
    mcp.tool()(get_aplus_content)
    mcp.tool()(get_aplus_asin_relations)
