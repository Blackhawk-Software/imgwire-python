from __future__ import annotations

from typing import Any, Callable, Mapping, TypeVar

from pydantic import BaseModel

from generated.imgwire_generated.api_client import ApiClient
from generated.imgwire_generated.api_response import ApiResponse

from imgwire.pagination import Page, Pagination

T = TypeVar("T")
TModel = TypeVar("TModel", bound=BaseModel)


class BaseResource:
    def __init__(self, api_client: ApiClient) -> None:
        self._api_client = api_client

    @staticmethod
    def _coerce_model(
        model_type: type[TModel], value: TModel | Mapping[str, Any]
    ) -> TModel:
        if isinstance(value, model_type):
            return value
        return model_type.model_validate(value)

    @staticmethod
    def _to_page(response: ApiResponse[list[T]]) -> Page[T]:
        return Page(
            data=response.data,
            pagination=Pagination.from_headers(response.headers or {}),
        )

    @staticmethod
    def _call(func: Callable[[], T]) -> T:
        return func()
