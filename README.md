# `imgwire`

[![PyPI version](https://img.shields.io/pypi/v/imgwire.svg)](https://pypi.org/project/imgwire/)
[![Python versions](https://img.shields.io/pypi/pyversions/imgwire.svg)](https://pypi.org/project/imgwire/)
[![CI](https://github.com/Blackhawk-Software/imgwire-python/actions/workflows/ci.yml/badge.svg)](https://github.com/Blackhawk-Software/imgwire-python/actions/workflows/ci.yml)
[![Release](https://github.com/Blackhawk-Software/imgwire-python/actions/workflows/release.yml/badge.svg)](https://github.com/Blackhawk-Software/imgwire-python/actions/workflows/release.yml)

`imgwire` is the server-side Python SDK for the imgwire API.

Use it in backend services, jobs, and server runtimes to authenticate with a Server API Key, upload files from Python paths, file objects, or bytes, manage server-side resources, and call the imgwire API without hand-writing request plumbing.

## Installation

```bash
pip install imgwire
```

## Quick Start

```python
from imgwire import ImgwireClient

client = ImgwireClient(api_key="sk_...")

image = client.images.upload("hero.jpg")

print(image.id)
print(image.url(preset="thumbnail"))
```

## Client Setup

Create a client with your server key:

```python
from imgwire import ImgwireClient

client = ImgwireClient(api_key="sk_...")
```

Optional configuration:

```python
client = ImgwireClient(
    api_key="sk_...",
    base_url="https://api.imgwire.dev",
    environment_id="env_123",
    timeout=10.0,
    max_retries=2,
    backoff_factor=0.25,
)
```

## Resources

The current handwritten SDK surface exposes these grouped resources:

- `client.images`
- `client.custom_domain`
- `client.cors_origins`
- `client.metrics`

### `client.images`

Image operations and upload workflows.

Returned image records expose `image.url(...)` so your backend can generate imgwire transformation URLs without reimplementing CDN path and query rules.

Supported methods:

- `list(page=None, limit=None)`
- `list_pages(page=1, limit=None)`
- `list_all(page=1, limit=None)`
- `retrieve(image_id)`
- `create(body, upload_token=None)`
- `upload(file, file_name=None, mime_type=None, content_length=None, ...)`
- `create_upload_token()`
- `create_bulk_download_job(body)`
- `retrieve_bulk_download_job(image_download_job_id)`
- `bulk_delete(body)`
- `delete(image_id)`

List images:

```python
page = client.images.list(limit=25, page=1)

print(page.data)
print(page.pagination.total_count)
```

Iterate page-by-page:

```python
for page in client.images.list_pages(limit=100):
    print(page.pagination.page, len(page.data))
```

Iterate every image record:

```python
for image in client.images.list_all(limit=100):
    print(image.id)
    print(image.url(preset="small"))
```

Retrieve an image by id:

```python
image = client.images.retrieve("img_123")

transformed_url = image.url(
    width=300,
    height=300,
)
```

Create a standard upload intent directly:

```python
upload = client.images.create(
    {
        "file_name": "hero.png",
        "mime_type": "image/png",
        "content_length": 1024,
    }
)

print(upload.upload_url)
```

Upload from a file path:

```python
image = client.images.upload("hero.jpg")
```

Upload from a file object:

```python
with open("hero.jpg", "rb") as handle:
    image = client.images.upload(handle, mime_type="image/jpeg")

print(
    image.url(
        width=1200,
        height=800,
        format="auto",
        quality=80,
    )
)
```

Upload from bytes:

```python
image = client.images.upload(
    image_bytes,
    file_name="hero.png",
    mime_type="image/png",
)
```

Create an upload token:

```python
upload_token = client.images.create_upload_token()

print(upload_token.token)
```

Create and inspect a bulk download job:

```python
job = client.images.create_bulk_download_job(
    {
        "image_ids": ["img_123", "img_456"],
    }
)

refreshed = client.images.retrieve_bulk_download_job(job.id)
```

Delete multiple images:

```python
client.images.bulk_delete(
    {
        "image_ids": ["img_123", "img_456"],
    }
)
```

### Image URL Transformations

Image-returning endpoints return `ImgwireImage` records with a `url(...)` helper:

```python
image = client.images.retrieve("img_123")

thumbnail_url = image.url(
    preset="thumbnail",
    width=300,
    height=300,
    format="auto",
    quality=80,
)

print(thumbnail_url)
```

The SDK validates and normalizes transformation values to match the CDN worker. Query params are emitted using canonical rule names and sorted deterministically.

Examples:

```python
image.url(bg="#ffffff", w=150, h=150, rot=90)
image.url(strip_metadata=True, enlarge=False)
image.url(crop="300:300:ce", gravity="ce")
```

### `client.custom_domain`

Custom domain management for your imgwire environment.

Supported methods:

- `create(body)`
- `retrieve()`
- `test_connection()`
- `delete()`

Example:

```python
client.custom_domain.create(
    {
        "hostname": "images.example.com",
    }
)

custom_domain = client.custom_domain.retrieve()
verification = client.custom_domain.test_connection()
```

### `client.cors_origins`

CORS origin management for server-controlled environments.

Supported methods:

- `list(page=None, limit=None)`
- `list_pages(page=1, limit=None)`
- `list_all(page=1, limit=None)`
- `create(body)`
- `retrieve(cors_origin_id)`
- `update(cors_origin_id, body)`
- `delete(cors_origin_id)`

Example:

```python
created = client.cors_origins.create(
    {
        "pattern": "app.example.com",
    }
)

origins = client.cors_origins.list(limit=50, page=1)

client.cors_origins.update(
    created.id,
    {
        "pattern": "dashboard.example.com",
    },
)

for origin in client.cors_origins.list_all(limit=50):
    print(origin.pattern)
```

### `client.metrics`

Server-side metrics endpoints for dashboards, reporting, and internal tooling.

Supported methods:

- `get_datasets(date_start=None, date_end=None, interval=None, tz=None)`
- `get_stats(date_start=None, date_end=None, interval=None, tz=None)`

Example:

```python
from datetime import datetime, timezone

datasets = client.metrics.get_datasets(
    date_start=datetime(2026, 4, 1, tzinfo=timezone.utc),
    date_end=datetime(2026, 4, 15, tzinfo=timezone.utc),
    interval="DAILY",
    tz="America/Chicago",
)

stats = client.metrics.get_stats(
    date_start=datetime(2026, 4, 1, tzinfo=timezone.utc),
    date_end=datetime(2026, 4, 15, tzinfo=timezone.utc),
    interval="DAILY",
    tz="America/Chicago",
)
```

## Response Shape Notes

- List endpoints exposed through handwritten wrappers return `{ data, pagination }`-style objects via `Page(data=..., pagination=...)`.
- `list_pages()` yields paginated result objects across pages.
- `list_all()` yields individual items across every page.
- Image-returning methods return image records extended with `url(...)` for transformation URL generation.
- Upload helpers return the created image record after the presigned upload completes.

## Development

For local development from this repository:

```bash
make install-py
. .venv/bin/activate
python
```

Common local workflows:

```bash
make help
make format
make format-py
make release-set VERSION=0.2.0
make clean
make ci
```

## Generation

This repository is generated from the imgwire API contract and then extended with handwritten Python SDK code.

The pipeline is:

1. acquire the raw OpenAPI document
2. shape it with `@imgwire/codegen-core` for `target: "python"`
3. generate a disposable base client with OpenAPI Generator
4. apply deterministic post-processing
5. layer in handwritten SDK code from `imgwire/`

Set `OPENAPI_SOURCE` to override the spec source. By default:

- local/dev uses `http://localhost:8000/openapi.json`
- release-oriented generation can use `https://api.imgwire.dev/openapi.json` by setting `OPENAPI_RELEASE=true`

```bash
make install
make generate
make verify-generated
```

This writes:

- `openapi/raw.openapi.json`
- `openapi/sdk.openapi.json`
- `generated/`
- `CODEGEN_VERSION`

Generated code lives in `generated/` and should not be edited by hand. Durable SDK code lives in `imgwire/`.

## Versioning

The PyPI package version lives in `pyproject.toml`, and the repo tooling version in `package.json` is kept in sync with it.

Set a new version manually with:

```bash
make release-set VERSION=0.2.0
```
