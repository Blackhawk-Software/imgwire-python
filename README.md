# imgwire-python

`imgwire-python` is the Python server-side SDK for imgwire.

It consumes the shared `@imgwire/codegen-core` shaping pipeline, uses OpenAPI Generator for the disposable base client under `generated/`, and exposes Python-specific ergonomics from the stable `imgwire/` package.

## Installation

```bash
pip install imgwire
```

For local development from this repository:

```bash
make install-py
. .venv/bin/activate
python
```

## Usage

```python
from imgwire import ImgwireClient

client = ImgwireClient(api_key="sk_...")

page = client.images.list(page=1, limit=25)
print(page.data)
print(page.pagination)
print(page.data[0].url(width=300, height=300))

for page in client.images.list_pages(limit=25):
    print(page.data)

for image in client.images.list_all(limit=25):
    print(image.id)
    print(image.url(preset="small"))
```

## Uploads

The upload helper accepts file paths, file-like objects, and bytes.

```python
client.images.upload("file.jpg")
client.images.upload(open("file.jpg", "rb"))
client.images.upload(b"raw-bytes", file_name="file.jpg", mime_type="image/jpeg")
```

Returned image objects expose `image.url(...)` so you can generate CDN transformation URLs directly from SDK responses:

```python
image = client.images.retrieve("img_123")

thumbnail_url = image.url(
    preset="thumbnail",
    width=300,
    height=300,
    format="webp",
    quality=80,
)

print(thumbnail_url)
```

## Generation

Install tooling:

```bash
make install
```

Regenerate the checked-in artifacts:

```bash
make generate
```

Verify that generated artifacts are current:

```bash
make verify-generated
```

## Development

Run Python tests:

```bash
make test
```

Build the package:

```bash
make build
```

Common local workflows:

```bash
make help
make format
make format-py
make clean
make ci
```
