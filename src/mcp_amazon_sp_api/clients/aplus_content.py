"""Cliente de A+ Content API — lectura de contenido A+."""

import logging

from sp_api.api import AplusContent
from sp_api.base import SellingApiException

from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class AplusContentClient(BaseClient):

    def _aplus_api(self) -> AplusContent:
        return AplusContent(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def search_content_documents(self) -> list[dict]:
        """Lista todos los documentos A+ del vendedor."""
        all_docs: list[dict] = []
        page_token = None

        while True:
            kwargs: dict = {"marketplaceId": self._marketplace_id}
            if page_token:
                kwargs["pageToken"] = page_token

            try:
                resp = self._aplus_api().search_content_documents(**kwargs)
                payload = resp.payload or {}
                docs = payload.get("contentMetadataRecords", [])
                all_docs.extend(docs)
                page_token = payload.get("nextPageToken")
                if not page_token:
                    break
            except SellingApiException as e:
                if getattr(e, "code", None) == 429:
                    raise
                logger.error("Error buscando documentos A+: %s", e)
                raise RuntimeError(f"Error SP-API al buscar documentos A+: {e}") from e

        return all_docs

    @throttle_retry()
    def get_content_document(self, content_reference_key: str) -> dict:
        """Lee el contenido de un documento A+."""
        try:
            resp = self._aplus_api().get_content_document(
                content_reference_key,
                marketplaceId=self._marketplace_id,
                includedDataSet=["CONTENTS", "METADATA"],
            )
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo documento A+ %s: %s", content_reference_key, e)
            raise RuntimeError(
                f"Error SP-API al obtener documento A+ {content_reference_key}: {e}"
            ) from e

    @throttle_retry()
    def get_content_asin_relations(self, content_reference_key: str) -> list[dict]:
        """Lista los ASINs asociados a un documento A+."""
        try:
            resp = self._aplus_api().list_content_document_asin_relations(
                content_reference_key,
                marketplaceId=self._marketplace_id,
            )
            payload = resp.payload or {}
            return payload.get("asinMetadataSet", [])
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo ASINs de A+ %s: %s", content_reference_key, e)
            raise RuntimeError(
                f"Error SP-API al obtener ASINs de A+ {content_reference_key}: {e}"
            ) from e
