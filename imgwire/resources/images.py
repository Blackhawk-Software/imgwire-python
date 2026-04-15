from __future__ import annotations

from typing import Any, BinaryIO, Iterator, Mapping, Optional, Union

from generated.imgwire_generated.api.images_api import ImagesApi
from generated.imgwire_generated.models.bulk_delete_images_schema import (
    BulkDeleteImagesSchema,
)
from generated.imgwire_generated.models.image_download_job_create_schema import (
    ImageDownloadJobCreateSchema,
)
from generated.imgwire_generated.models.image_download_job_schema import (
    ImageDownloadJobSchema,
)
from generated.imgwire_generated.models.image_schema import ImageSchema
from generated.imgwire_generated.models.standard_upload_create_schema import (
    StandardUploadCreateSchema,
)
from generated.imgwire_generated.models.standard_upload_response_schema import (
    StandardUploadResponseSchema,
)
from generated.imgwire_generated.models.upload_token_create_response_schema import (
    UploadTokenCreateResponseSchema,
)

from imgwire.client.options import ImgwireClientOptions
from imgwire.pagination import Page, iterate_pages, iterate_items
from imgwire.resources.base import BaseResource
from imgwire.uploads import ResolvedUpload, resolve_upload_input, upload_bytes
from imgwire.uploads.types import UploadLike


class ImagesResource(BaseResource):
    def __init__(self, api_client, options: ImgwireClientOptions) -> None:
        super().__init__(api_client)
        self._api = ImagesApi(api_client)
        self._options = options

    def bulk_delete(
        self, payload: BulkDeleteImagesSchema | Mapping[str, Any]
    ) -> dict[str, Optional[str]]:
        body = self._coerce_model(BulkDeleteImagesSchema, payload)
        return self._call(lambda: self._api.images_bulk_delete(body))

    def create(
        self,
        payload: StandardUploadCreateSchema | Mapping[str, Any],
        *,
        upload_token: Optional[str] = None,
    ) -> StandardUploadResponseSchema:
        body = self._coerce_model(StandardUploadCreateSchema, payload)
        return self._call(
            lambda: self._api.images_create(body, upload_token=upload_token)
        )

    def create_bulk_download_job(
        self, payload: ImageDownloadJobCreateSchema | Mapping[str, Any]
    ) -> ImageDownloadJobSchema:
        body = self._coerce_model(ImageDownloadJobCreateSchema, payload)
        return self._call(lambda: self._api.images_create_bulk_download_job(body))

    def create_upload_token(self) -> UploadTokenCreateResponseSchema:
        return self._call(self._api.images_create_upload_token)

    def delete(self, image_id: str) -> dict[str, Optional[str]]:
        return self._call(lambda: self._api.images_delete(image_id))

    def list(
        self, *, page: Optional[int] = None, limit: Optional[int] = None
    ) -> Page[ImageSchema]:
        response = self._call(
            lambda: self._api.images_list_with_http_info(limit=limit, page=page)
        )
        return self._to_page(response)

    def list_pages(
        self, *, page: int = 1, limit: Optional[int] = None
    ) -> Iterator[Page[ImageSchema]]:
        return iterate_pages(
            lambda current_page, current_limit: self.list(
                page=current_page, limit=current_limit
            ),
            page=page,
            limit=limit,
        )

    def list_all(
        self, *, page: int = 1, limit: Optional[int] = None
    ) -> Iterator[ImageSchema]:
        return iterate_items(self.list_pages(page=page, limit=limit))

    def retrieve(self, image_id: str) -> ImageSchema:
        return self._call(lambda: self._api.images_retrieve(image_id))

    def retrieve_bulk_download_job(
        self, image_download_job_id: str
    ) -> ImageDownloadJobSchema:
        return self._call(
            lambda: self._api.images_retrieve_bulk_download_job(image_download_job_id)
        )

    def upload(
        self,
        file: UploadLike,
        *,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        content_length: Optional[int] = None,
        custom_metadata: Optional[dict[str, Any]] = None,
        hash_sha256: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> ImageSchema:
        resolved = resolve_upload_input(
            file,
            file_name=file_name,
            mime_type=mime_type,
            content_length=content_length,
        )
        created = self.create(
            _build_standard_upload_payload(
                resolved, custom_metadata, hash_sha256, idempotency_key, purpose
            )
        )
        upload_bytes(
            created.upload_url,
            resolved,
            timeout=self._options.timeout,
            max_retries=self._options.max_retries,
            backoff_factor=self._options.backoff_factor,
        )
        return created.image


def _build_standard_upload_payload(
    resolved: ResolvedUpload,
    custom_metadata: Optional[dict[str, Any]],
    hash_sha256: Optional[str],
    idempotency_key: Optional[str],
    purpose: Optional[str],
) -> StandardUploadCreateSchema:
    return StandardUploadCreateSchema(
        content_length=resolved.content_length,
        custom_metadata=custom_metadata,
        file_name=resolved.file_name,
        hash_sha256=hash_sha256,
        idempotency_key=idempotency_key,
        mime_type=resolved.mime_type,
        purpose=purpose,
    )
