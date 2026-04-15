from __future__ import annotations

import unittest

from imgwire.pagination import Page, Pagination, iterate_items, iterate_pages


class PaginationTests(unittest.TestCase):
    def test_pagination_headers_are_parsed(self) -> None:
        pagination = Pagination.from_headers(
            {
                "X-Total-Count": "10",
                "X-Page": "2",
                "X-Limit": "3",
                "X-Prev-Page": "1",
                "X-Next-Page": "3",
            }
        )

        self.assertEqual(pagination.total_count, 10)
        self.assertEqual(pagination.page, 2)
        self.assertEqual(pagination.limit, 3)
        self.assertEqual(pagination.prev_page, 1)
        self.assertEqual(pagination.next_page, 3)

    def test_iterators_follow_next_page_headers(self) -> None:
        pages = {
            1: Page(data=[1, 2], pagination=Pagination(4, 1, 2, None, 2)),
            2: Page(data=[3, 4], pagination=Pagination(4, 2, 2, 1, None)),
        }

        seen_pages = list(
            iterate_pages(lambda page, limit: pages[page], page=1, limit=2)
        )
        seen_items = list(iterate_items(iter(seen_pages)))

        self.assertEqual(len(seen_pages), 2)
        self.assertEqual(seen_items, [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
