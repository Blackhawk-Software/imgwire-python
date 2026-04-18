from __future__ import annotations

import unittest
from datetime import datetime, timezone

from imgwire.images import ImgwireImage, extend_image


def make_image() -> ImgwireImage:
    return extend_image(
        {
            "can_upload": False,
            "cdn_url": "https://cdn.imgwire.dev/example",
            "created_at": datetime(2026, 4, 14, tzinfo=timezone.utc),
            "custom_metadata": {},
            "deleted_at": None,
            "environment_id": None,
            "exif_data": {},
            "extension": "jpg",
            "hash_sha256": None,
            "height": 100,
            "id": "img_1",
            "idempotency_key": None,
            "is_directly_deliverable": True,
            "mime_type": "image/jpeg",
            "original_filename": "example.jpg",
            "processed_metadata_at": None,
            "purpose": None,
            "size_bytes": 100,
            "status": "READY",
            "updated_at": datetime(2026, 4, 14, tzinfo=timezone.utc),
            "upload_token_id": None,
            "width": 100,
        }
    )


class ImageUrlBuilderTests(unittest.TestCase):
    def test_builds_transformed_urls_with_presets_and_canonical_params(self) -> None:
        image = make_image()

        self.assertEqual(
            image.url(preset="thumbnail", bg="#ffffff", h=150, rot=90, w=150),
            "https://cdn.imgwire.dev/example@thumbnail"
            "?background=ffffff&height=150&rotate=90&width=150",
        )

    def test_normalizes_boolean_behavior(self) -> None:
        image = make_image()

        self.assertEqual(
            image.url(enlarge=False, strip_metadata=True),
            "https://cdn.imgwire.dev/example?strip_metadata=true",
        )

    def test_accepts_auto_output_format(self) -> None:
        image = make_image()

        self.assertEqual(
            image.url(format="auto"),
            "https://cdn.imgwire.dev/example?format=auto",
        )

    def test_rejects_duplicate_aliases_for_same_canonical_rule(self) -> None:
        image = make_image()

        with self.assertRaisesRegex(ValueError, "Duplicate transformation rule: width"):
            image.url(width=100, w=200)

    def test_rejects_invalid_worker_transformation_values(self) -> None:
        image = make_image()

        with self.assertRaisesRegex(
            ValueError, "Invalid transformation rule value for rotate"
        ):
            image.url(rotate=45)


if __name__ == "__main__":
    unittest.main()
