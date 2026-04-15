from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional

from imgwire.uploads.types import UploadLike


@dataclass(frozen=True)
class ResolvedUpload:
    content: bytes
    file_name: str
    mime_type: Optional[str]
    content_length: int


def resolve_upload_input(
    value: UploadLike,
    *,
    file_name: Optional[str] = None,
    mime_type: Optional[str] = None,
    content_length: Optional[int] = None,
) -> ResolvedUpload:
    if isinstance(value, str):
        path = Path(value)
        content = path.read_bytes()
        resolved_name = file_name or path.name
        resolved_mime_type = mime_type or mimetypes.guess_type(path.name)[0]
        return ResolvedUpload(
            content=content,
            file_name=resolved_name,
            mime_type=resolved_mime_type,
            content_length=content_length or len(content),
        )

    if isinstance(value, (bytes, bytearray)):
        content = bytes(value)
        resolved_name = file_name or "upload.bin"
        resolved_mime_type = mime_type or mimetypes.guess_type(resolved_name)[0]
        return ResolvedUpload(
            content=content,
            file_name=resolved_name,
            mime_type=resolved_mime_type,
            content_length=content_length or len(content),
        )

    content = _read_file_object(value)
    resolved_name = file_name or _infer_file_name(value)
    resolved_mime_type = mime_type or mimetypes.guess_type(resolved_name)[0]
    return ResolvedUpload(
        content=content,
        file_name=resolved_name,
        mime_type=resolved_mime_type,
        content_length=content_length or len(content),
    )


def _read_file_object(value: BinaryIO) -> bytes:
    content = value.read()
    if isinstance(content, str):
        content = content.encode("utf8")
    return content


def _infer_file_name(value: BinaryIO) -> str:
    candidate = getattr(value, "name", None)
    if isinstance(candidate, str) and candidate:
        return Path(candidate).name
    return "upload.bin"
