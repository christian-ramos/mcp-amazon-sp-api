"""Fixtures compartidos para tests de MCP tools."""

import importlib
import json
from contextlib import ExitStack
from unittest.mock import patch, MagicMock

import pytest

from mcp_amazon_sp_api import helpers, server
from mcp_amazon_sp_api.tools import PACKAGE_REGISTRY

# Importar todos los tool modules para parchear get_client en cada uno
_TOOL_MODULES = []


def _ensure_all_packages_loaded():
    """Carga todos los paquetes de tools para que los tests puedan importar las funciones."""
    for name, info in PACKAGE_REGISTRY.items():
        module = importlib.import_module(info.module)
        _TOOL_MODULES.append(module)
        if name not in server._loaded_packages:
            module.register(server.mcp)
            server._loaded_packages.add(name)


_ensure_all_packages_loaded()


def parse(result: str) -> dict | list:
    return json.loads(result)


@pytest.fixture(autouse=True)
def mock_client(env_credentials):
    """Mockea get_client en helpers y en cada tool module."""
    mock = MagicMock()
    with ExitStack() as stack:
        stack.enter_context(patch.object(helpers, "get_client", return_value=mock))
        for module in _TOOL_MODULES:
            if hasattr(module, "get_client"):
                stack.enter_context(patch.object(module, "get_client", return_value=mock))
        yield mock
