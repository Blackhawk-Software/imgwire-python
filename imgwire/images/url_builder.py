from __future__ import annotations

import base64
import json
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional
from urllib.parse import urlencode, urlparse, urlunparse

from generated.imgwire_generated.models.image_schema import ImageSchema

IMAGE_URL_PRESETS = ("thumbnail", "small", "medium", "large")
IMAGE_URL_GRAVITY_ALIASES = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
    "ne": "northeast",
    "se": "southeast",
    "nw": "northwest",
    "sw": "southwest",
    "no": "north",
    "so": "south",
    "ea": "east",
    "we": "west",
    "noea": "northeast",
    "soea": "southeast",
    "nowe": "northwest",
    "sowe": "southwest",
}
IMAGE_URL_GRAVITY_TYPES = (
    "ce",
    "center",
    "north",
    "south",
    "east",
    "west",
    "northeast",
    "northwest",
    "southeast",
    "southwest",
    "attention",
    "entropy",
)
IMAGE_URL_RESIZING_TYPE_ALIASES = {
    "fit": "inside",
    "fill-down": "inside",
    "force": "fill",
    "auto": "inside",
}
IMAGE_URL_RESIZING_TYPES = ("cover", "contain", "fill", "inside", "outside")
IMAGE_URL_RESIZING_ALGORITHMS = (
    "nearest",
    "cubic",
    "mitchell",
    "lanczos2",
    "lanczos3",
)
IMAGE_URL_OUTPUT_FORMATS = ("auto", "jpg", "jpeg", "png", "webp", "avif", "gif", "tiff")
IMAGE_URL_TRUTHY_VALUES = ("true", "t", "1")
IMAGE_URL_FALSY_VALUES = ("false", "f", "0")

_MISSING = object()


class ImgwireImage(ImageSchema):
    def url(self, options: Optional[Mapping[str, Any]] = None, /, **kwargs: Any) -> str:
        merged_options = dict(options or {})
        for key, value in kwargs.items():
            if key in merged_options:
                raise ValueError(f"Duplicate transformation rule: {key}")
            merged_options[key] = value

        return ImageUrlBuilder(self).build(merged_options)


def extend_image(image: ImageSchema | Mapping[str, Any]) -> ImgwireImage:
    if isinstance(image, ImgwireImage):
        return image

    if isinstance(image, ImageSchema):
        return ImgwireImage.model_validate(image.model_dump())

    return ImgwireImage.model_validate(image)


@dataclass(frozen=True)
class TransformationEntry:
    canonical: str
    url_value: str


@dataclass(frozen=True)
class Rule:
    aliases: tuple[str, ...]
    canonical: str
    parse: Callable[[Any, str], Optional[TransformationEntry]]


class ImageUrlBuilder:
    def __init__(self, image: ImageSchema) -> None:
        self._image = image

    def build(self, options: Optional[Mapping[str, Any]] = None) -> str:
        parsed = urlparse(self._image.cdn_url)
        options = dict(options or {})
        entries = _parse_transformation_entries(options)
        path = parsed.path

        preset = options.get("preset")
        if preset is not None:
            if preset not in IMAGE_URL_PRESETS:
                raise ValueError("Invalid transformation rule value for preset")
            path = _append_preset_to_path(parsed.path, str(preset))

        if not entries:
            return urlunparse(parsed._replace(path=path, query=""))

        pairs = [(entry.canonical, entry.url_value) for entry in entries]
        query = urlencode(sorted(pairs, key=lambda pair: pair[0]))
        return urlunparse(parsed._replace(path=path, query=query))


def _parse_transformation_entries(
    options: Mapping[str, Any],
) -> list[TransformationEntry]:
    entries: list[TransformationEntry] = []
    seen_canonicals: set[str] = set()

    for rule in RULES:
        present_aliases = [alias for alias in rule.aliases if alias in options]
        if not present_aliases:
            continue
        if len(present_aliases) > 1 or rule.canonical in seen_canonicals:
            raise ValueError(f"Duplicate transformation rule: {rule.canonical}")

        seen_canonicals.add(rule.canonical)
        try:
            entry = rule.parse(options[present_aliases[0]], rule.canonical)
        except ValueError:
            continue
        if entry is not None:
            entries.append(entry)

    return entries


def _append_preset_to_path(pathname: str, preset: str) -> str:
    return f"{pathname}@{preset}"


def _create_transformation(canonical: str, url_value: str) -> TransformationEntry:
    return TransformationEntry(canonical=canonical, url_value=url_value)


def _parse_width(value: Any, canonical: str) -> TransformationEntry:
    return _parse_dimension_transformation(value, canonical)


def _parse_height(value: Any, canonical: str) -> TransformationEntry:
    return _parse_dimension_transformation(value, canonical)


def _parse_min_width(value: Any, canonical: str) -> TransformationEntry:
    return _parse_dimension_transformation(value, canonical)


def _parse_min_height(value: Any, canonical: str) -> TransformationEntry:
    return _parse_dimension_transformation(value, canonical)


def _parse_dimension_transformation(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(canonical, str(_parse_dimension(value, canonical)))


def _parse_resizing_type(value: Any, canonical: str) -> TransformationEntry:
    raw = _parse_string(value, canonical).strip().lower()
    resizing_type = IMAGE_URL_RESIZING_TYPE_ALIASES.get(raw, raw)
    if resizing_type not in IMAGE_URL_RESIZING_TYPES:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(canonical, resizing_type)


def _parse_resizing_algorithm(value: Any, canonical: str) -> TransformationEntry:
    algorithm = _parse_string(value, canonical).strip().lower()
    if algorithm not in IMAGE_URL_RESIZING_ALGORITHMS:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(canonical, algorithm)


def _parse_zoom(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        factor = _parse_range_number(_field(record, "factor"), canonical, 1, 10)
        gravity = _field(record, "gravity", default=None)
        if gravity is None:
            return _create_transformation(canonical, _stringify_number(factor))
        return _create_transformation(
            canonical,
            f"{_stringify_number(factor)}:{_normalize_gravity(gravity, canonical)}",
        )

    parts = _parse_string(value, canonical).split(":")
    if len(parts) not in {1, 2}:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    factor = _parse_range_number(parts[0], canonical, 1, 10)
    if len(parts) == 1:
        return _create_transformation(canonical, _stringify_number(factor))
    gravity = _normalize_gravity(parts[1], canonical)
    return _create_transformation(canonical, f"{_stringify_number(factor)}:{gravity}")


def _parse_dpr(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, _stringify_number(_parse_range_number(value, canonical, 0.01, 8))
    )


def _parse_enlarge(value: Any, canonical: str) -> TransformationEntry:
    return _parse_boolean_transformation(value, canonical)


def _parse_extend(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        payload: dict[str, Any] = {}
        for field in ("top", "right", "bottom", "left"):
            field_value = _field(record, field, default=None)
            if field_value is not None:
                payload[field] = _parse_integer(
                    field_value, canonical, minimum=0, maximum=8192
                )
        background = _field(record, "background", "bg", default=None)
        if background is not None:
            payload["background"] = _normalize_color_for_json(background, canonical)
        if not payload:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        return _create_transformation(canonical, _json_value(payload))

    parts = _parse_string(value, canonical).split(":")
    if len(parts) < 1 or len(parts) > 5:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    parsed_parts = [
        str(_parse_integer(part, canonical, minimum=0, maximum=8192))
        for part in parts[:4]
    ]
    if len(parts) == 5:
        parsed_parts.append(_normalize_color_for_url(parts[4], canonical))
    return _create_transformation(canonical, ":".join(parsed_parts))


def _parse_extend_aspect_ratio(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        payload: dict[str, Any] = {}
        ratio = _field(record, "ratio", "aspectRatio", "aspect_ratio", default=None)
        width = _field(record, "width", default=None)
        height = _field(record, "height", default=None)
        if ratio is not None:
            payload["ratio"] = _normalize_aspect_ratio(ratio, canonical)
        if width is not None:
            payload["width"] = _parse_dimension(width, canonical)
        if height is not None:
            payload["height"] = _parse_dimension(height, canonical)
        if not payload or (("width" in payload) != ("height" in payload)):
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        return _create_transformation(canonical, _json_value(payload))

    raw = _parse_string(value, canonical)
    if ":" in raw:
        width, height = raw.split(":", 1)
        parsed_width = _parse_positive_number(width, canonical)
        parsed_height = _parse_positive_number(height, canonical)
        return _create_transformation(
            canonical,
            f"{_stringify_number(parsed_width)}:{_stringify_number(parsed_height)}",
        )

    return _create_transformation(
        canonical,
        _stringify_number(_parse_range_number(raw, canonical, 0.01, 8192)),
    )


def _parse_gravity(value: Any, canonical: str) -> TransformationEntry:
    parts = _parse_string(value, canonical).split(":")
    if len(parts) == 2 and parts[1] == "sm":
        return _create_transformation(canonical, "attention")
    if len(parts) != 1:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(canonical, _normalize_gravity(parts[0], canonical))


def _parse_crop(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        payload: dict[str, Any] = {}
        mode = _field(record, "mode", default=None)
        if mode is not None:
            normalized_mode = _parse_string(mode, canonical).strip().lower()
            if normalized_mode not in {"cover", "extract", "attention", "entropy"}:
                raise ValueError(f"Invalid transformation rule value for {canonical}")
            payload["mode"] = normalized_mode
        for field in ("x", "y"):
            field_value = _field(record, field, default=None)
            if field_value is not None:
                payload[field] = _parse_integer(field_value, canonical, minimum=0)
        for field in ("width", "height"):
            field_value = _field(record, field, default=None)
            if field_value is not None:
                payload[field] = _parse_dimension(field_value, canonical)
        gravity = _field(record, "gravity", default=None)
        if gravity is not None:
            payload["gravity"] = _normalize_gravity(gravity, canonical)
        if "width" not in payload or "height" not in payload:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        if payload.get("mode") == "extract" and (
            "x" not in payload or "y" not in payload
        ):
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        return _create_transformation(canonical, _json_value(payload))

    parts = _parse_string(value, canonical).split(":")
    if len(parts) in {4, 5}:
        x, y, width, height, *gravity_part = parts
        parsed = [
            str(_parse_integer(x, canonical, minimum=0)),
            str(_parse_integer(y, canonical, minimum=0)),
            str(_parse_dimension(width, canonical)),
            str(_parse_dimension(height, canonical)),
        ]
        if gravity_part:
            parsed.append(_normalize_gravity(gravity_part[0], canonical))
        return _create_transformation(canonical, ":".join(parsed))

    if len(parts) not in {2, 3}:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    width, height, *gravity_part = parts
    gravity = _normalize_gravity(gravity_part[0], canonical) if gravity_part else "ce"
    return _create_transformation(
        canonical,
        f"{_parse_dimension(width, canonical)}:{_parse_dimension(height, canonical)}"
        f":{gravity}",
    )


def _parse_padding(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        payload: dict[str, Any] = {}
        for field in ("all", "x", "y", "top", "right", "bottom", "left"):
            field_value = _field(record, field, default=None)
            if field_value is not None:
                payload[field] = _parse_integer(
                    field_value, canonical, minimum=0, maximum=8192
                )
        background = _field(record, "background", "bg", default=None)
        if background is not None:
            payload["background"] = _normalize_color_for_json(background, canonical)
        if not payload:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        return _create_transformation(canonical, _json_value(payload))

    parts = _parse_string(value, canonical).split(":")
    if len(parts) < 1 or len(parts) > 4:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(
        canonical,
        ":".join(
            str(_parse_integer(part, canonical, minimum=0, maximum=8192))
            for part in parts
        ),
    )


def _parse_rotate(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        angle = _parse_integer(_field(record, "angle"), canonical)
        payload: dict[str, Any] = {"angle": angle}
        background = _field(record, "background", "bg", default=None)
        if background is not None:
            payload["background"] = _normalize_color_for_json(background, canonical)
        return _create_transformation(canonical, _json_value(payload))

    parts = _parse_string(value, canonical).split(":")
    if len(parts) not in {1, 2}:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    angle = str(_parse_integer(parts[0], canonical))
    if len(parts) == 1:
        return _create_transformation(canonical, angle)
    return _create_transformation(
        canonical, f"{angle}:{_normalize_color_for_url(parts[1], canonical)}"
    )


def _parse_flip(value: Any, canonical: str) -> Optional[TransformationEntry]:
    normalized = _parse_string(value, canonical).strip().lower()
    if normalized in {"vertical", "horizontal", "both"}:
        return _create_transformation(canonical, normalized)

    parts = normalized.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    horizontal, vertical = (_parse_boolean(part, canonical) for part in parts)
    if horizontal and vertical:
        return _create_transformation(canonical, "both")
    if horizontal:
        return _create_transformation(canonical, "horizontal")
    if vertical:
        return _create_transformation(canonical, "vertical")
    return None


def _parse_background(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(canonical, _normalize_color_for_url(value, canonical))


def _parse_background_alpha(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, _stringify_number(_parse_range_number(value, canonical, 0, 1))
    )


def _parse_blur(value: Any, canonical: str) -> TransformationEntry:
    if _is_truthy_string(value):
        return _create_transformation(canonical, "true")
    return _create_transformation(
        canonical, _stringify_number(_parse_range_number(value, canonical, 0.3, 100))
    )


def _parse_sharpen(value: Any, canonical: str) -> TransformationEntry:
    if _is_truthy_string(value):
        return _create_transformation(canonical, "true")

    record = _object_value(value, canonical)
    if record is not None:
        payload: dict[str, Any] = {}
        for field in ("sigma", "m1", "m2", "x1", "y2", "y3"):
            field_value = _field(record, field, default=None)
            if field_value is not None:
                payload[field] = _parse_positive_number(field_value, canonical)
        if not payload:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        return _create_transformation(canonical, _json_value(payload))

    sigma = _parse_positive_number(value, canonical)
    return _create_transformation(canonical, _stringify_number(sigma))


def _parse_pixelate(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, str(_parse_integer(value, canonical, minimum=2, maximum=256))
    )


def _parse_boolean_transformation(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, "true" if _parse_boolean(value, canonical) else "false"
    )


def _parse_quality(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, str(_parse_integer(value, canonical, minimum=1, maximum=100))
    )


def _parse_format(value: Any, canonical: str) -> TransformationEntry:
    image_format = _parse_string(value, canonical).strip().lower()
    if image_format not in IMAGE_URL_OUTPUT_FORMATS:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(
        canonical, "jpg" if image_format == "jpeg" else image_format
    )


def _parse_simple_number(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, _stringify_number(_parse_range_number(value, canonical, 0.01, 10))
    )


def _parse_hue(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, _stringify_number(_parse_number(value, canonical))
    )


def _parse_dpi(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, str(_parse_integer(value, canonical, minimum=1, maximum=600))
    )


def _parse_adjust(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        payload: dict[str, Any] = {}
        for field in ("brightness", "saturation", "color"):
            field_value = _field(record, field, default=None)
            if field_value is not None:
                payload[field] = _parse_range_number(field_value, canonical, 0.01, 10)
        if not payload:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        return _create_transformation(canonical, _json_value(payload))

    parts = _parse_string(value, canonical).split(":")
    if len(parts) < 1 or len(parts) > 3:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    parsed = [_stringify_number(_parse_range_number(parts[0], canonical, 0.01, 10))]
    for part in parts[1:]:
        parsed.append(
            ""
            if part == ""
            else _stringify_number(_parse_range_number(part, canonical, 0.01, 10))
        )
    return _create_transformation(canonical, ":".join(parsed))


def _parse_color_profile(value: Any, canonical: str) -> TransformationEntry:
    profile = _parse_string(value, canonical).strip().lower()
    if profile not in {"srgb", "rgb16", "cmyk", "keep", "preserve"}:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(canonical, profile)


def _parse_colorize(value: Any, canonical: str) -> TransformationEntry:
    return _parse_background(value, canonical)


def _parse_contrast(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        payload: dict[str, Any] = {
            "multiplier": _parse_range_number(
                _field(record, "multiplier"), canonical, 0.01, 10
            )
        }
        pivot = _field(record, "pivot", default=None)
        if pivot is not None:
            payload["pivot"] = _parse_range_number(pivot, canonical, 0, 255)
        return _create_transformation(canonical, _json_value(payload))

    parts = _parse_string(value, canonical).split(":")
    if len(parts) not in {1, 2}:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    multiplier = _stringify_number(_parse_range_number(parts[0], canonical, 0.01, 10))
    if len(parts) == 1:
        return _create_transformation(canonical, multiplier)
    pivot = _stringify_number(_parse_range_number(parts[1], canonical, 0, 255))
    return _create_transformation(canonical, f"{multiplier}:{pivot}")


def _parse_duotone(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        payload = {
            "highlightColor": _normalize_color_for_json(
                _field(record, "highlightColor", "highlight_color"), canonical
            ),
            "shadowColor": _normalize_color_for_json(
                _field(record, "shadowColor", "shadow_color"), canonical
            ),
        }
        return _create_transformation(canonical, _json_value(payload))

    parts = _parse_string(value, canonical).split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(
        canonical,
        ":".join(_normalize_color_for_url(part, canonical) for part in parts),
    )


def _parse_gradient(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        raw_colors = _field(record, "colors", default=None)
        if not isinstance(raw_colors, list) or not raw_colors:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        payload: dict[str, Any] = {
            "colors": [
                _normalize_color_for_json(color, canonical) for color in raw_colors
            ]
        }
        angle = _field(record, "angle", default=None)
        if angle is not None:
            payload["angle"] = _parse_range_number(angle, canonical, -360, 360)
        opacity = _field(record, "opacity", default=None)
        if opacity is not None:
            payload["opacity"] = _parse_range_number(opacity, canonical, 0, 1)
        blend = _field(record, "blend", default=None)
        if blend is not None:
            payload["blend"] = _parse_non_empty_string(blend, canonical)
        return _create_transformation(canonical, _json_value(payload))

    colors_value, *optional_parts = _parse_string(value, canonical).split(":")
    colors = [
        _normalize_color_for_url(color, canonical)
        for color in colors_value.split(",")
        if color
    ]
    if not colors or len(optional_parts) > 3:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    parsed = [",".join(colors)]
    if len(optional_parts) >= 1:
        parsed.append(
            ""
            if optional_parts[0] == ""
            else _stringify_number(
                _parse_range_number(optional_parts[0], canonical, -360, 360)
            )
        )
    if len(optional_parts) >= 2:
        parsed.append(
            ""
            if optional_parts[1] == ""
            else _stringify_number(
                _parse_range_number(optional_parts[1], canonical, 0, 1)
            )
        )
    if len(optional_parts) == 3:
        parsed.append(_parse_non_empty_string(optional_parts[2], canonical))
    return _create_transformation(canonical, ":".join(parsed))


def _parse_monochrome(value: Any, canonical: str) -> Optional[TransformationEntry]:
    if _is_truthy_string(value):
        return _create_transformation(canonical, "true")
    if _is_falsy_string(value):
        return None

    record = _object_value(value, canonical)
    if record is not None:
        tint = _field(record, "tint", default=None)
        if tint is None:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        return _create_transformation(
            canonical, _normalize_color_for_url(tint, canonical)
        )

    return _create_transformation(canonical, _normalize_color_for_url(value, canonical))


def _parse_negate(value: Any, canonical: str) -> TransformationEntry:
    if _is_truthy_string(value):
        return _create_transformation(canonical, "true")

    record = _object_value(value, canonical)
    if record is not None:
        alpha = _field(record, "alpha", default=None)
        if alpha is None:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        return _create_transformation(
            canonical,
            f"alpha:{'true' if _parse_boolean(alpha, canonical) else 'false'}",
        )

    parts = _parse_string(value, canonical).split(":")
    if len(parts) == 2 and parts[0] == "alpha":
        return _create_transformation(
            canonical,
            f"alpha:{'true' if _parse_boolean(parts[1], canonical) else 'false'}",
        )
    raise ValueError(f"Invalid transformation rule value for {canonical}")


def _parse_normalize(value: Any, canonical: str) -> TransformationEntry:
    if _is_truthy_string(value) or _is_falsy_string(value):
        return _parse_boolean_transformation(value, canonical)

    record = _object_value(value, canonical)
    if record is not None:
        payload: dict[str, Any] = {}
        for field in ("lower", "upper"):
            field_value = _field(record, field, default=None)
            if field_value is not None:
                payload[field] = _parse_range_number(field_value, canonical, 0, 100)
        _validate_normalize_bounds(payload, canonical)
        if not payload:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        return _create_transformation(canonical, _json_value(payload))

    parts = _parse_string(value, canonical).split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    lower = _parse_range_number(parts[0], canonical, 0, 100)
    upper = _parse_range_number(parts[1], canonical, 0, 100)
    _validate_normalize_bounds({"lower": lower, "upper": upper}, canonical)
    return _create_transformation(
        canonical, f"{_stringify_number(lower)}:{_stringify_number(upper)}"
    )


def _parse_watermark(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        image_id = _field(record, "image_id", "imageId")
        payload: dict[str, Any] = {
            "imageId": _parse_watermark_image_id(image_id, canonical)
        }
        _copy_position_fields(record, payload, canonical)
        return _create_transformation(canonical, _json_value(payload))

    parts = _parse_string(value, canonical).split(":")
    if len(parts) < 1 or len(parts) > 4:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    image_id, *rest = parts
    parsed = [_parse_watermark_image_id(image_id, canonical)]
    if len(rest) >= 1 and rest[0] != "":
        parsed.append(_normalize_gravity(rest[0], canonical))
    if len(rest) >= 2 and rest[1] != "":
        parsed.append(str(_parse_integer(rest[1], canonical)))
    if len(rest) >= 3 and rest[2] != "":
        parsed.append(str(_parse_integer(rest[2], canonical)))
    return _create_transformation(canonical, ":".join(parsed))


def _parse_watermark_position(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        payload: dict[str, Any] = {}
        _copy_position_fields(record, payload, canonical, gravity_required=False)
        if not payload:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        return _create_transformation(canonical, _json_value(payload))

    parts = _parse_string(value, canonical).split(":")
    if len(parts) < 1 or len(parts) > 5:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    gravity, *rest = parts
    parsed = [_normalize_gravity(gravity, canonical)]
    if len(rest) >= 1 and rest[0] != "":
        parsed.append(str(_parse_integer(rest[0], canonical)))
    if len(rest) >= 2 and rest[1] != "":
        parsed.append(str(_parse_integer(rest[1], canonical)))
    if len(rest) >= 3 and rest[2] != "":
        parsed.append(_stringify_number(_parse_range_number(rest[2], canonical, 0, 1)))
    if len(rest) >= 4 and rest[3] != "":
        parsed.append(_parse_non_empty_string(rest[3], canonical))
    return _create_transformation(canonical, ":".join(parsed))


def _parse_watermark_shadow(value: Any, canonical: str) -> TransformationEntry:
    if _is_truthy_string(value):
        return _create_transformation(canonical, "true")

    record = _object_value(value, canonical)
    if record is not None:
        payload: dict[str, Any] = {}
        color = _field(record, "color", default=None)
        if color is not None:
            payload["color"] = _normalize_color_for_json(color, canonical)
        blur = _field(record, "blur", default=None)
        if blur is not None:
            payload["blur"] = _parse_range_number(blur, canonical, 0.3, 100)
        for field in ("x", "y"):
            field_value = _field(record, field, default=None)
            if field_value is not None:
                payload[field] = _parse_integer(field_value, canonical)
        if not payload:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        return _create_transformation(canonical, _json_value(payload))

    parts = _parse_string(value, canonical).split(":")
    if len(parts) < 1 or len(parts) > 4:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    parsed = [_normalize_color_for_url(parts[0], canonical)]
    if len(parts) >= 2 and parts[1] != "":
        parsed.append(
            _stringify_number(_parse_range_number(parts[1], canonical, 0.3, 100))
        )
    if len(parts) >= 3 and parts[2] != "":
        parsed.append(str(_parse_integer(parts[2], canonical)))
    if len(parts) >= 4 and parts[3] != "":
        parsed.append(str(_parse_integer(parts[3], canonical)))
    return _create_transformation(canonical, ":".join(parsed))


def _parse_watermark_size(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        payload: dict[str, Any] = {}
        for field in ("width", "height"):
            field_value = _field(record, field, default=None)
            if field_value is not None:
                payload[field] = _parse_dimension(field_value, canonical)
        scale = _field(record, "scale", default=None)
        if scale is not None:
            payload["scale"] = _parse_range_number(scale, canonical, 0.01, 10)
        if not payload:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        return _create_transformation(canonical, _json_value(payload))

    parts = _parse_string(value, canonical).split(":")
    if len(parts) < 1 or len(parts) > 3:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    parsed: list[str] = []
    if parts[0] != "":
        parsed.append(str(_parse_dimension(parts[0], canonical)))
    elif len(parts) == 1:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    else:
        parsed.append("")
    if len(parts) >= 2:
        parsed.append(
            "" if parts[1] == "" else str(_parse_dimension(parts[1], canonical))
        )
    if len(parts) == 3:
        parsed.append(
            ""
            if parts[2] == ""
            else _stringify_number(_parse_range_number(parts[2], canonical, 0.01, 10))
        )
    if all(part == "" for part in parsed):
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(canonical, ":".join(parsed))


def _parse_watermark_text(value: Any, canonical: str) -> TransformationEntry:
    record = _object_value(value, canonical)
    if record is not None:
        text = _parse_non_empty_string(_field(record, "text"), canonical)
        if len(text) > 2048:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        payload: dict[str, Any] = {"text": text}
        for field in ("font", "blend"):
            field_value = _field(record, field, default=None)
            if field_value is not None:
                payload[field] = _parse_non_empty_string(field_value, canonical)
        size = _field(record, "size", default=None)
        if size is not None:
            payload["size"] = _parse_integer(size, canonical, minimum=1, maximum=8192)
        color = _field(record, "color", default=None)
        if color is not None:
            payload["color"] = _normalize_color_for_json(color, canonical)
        for field in ("width", "height"):
            field_value = _field(record, field, default=None)
            if field_value is not None:
                payload[field] = _parse_dimension(field_value, canonical)
        _copy_position_fields(record, payload, canonical, gravity_required=False)
        return _create_transformation(canonical, _json_value(payload))

    text = _parse_non_empty_string(value, canonical)
    if len(text) > 2048:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(canonical, text)


def _parse_watermark_url(value: Any, canonical: str) -> TransformationEntry:
    raw = _parse_non_empty_string(value, canonical)
    parsed = urlparse(raw)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme.lower() != "https" or not parsed.netloc:
            raise ValueError(f"Invalid transformation rule value for {canonical}")
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        return _create_transformation(canonical, encoded)

    try:
        decoded = base64.b64decode(raw.encode("ascii"), validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError(f"Invalid transformation rule value for {canonical}") from exc
    decoded_url = urlparse(decoded)
    if decoded_url.scheme.lower() != "https" or not decoded_url.netloc:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(canonical, raw)


def _parse_integer(
    value: Any,
    label: str,
    *,
    minimum: int = -(2**53) + 1,
    maximum: int = (2**53) - 1,
) -> int:
    raw = _stringify_value(value, label)
    digits = raw[1:] if raw.startswith("-") else raw
    if not digits.isdigit():
        raise ValueError(f"Invalid transformation rule value for {label}")

    parsed_value = int(raw)
    if parsed_value < minimum or parsed_value > maximum:
        raise ValueError(f"Invalid transformation rule value for {label}")
    return parsed_value


def _parse_number(
    value: Any,
    label: str,
    *,
    minimum: float = float("-inf"),
    maximum: float = float("inf"),
    min_exclusive: bool = False,
) -> float:
    raw = _stringify_value(value, label)
    if raw.strip() == "":
        raise ValueError(f"Invalid transformation rule value for {label}")
    try:
        parsed_value = float(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid transformation rule value for {label}") from exc

    if (
        parsed_value == float("inf")
        or parsed_value == float("-inf")
        or parsed_value != parsed_value
        or (min_exclusive and parsed_value <= minimum)
        or (not min_exclusive and parsed_value < minimum)
        or parsed_value > maximum
    ):
        raise ValueError(f"Invalid transformation rule value for {label}")
    return parsed_value


def _parse_range_number(
    value: Any, label: str, minimum: float, maximum: float
) -> float:
    return _parse_number(value, label, minimum=minimum, maximum=maximum)


def _parse_dimension(value: Any, label: str) -> int:
    return _parse_integer(value, label, minimum=1, maximum=8192)


def _parse_positive_number(value: Any, label: str) -> float:
    return _parse_number(value, label, minimum=0, min_exclusive=True)


def _parse_boolean(value: Any, label: str) -> bool:
    if isinstance(value, bool):
        return value
    raw = _stringify_value(value, label).lower()
    if raw in IMAGE_URL_TRUTHY_VALUES:
        return True
    if raw in IMAGE_URL_FALSY_VALUES:
        return False
    raise ValueError(f"Invalid transformation rule value for {label}")


def _is_truthy_string(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        return False
    return value.strip().lower() in IMAGE_URL_TRUTHY_VALUES


def _is_falsy_string(value: Any) -> bool:
    if isinstance(value, bool):
        return not value
    if not isinstance(value, str):
        return False
    return value.strip().lower() in IMAGE_URL_FALSY_VALUES


def _parse_string(value: Any, label: str) -> str:
    return _stringify_value(value, label)


def _parse_non_empty_string(value: Any, label: str) -> str:
    raw = _parse_string(value, label).strip()
    if raw == "":
        raise ValueError(f"Invalid transformation rule value for {label}")
    return raw


def _stringify_value(value: Any, label: str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    raise ValueError(f"Invalid transformation rule value for {label}")


def _stringify_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def _json_value(value: Mapping[str, Any]) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _object_value(value: Any, label: str) -> Optional[Mapping[str, Any]]:
    if isinstance(value, MappingABC):
        return value
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    if not trimmed.startswith("{"):
        return None
    try:
        parsed = json.loads(trimmed)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid transformation rule value for {label}") from exc
    if not isinstance(parsed, MappingABC):
        raise ValueError(f"Invalid transformation rule value for {label}")
    return parsed


def _field(
    record: Mapping[str, Any],
    *names: str,
    default: Any = _MISSING,
) -> Any:
    for name in names:
        if name in record:
            return record[name]
    if default is not _MISSING:
        return default
    raise ValueError("Missing required transformation object field")


def _normalize_gravity(value: Any, label: str) -> str:
    raw = _parse_string(value, label).strip().lower()
    normalized = IMAGE_URL_GRAVITY_ALIASES.get(raw, raw)
    if normalized not in IMAGE_URL_GRAVITY_TYPES:
        raise ValueError(f"Invalid transformation rule value for {label}")
    return normalized


def _normalize_color_for_url(value: Any, label: str) -> str:
    if isinstance(value, MappingABC):
        parsed_parts = [
            str(_parse_integer(_field(value, field), label, minimum=0, maximum=255))
            for field in ("r", "g", "b")
        ]
        alpha = _field(value, "alpha", default=None)
        if alpha is not None:
            parsed_parts.append(
                _stringify_number(_parse_range_number(alpha, label, 0, 1))
            )
        return ":".join(parsed_parts)

    raw = _parse_string(value, label).strip()
    parts = raw.split(":")
    if len(parts) in {3, 4}:
        parsed_parts = [
            str(_parse_integer(part, label, minimum=0, maximum=255))
            for part in parts[:3]
        ]
        if len(parts) == 4:
            parsed_parts.append(
                _stringify_number(_parse_range_number(parts[3], label, 0, 1))
            )
        return ":".join(parsed_parts)

    hex_color = raw[1:] if raw.startswith("#") else raw
    if len(hex_color) not in {3, 6, 8} or any(
        character not in "0123456789abcdefABCDEF" for character in hex_color
    ):
        raise ValueError(f"Invalid transformation rule value for {label}")
    return hex_color.lower()


def _normalize_color_for_json(value: Any, label: str) -> Any:
    if isinstance(value, MappingABC):
        color: dict[str, Any] = {
            "b": _parse_integer(_field(value, "b"), label, minimum=0, maximum=255),
            "g": _parse_integer(_field(value, "g"), label, minimum=0, maximum=255),
            "r": _parse_integer(_field(value, "r"), label, minimum=0, maximum=255),
        }
        alpha = _field(value, "alpha", default=None)
        if alpha is not None:
            color["alpha"] = _parse_range_number(alpha, label, 0, 1)
        return color

    raw = _parse_string(value, label).strip()
    parts = raw.split(":")
    if len(parts) in {3, 4}:
        color = {
            "b": _parse_integer(parts[2], label, minimum=0, maximum=255),
            "g": _parse_integer(parts[1], label, minimum=0, maximum=255),
            "r": _parse_integer(parts[0], label, minimum=0, maximum=255),
        }
        if len(parts) == 4:
            color["alpha"] = _parse_range_number(parts[3], label, 0, 1)
        return color

    return f"#{_normalize_color_for_url(raw, label)}"


def _normalize_aspect_ratio(value: Any, label: str) -> Any:
    if isinstance(value, str) and ":" in value:
        width, height = value.split(":", 1)
        parsed_width = _parse_positive_number(width, label)
        parsed_height = _parse_positive_number(height, label)
        return f"{_stringify_number(parsed_width)}:{_stringify_number(parsed_height)}"
    return _parse_range_number(value, label, 0.01, 8192)


def _validate_normalize_bounds(payload: Mapping[str, Any], label: str) -> None:
    if (
        "lower" in payload
        and "upper" in payload
        and float(payload["lower"]) >= float(payload["upper"])
    ):
        raise ValueError(f"Invalid transformation rule value for {label}")


def _parse_watermark_image_id(value: Any, label: str) -> str:
    image_id = _parse_non_empty_string(value, label)
    if ":" in image_id or "/" in image_id:
        raise ValueError(f"Invalid transformation rule value for {label}")
    return image_id


def _copy_position_fields(
    record: Mapping[str, Any],
    payload: dict[str, Any],
    label: str,
    *,
    gravity_required: bool = False,
) -> None:
    gravity = _field(record, "gravity", default=None)
    if gravity is not None:
        payload["gravity"] = _normalize_gravity(gravity, label)
    elif gravity_required:
        raise ValueError(f"Invalid transformation rule value for {label}")

    for field in ("x", "y", "left", "top"):
        field_value = _field(record, field, default=None)
        if field_value is not None:
            payload[field] = _parse_integer(field_value, label)

    offset = _field(record, "offset", default=None)
    if offset is not None:
        if not isinstance(offset, MappingABC):
            raise ValueError(f"Invalid transformation rule value for {label}")
        parsed_offset: dict[str, int] = {}
        for field in ("x", "y"):
            field_value = _field(offset, field, default=None)
            if field_value is not None:
                parsed_offset[field] = _parse_integer(field_value, label)
        if not parsed_offset:
            raise ValueError(f"Invalid transformation rule value for {label}")
        payload["offset"] = parsed_offset

    opacity = _field(record, "opacity", default=None)
    if opacity is not None:
        payload["opacity"] = _parse_range_number(opacity, label, 0, 1)

    blend = _field(record, "blend", default=None)
    if blend is not None:
        payload["blend"] = _parse_non_empty_string(blend, label)


RULES = (
    Rule(canonical="adjust", aliases=("a", "adjust"), parse=_parse_adjust),
    Rule(canonical="background", aliases=("bg", "background"), parse=_parse_background),
    Rule(
        canonical="background_alpha",
        aliases=("bga", "background_alpha"),
        parse=_parse_background_alpha,
    ),
    Rule(canonical="blur", aliases=("bl", "blur"), parse=_parse_blur),
    Rule(
        canonical="brightness", aliases=("br", "brightness"), parse=_parse_simple_number
    ),
    Rule(
        canonical="color_profile",
        aliases=("cp", "icc", "color_profile"),
        parse=_parse_color_profile,
    ),
    Rule(canonical="colorize", aliases=("col", "colorize"), parse=_parse_colorize),
    Rule(canonical="contrast", aliases=("co", "contrast"), parse=_parse_contrast),
    Rule(canonical="crop", aliases=("c", "crop"), parse=_parse_crop),
    Rule(canonical="dpi", aliases=("dpi",), parse=_parse_dpi),
    Rule(canonical="dpr", aliases=("dpr",), parse=_parse_dpr),
    Rule(canonical="duotone", aliases=("dt", "duotone"), parse=_parse_duotone),
    Rule(canonical="enlarge", aliases=("el", "enlarge"), parse=_parse_enlarge),
    Rule(canonical="extend", aliases=("ex", "extend"), parse=_parse_extend),
    Rule(
        canonical="extend_aspect_ratio",
        aliases=("exar", "extend_ar", "extend_aspect_ratio"),
        parse=_parse_extend_aspect_ratio,
    ),
    Rule(canonical="flip", aliases=("fl", "flip"), parse=_parse_flip),
    Rule(
        canonical="format",
        aliases=("f", "format", "ext", "extension"),
        parse=_parse_format,
    ),
    Rule(canonical="gradient", aliases=("gr", "gradient"), parse=_parse_gradient),
    Rule(canonical="gravity", aliases=("g", "gravity"), parse=_parse_gravity),
    Rule(canonical="height", aliases=("h", "height"), parse=_parse_height),
    Rule(canonical="hue", aliases=("hu", "hue"), parse=_parse_hue),
    Rule(
        canonical="keep_copyright",
        aliases=("kcr", "keep_copyright"),
        parse=_parse_boolean_transformation,
    ),
    Rule(canonical="lightness", aliases=("l", "lightness"), parse=_parse_simple_number),
    Rule(
        canonical="min-height",
        aliases=("mh", "min_height", "min-height"),
        parse=_parse_min_height,
    ),
    Rule(
        canonical="min-width",
        aliases=("mw", "min_width", "min-width"),
        parse=_parse_min_width,
    ),
    Rule(canonical="monochrome", aliases=("mc", "monochrome"), parse=_parse_monochrome),
    Rule(canonical="negate", aliases=("neg", "negate"), parse=_parse_negate),
    Rule(
        canonical="normalize",
        aliases=("norm", "normalise", "normalize"),
        parse=_parse_normalize,
    ),
    Rule(canonical="padding", aliases=("pd", "padding"), parse=_parse_padding),
    Rule(canonical="pixelate", aliases=("pix", "pixelate"), parse=_parse_pixelate),
    Rule(canonical="quality", aliases=("q", "quality"), parse=_parse_quality),
    Rule(
        canonical="resizing_algorithm",
        aliases=("ra", "resizing_algorithm"),
        parse=_parse_resizing_algorithm,
    ),
    Rule(
        canonical="resizing_type",
        aliases=("resizing_type",),
        parse=_parse_resizing_type,
    ),
    Rule(canonical="rotate", aliases=("rot", "rotate"), parse=_parse_rotate),
    Rule(
        canonical="saturation", aliases=("sa", "saturation"), parse=_parse_simple_number
    ),
    Rule(canonical="sharpen", aliases=("sh", "sharpen"), parse=_parse_sharpen),
    Rule(
        canonical="strip_color_profile",
        aliases=("scp", "strip_color_profile"),
        parse=_parse_boolean_transformation,
    ),
    Rule(
        canonical="strip_metadata",
        aliases=("sm", "strip_metadata"),
        parse=_parse_boolean_transformation,
    ),
    Rule(canonical="watermark", aliases=("wm", "watermark"), parse=_parse_watermark),
    Rule(
        canonical="watermark_position",
        aliases=("wmp", "watermark_offset", "watermark_position"),
        parse=_parse_watermark_position,
    ),
    Rule(
        canonical="watermark_rotate",
        aliases=("wmr", "wm_rot", "watermark_rotate"),
        parse=_parse_rotate,
    ),
    Rule(
        canonical="watermark_shadow",
        aliases=("wmsh", "watermark_shadow"),
        parse=_parse_watermark_shadow,
    ),
    Rule(
        canonical="watermark_size",
        aliases=("wms", "watermark_size"),
        parse=_parse_watermark_size,
    ),
    Rule(
        canonical="watermark_text",
        aliases=("wmt", "watermark_text"),
        parse=_parse_watermark_text,
    ),
    Rule(
        canonical="watermark_url",
        aliases=("wmu", "watermark_url"),
        parse=_parse_watermark_url,
    ),
    Rule(canonical="width", aliases=("w", "width"), parse=_parse_width),
    Rule(canonical="zoom", aliases=("z", "zoom"), parse=_parse_zoom),
)
