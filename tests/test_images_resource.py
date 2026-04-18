from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from generated.imgwire_generated.api_response import ApiResponse
from generated.imgwire_generated.models.standard_upload_response_schema import (
    StandardUploadResponseSchema,
)

from imgwire.client.options import ImgwireClientOptions
from imgwire.images import ImgwireImage
from imgwire.resources.images import ImagesResource


def make_image_payload() -> dict[str, object]:
    return {
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


class FakeImagesApi:
    def __init__(self) -> None:
        self.image_payload = make_image_payload()

    def images_create(self, body, upload_token=None) -> StandardUploadResponseSchema:
        return StandardUploadResponseSchema(
            image=self.image_payload,
            upload_url="https://uploads.imgwire.dev/example",
        )

    def images_list_with_http_info(
        self, limit=None, page=None
    ) -> ApiResponse[list[dict[str, object]]]:
        return ApiResponse(
            status_code=200,
            headers={
                "X-Total-Count": "1",
                "X-Page": str(page or 1),
                "X-Limit": str(limit or 25),
            },
            data=[self.image_payload],
            raw_data=b"[]",
        )

    def images_retrieve(self, image_id: str) -> dict[str, object]:
        return self.image_payload


class ImagesResourceTests(unittest.TestCase):
    def make_resource(self) -> ImagesResource:
        resource = ImagesResource(
            api_client=object(),
            options=ImgwireClientOptions(api_key="sk_test"),
        )
        resource._api = FakeImagesApi()
        return resource

    def test_create_wraps_response_image(self) -> None:
        resource = self.make_resource()

        created = resource.create({"file_name": "example.jpg"})

        self.assertIsInstance(created.image, ImgwireImage)
        self.assertEqual(
            created.image.url(width=200),
            "https://cdn.imgwire.dev/example?width=200",
        )

    def test_list_wraps_page_data(self) -> None:
        resource = self.make_resource()

        page = resource.list(page=1, limit=25)

        self.assertIsInstance(page.data[0], ImgwireImage)
        self.assertEqual(
            page.data[0].url(preset="small"),
            "https://cdn.imgwire.dev/example@small",
        )

    def test_retrieve_wraps_returned_image(self) -> None:
        resource = self.make_resource()

        image = resource.retrieve("img_1")

        self.assertIsInstance(image, ImgwireImage)
        self.assertEqual(
            image.url(bg="#ffffff", w=100),
            "https://cdn.imgwire.dev/example?background=ffffff&width=100",
        )

    def test_upload_returns_extended_image(self) -> None:
        resource = self.make_resource()

        with patch("imgwire.resources.images.upload_bytes"):
            image = resource.upload(
                b"payload", file_name="example.jpg", mime_type="image/jpeg"
            )

        self.assertIsInstance(image, ImgwireImage)
        self.assertEqual(
            image.url(width=150, height=150),
            "https://cdn.imgwire.dev/example?height=150&width=150",
        )


if __name__ == "__main__":
    unittest.main()
