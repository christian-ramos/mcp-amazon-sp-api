"""Clase base y decoradores compartidos por todos los clientes SP-API."""

import functools
import logging
import time

from sp_api.base import Marketplaces, SellingApiException

from ..config import SpApiConfig

logger = logging.getLogger(__name__)


def throttle_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Reintenta ante throttling (HTTP 429) con backoff exponencial."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except SellingApiException as e:
                    if getattr(e, "code", None) == 429 and attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning("Throttled en %s, reintentando en %.1fs…", func.__name__, delay)
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator


def load_all_pages(func):
    """Paginación automática: acumula resultados de todas las páginas."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        all_items = []
        next_token = None
        while True:
            kwargs["next_token"] = next_token
            result, next_token = func(*args, **kwargs)
            all_items.extend(result)
            if not next_token:
                break
        return all_items
    return wrapper


class BaseClient:
    """Base con credenciales y marketplace compartidos."""

    def __init__(self, config: SpApiConfig):
        self._credentials = {
            "refresh_token": config.refresh_token,
            "lwa_app_id": config.lwa_app_id,
            "lwa_client_secret": config.lwa_client_secret,
        }
        self._marketplace = getattr(Marketplaces, config.marketplace)
        self._marketplace_id = config.marketplace_id
        self._currency = config.currency
        self._seller_id = config.seller_id
        self._language_tag = config.language_tag
