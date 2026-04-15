from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Mapping, Optional, TypeVar

T = TypeVar("T")


def _parse_int(headers: Mapping[str, str], key: str) -> Optional[int]:
    value = headers.get(key)
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized in {"", "null", "none"}:
        return None
    return int(value)


@dataclass(frozen=True)
class Pagination:
    total_count: Optional[int]
    page: Optional[int]
    limit: Optional[int]
    prev_page: Optional[int]
    next_page: Optional[int]

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> "Pagination":
        return cls(
            total_count=_parse_int(headers, "X-Total-Count"),
            page=_parse_int(headers, "X-Page"),
            limit=_parse_int(headers, "X-Limit"),
            prev_page=_parse_int(headers, "X-Prev-Page"),
            next_page=_parse_int(headers, "X-Next-Page"),
        )


@dataclass(frozen=True)
class Page(Generic[T]):
    data: list[T]
    pagination: Pagination
