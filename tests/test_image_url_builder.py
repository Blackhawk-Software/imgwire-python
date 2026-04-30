from __future__ import annotations

import unittest
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

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
            "https://cdn.imgwire.dev/example?enlarge=false&strip_metadata=true",
        )

    def test_accepts_auto_output_format(self) -> None:
        image = make_image()

        self.assertEqual(
            image.url(format="auto"),
            "https://cdn.imgwire.dev/example?format=auto",
        )

    def test_supports_encoding_transform_updates(self) -> None:
        image = make_image()

        self.assertEqual(
            image.url(chroma_subsampling="4:4:4", progressive="auto", quality="auto"),
            "https://cdn.imgwire.dev/example?chroma_subsampling=4%3A4%3A4"
            "&progressive=auto&quality=auto",
        )
        self.assertEqual(
            image.url(chroma_subsampling="AUTO", progressive=True, q=85),
            "https://cdn.imgwire.dev/example?chroma_subsampling=auto"
            "&progressive=true&quality=85",
        )
        self.assertEqual(
            image.url(chroma_subsampling="4:2:2", progressive=False),
            "https://cdn.imgwire.dev/example?chroma_subsampling=4%3A2%3A2"
            "&progressive=false",
        )

    def test_rejects_duplicate_aliases_for_same_canonical_rule(self) -> None:
        image = make_image()

        with self.assertRaisesRegex(ValueError, "Duplicate transformation rule: width"):
            image.url(width=100, w=200)

    def test_ignores_invalid_worker_transformation_values(self) -> None:
        image = make_image()

        self.assertEqual(
            image.url(width=800, pixelate=1, quality=0, dpr=9),
            "https://cdn.imgwire.dev/example?width=800",
        )
        self.assertEqual(
            image.url(
                width=800,
                chroma_subsampling="4:2:0",
                progressive="maybe",
                quality="best",
            ),
            "https://cdn.imgwire.dev/example?width=800",
        )
        self.assertEqual(
            image.url(pixelate=257),
            "https://cdn.imgwire.dev/example",
        )

    def test_builds_urls_for_rulespec_examples(self) -> None:
        image = make_image()

        self.assertEqual(
            image.url(w=800, h=600, resizing_type="cover"),
            "https://cdn.imgwire.dev/example?height=600&resizing_type=cover&width=800",
        )
        self.assertEqual(
            image.url(width=1200, format="jpg", q=85),
            "https://cdn.imgwire.dev/example?format=jpg&quality=85&width=1200",
        )
        self.assertEqual(
            image.url(crop="400:300:noea"),
            "https://cdn.imgwire.dev/example?crop=400%3A300%3Anortheast",
        )
        self.assertEqual(
            image.url(
                watermark_url="https://example.com/logo.png",
                watermark_position="southeast:-24:-24:0.85",
                format="webp",
            ),
            "https://cdn.imgwire.dev/example?format=webp"
            "&watermark_position=southeast%3A-24%3A-24%3A0.85"
            "&watermark_url=aHR0cHM6Ly9leGFtcGxlLmNvbS9sb2dvLnBuZw%3D%3D",
        )
        self.assertEqual(
            image.url(
                watermark="logo_image_id",
                watermark_position="se:-24:-24",
                format="webp",
            ),
            "https://cdn.imgwire.dev/example?format=webp&watermark=logo_image_id"
            "&watermark_position=southeast%3A-24%3A-24",
        )

    def test_supports_every_rulespec_transformation(self) -> None:
        image = make_image()

        url = image.url(
            {
                "adjust": {"brightness": 1.1, "saturation": 0.9, "color": 1.2},
                "background": "#fff",
                "background_alpha": 0.5,
                "blur": True,
                "brightness": 1.2,
                "chroma_subsampling": "4:2:2",
                "color_profile": "srgb",
                "colorize": "#112233",
                "contrast": {"multiplier": 1.1, "pivot": 128},
                "crop": {
                    "mode": "extract",
                    "x": 1,
                    "y": 2,
                    "width": 300,
                    "height": 200,
                    "gravity": "ne",
                },
                "dpi": 300,
                "dpr": 2,
                "duotone": {
                    "shadow_color": "#000000",
                    "highlight_color": "#ffffff",
                },
                "enlarge": False,
                "extend": {
                    "top": 1,
                    "right": 2,
                    "bottom": 3,
                    "left": 4,
                    "background": "#abcdef",
                },
                "extend_aspect_ratio": {"width": 16, "height": 9},
                "flip": "horizontal",
                "format": "jpeg",
                "gradient": {
                    "colors": ["#ff0000", "#00ff00"],
                    "angle": 90,
                    "opacity": 0.25,
                    "blend": "overlay",
                },
                "gravity": "se",
                "height": 600,
                "hue": 45,
                "keep_copyright": True,
                "lightness": 1.1,
                "min_height": 100,
                "min_width": 100,
                "monochrome": "#333333",
                "negate": {"alpha": True},
                "normalize": {"lower": 1, "upper": 99},
                "padding": {"all": 5, "background": "#ffffff"},
                "pixelate": 8,
                "progressive": "auto",
                "quality": 80,
                "resizing_algorithm": "lanczos3",
                "resizing_type": "fit",
                "rotate": {"angle": 45, "background": "255:255:255"},
                "saturation": 0.8,
                "sharpen": {"sigma": 1.2},
                "strip_color_profile": False,
                "strip_metadata": False,
                "watermark": {
                    "image_id": "wm_1",
                    "gravity": "sw",
                    "x": -1,
                    "y": 2,
                },
                "watermark_position": {
                    "gravity": "se",
                    "x": -24,
                    "y": -24,
                    "opacity": 0.85,
                    "blend": "over",
                },
                "watermark_rotate": {"angle": -15, "background": "#00000000"},
                "watermark_shadow": {"color": "#000", "blur": 4, "x": 1, "y": 2},
                "watermark_size": {"width": 200, "scale": 0.5},
                "watermark_text": {
                    "text": "Sample",
                    "size": 24,
                    "color": "#ffffff",
                    "gravity": "ce",
                },
                "watermark_url": "https://example.com/logo.png",
                "width": 800,
                "zoom": {"factor": 2, "gravity": "attention"},
            }
        )

        params = {
            key: values[0] for key, values in parse_qs(urlparse(url).query).items()
        }
        self.assertEqual(
            set(params),
            {
                "adjust",
                "background",
                "background_alpha",
                "blur",
                "brightness",
                "chroma_subsampling",
                "color_profile",
                "colorize",
                "contrast",
                "crop",
                "dpi",
                "dpr",
                "duotone",
                "enlarge",
                "extend",
                "extend_aspect_ratio",
                "flip",
                "format",
                "gradient",
                "gravity",
                "height",
                "hue",
                "keep_copyright",
                "lightness",
                "min-height",
                "min-width",
                "monochrome",
                "negate",
                "normalize",
                "padding",
                "pixelate",
                "progressive",
                "quality",
                "resizing_algorithm",
                "resizing_type",
                "rotate",
                "saturation",
                "sharpen",
                "strip_color_profile",
                "strip_metadata",
                "watermark",
                "watermark_position",
                "watermark_rotate",
                "watermark_shadow",
                "watermark_size",
                "watermark_text",
                "watermark_url",
                "width",
                "zoom",
            },
        )

        self.assertEqual(params["background"], "fff")
        self.assertEqual(params["blur"], "true")
        self.assertEqual(params["chroma_subsampling"], "4:2:2")
        self.assertEqual(params["format"], "jpg")
        self.assertEqual(params["gravity"], "southeast")
        self.assertEqual(params["monochrome"], "333333")
        self.assertEqual(params["negate"], "alpha:true")
        self.assertEqual(params["progressive"], "auto")
        self.assertEqual(params["resizing_type"], "inside")
        self.assertEqual(
            params["watermark_url"], "aHR0cHM6Ly9leGFtcGxlLmNvbS9sb2dvLnBuZw=="
        )
        self.assertEqual(params["zoom"], "2:attention")

        self.assertEqual(
            json_value(params["gradient"]),
            {
                "angle": 90,
                "blend": "overlay",
                "colors": ["#ff0000", "#00ff00"],
                "opacity": 0.25,
            },
        )
        self.assertEqual(
            json_value(params["rotate"]),
            {"angle": 45, "background": {"b": 255, "g": 255, "r": 255}},
        )
        self.assertEqual(
            json_value(params["watermark"]),
            {"gravity": "southwest", "imageId": "wm_1", "x": -1, "y": 2},
        )


def json_value(value: str) -> object:
    import json

    return json.loads(value)


if __name__ == "__main__":
    unittest.main()
