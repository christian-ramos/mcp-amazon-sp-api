"""Wrapper sobre python-amazon-sp-api — re-exporta desde clients/."""

from .clients import AmazonClient, load_all_pages, throttle_retry

__all__ = ["AmazonClient", "throttle_retry", "load_all_pages"]
