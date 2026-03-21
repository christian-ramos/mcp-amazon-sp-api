"""Wrapper sobre python-amazon-sp-api — re-exporta desde clients/."""

from .clients import AmazonClient, throttle_retry, load_all_pages

__all__ = ["AmazonClient", "throttle_retry", "load_all_pages"]
