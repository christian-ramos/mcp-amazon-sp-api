"""MCP Server — entry point. Registra todas las tools al arrancar."""

import importlib
import logging
import sys

from mcp.server.fastmcp import FastMCP

from .tool_docs import TOOL_DOCS
from .tools import PACKAGE_REGISTRY

# Logging a stderr (NUNCA stdout — corrompe el protocolo MCP stdio)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

mcp = FastMCP("amazon-sp-api")

_loaded_packages: set[str] = set()


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("tool-docs://all")
def get_all_tool_docs() -> str:
    """Documentación detallada de todas las tools disponibles."""
    lines = []
    for name, doc in TOOL_DOCS.items():
        lines.append(f"## {name}\n{doc}\n")
    return "\n".join(lines)


@mcp.resource("tool-docs://{tool_name}")
def get_tool_doc(tool_name: str) -> str:
    """Documentación detallada de una tool específica."""
    doc = TOOL_DOCS.get(tool_name)
    if doc:
        return f"## {tool_name}\n{doc}"
    return f"Tool '{tool_name}' no encontrada. Tools disponibles: {', '.join(TOOL_DOCS.keys())}"


# ---------------------------------------------------------------------------
# Registrar todos los paquetes de tools al arrancar
# ---------------------------------------------------------------------------

def _register_all_packages():
    for name, info in PACKAGE_REGISTRY.items():
        module = importlib.import_module(info.module)
        module.register(mcp)
        _loaded_packages.add(name)
    logger.info("Registrados %d paquetes (%d tools)",
                len(PACKAGE_REGISTRY),
                sum(len(p.tool_names) for p in PACKAGE_REGISTRY.values()))


_register_all_packages()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    mcp.run()


if __name__ == "__main__":
    main()
