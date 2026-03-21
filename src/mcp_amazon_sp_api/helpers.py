"""Funciones compartidas entre todos los módulos de tools."""

import json
import logging
import sys
from datetime import datetime, timedelta, timezone

from .config import load_config
from .sp_client import AmazonClient

# Logging a stderr (NUNCA stdout — corrompe el protocolo MCP stdio)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_amazon_sp_api")


def to_json(obj: object) -> str:
    """JSON formateado con soporte para caracteres españoles."""
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)


def iso_now() -> str:
    """Timestamp actual en formato ISO8601 compatible con SP-API producción."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_days_ago(days: int) -> str:
    """Timestamp de hace N días en formato ISO8601 compatible con SP-API producción."""
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_client(marketplace: str = "") -> AmazonClient:
    """Crea cliente SP-API. Se llama en cada tool para evitar estado global."""
    config = load_config()
    if marketplace:
        from dataclasses import replace
        config = replace(config, marketplace=marketplace.upper())
    return AmazonClient(config)
