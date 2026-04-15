from __future__ import annotations

from typing import Any, Mapping

from generated.imgwire_generated.api.custom_domain_api import CustomDomainApi
from generated.imgwire_generated.models.custom_domain_create_schema import (
    CustomDomainCreateSchema,
)
from generated.imgwire_generated.models.custom_domain_schema import CustomDomainSchema

from imgwire.resources.base import BaseResource


class CustomDomainResource(BaseResource):
    def __init__(self, api_client) -> None:
        super().__init__(api_client)
        self._api = CustomDomainApi(api_client)

    def create(
        self, payload: CustomDomainCreateSchema | Mapping[str, Any]
    ) -> CustomDomainSchema:
        body = self._coerce_model(CustomDomainCreateSchema, payload)
        return self._call(lambda: self._api.custom_domain_create(body))

    def delete(self) -> dict[str, str | None]:
        return self._call(self._api.custom_domain_delete)

    def retrieve(self) -> CustomDomainSchema:
        return self._call(self._api.custom_domain_retrieve)

    def test_connection(self) -> dict[str, Any]:
        return self._call(self._api.custom_domain_test_connection)
