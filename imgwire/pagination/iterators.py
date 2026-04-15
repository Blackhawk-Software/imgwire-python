from __future__ import annotations

from typing import Callable, Iterator, Optional, TypeVar

from imgwire.pagination.models import Page

T = TypeVar("T")


def iterate_pages(
    load_page: Callable[[int, Optional[int]], Page[T]],
    *,
    page: int = 1,
    limit: Optional[int] = None,
) -> Iterator[Page[T]]:
    next_page: Optional[int] = page
    current_limit = limit

    while next_page is not None:
        result = load_page(next_page, current_limit)
        yield result
        current_limit = result.pagination.limit or current_limit
        next_page = result.pagination.next_page


def iterate_items(pages: Iterator[Page[T]]) -> Iterator[T]:
    for page in pages:
        for item in page.data:
            yield item
