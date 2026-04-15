from __future__ import annotations

import time

import httpx

from imgwire.uploads.resolve import ResolvedUpload


def upload_bytes(
    upload_url: str,
    upload: ResolvedUpload,
    *,
    timeout: float,
    max_retries: int,
    backoff_factor: float,
) -> None:
    headers = {"Content-Length": str(upload.content_length)}
    if upload.mime_type:
        headers["Content-Type"] = upload.mime_type

    attempt = 0
    while True:
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.put(
                    upload_url, content=upload.content, headers=headers
                )
            response.raise_for_status()
            return
        except httpx.HTTPError:
            if attempt >= max_retries:
                raise
            time.sleep(backoff_factor * (2**attempt))
            attempt += 1
