from __future__ import annotations

from typing import Any, Iterator, Mapping, Optional

from generated.imgwire_generated.api.cors_origins_api import CorsOriginsApi
from generated.imgwire_generated.models.cors_origin_create_schema import (
    CorsOriginCreateSchema,
)
from generated.imgwire_generated.models.cors_origin_schema import CorsOriginSchema
from generated.imgwire_generated.models.cors_origin_update_schema import (
    CorsOriginUpdateSchema,
)

from imgwire.pagination import Page, iterate_items, iterate_pages
from imgwire.resources.base import BaseResource


class CorsOriginsResource(BaseResource):
    def __init__(self, api_client) -> None:
        super().__init__(api_client)
        self._api = CorsOriginsApi(api_client)

    def create(
        self, payload: CorsOriginCreateSchema | Mapping[str, Any]
    ) -> CorsOriginSchema:
        body = self._coerce_model(CorsOriginCreateSchema, payload)
        return self._call(lambda: self._api.cors_origins_create(body))

    def delete(self, cors_origin_id: str) -> dict[str, Optional[str]]:
        return self._call(lambda: self._api.cors_origins_delete(cors_origin_id))

    def list(
        self, *, page: Optional[int] = None, limit: Optional[int] = None
    ) -> Page[CorsOriginSchema]:
        response = self._call(
            lambda: self._api.cors_origins_list_with_http_info(limit=limit, page=page)
        )
        return self._to_page(response)

    def list_pages(
        self, *, page: int = 1, limit: Optional[int] = None
    ) -> Iterator[Page[CorsOriginSchema]]:
        return iterate_pages(
            lambda current_page, current_limit: self.list(
                page=current_page, limit=current_limit
            ),
            page=page,
            limit=limit,
        )

    def list_all(
        self, *, page: int = 1, limit: Optional[int] = None
    ) -> Iterator[CorsOriginSchema]:
        return iterate_items(self.list_pages(page=page, limit=limit))

    def retrieve(self, cors_origin_id: str) -> CorsOriginSchema:
        return self._call(lambda: self._api.cors_origins_retrieve(cors_origin_id))

    def update(
        self, cors_origin_id: str, payload: CorsOriginUpdateSchema | Mapping[str, Any]
    ) -> CorsOriginSchema:
        body = self._coerce_model(CorsOriginUpdateSchema, payload)
        return self._call(lambda: self._api.cors_origins_update(cors_origin_id, body))
