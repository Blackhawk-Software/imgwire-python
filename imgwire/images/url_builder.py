from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from generated.imgwire_generated.models.image_schema import ImageSchema

IMAGE_URL_PRESETS = ("thumbnail", "small", "medium", "large")
IMAGE_URL_GRAVITY_TYPES = (
    "no",
    "so",
    "ea",
    "we",
    "noea",
    "nowe",
    "soea",
    "sowe",
    "ce",
)
IMAGE_URL_RESIZING_TYPES = ("fit", "fill", "fill-down", "force", "auto")
IMAGE_URL_OUTPUT_FORMATS = ("jpg", "png", "avif", "gif", "webp", "auto")
IMAGE_URL_ROTATE_ANGLES = (0, 90, 180, 270, 360)


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
    cache_value: str


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
        entries = _parse_transformation_entries(dict(options or {}))
        path = parsed.path

        preset = (options or {}).get("preset")
        if preset is not None:
            if preset not in IMAGE_URL_PRESETS:
                raise ValueError("Invalid transformation rule value for preset")
            path = _append_preset_to_path(parsed.path, str(preset))

        if not entries:
            return urlunparse(parsed._replace(path=path, query=""))

        pairs = [(entry.canonical, entry.cache_value) for entry in entries]
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
        entry = rule.parse(options[present_aliases[0]], rule.canonical)
        if entry is not None:
            entries.append(entry)

    return entries


def _append_preset_to_path(pathname: str, preset: str) -> str:
    return f"{pathname}@{preset}"


def _create_transformation(canonical: str, cache_value: str) -> TransformationEntry:
    return TransformationEntry(canonical=canonical, cache_value=cache_value)


def _parse_width(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, str(_parse_positive_integer(value, canonical))
    )


def _parse_height(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, str(_parse_positive_integer(value, canonical))
    )


def _parse_resizing_type(value: Any, canonical: str) -> TransformationEntry:
    resizing_type = _parse_string(value, canonical)
    if resizing_type not in IMAGE_URL_RESIZING_TYPES:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(canonical, resizing_type)


def _parse_min_width(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, str(_parse_positive_integer(value, canonical))
    )


def _parse_min_height(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, str(_parse_positive_integer(value, canonical))
    )


def _parse_zoom(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, _stringify_number(_parse_positive_number(value, canonical))
    )


def _parse_dpr(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, _stringify_number(_parse_positive_number(value, canonical))
    )


def _parse_enlarge(value: Any, canonical: str) -> Optional[TransformationEntry]:
    return (
        _create_transformation(canonical, "true")
        if _parse_boolean(value, canonical)
        else None
    )


def _parse_extend(value: Any, canonical: str) -> Optional[TransformationEntry]:
    return _parse_extend_like(value, canonical)


def _parse_extend_aspect_ratio(
    value: Any, canonical: str
) -> Optional[TransformationEntry]:
    return _parse_extend_like(value, canonical)


def _parse_extend_like(value: Any, canonical: str) -> Optional[TransformationEntry]:
    raw = _parse_string(value, canonical)
    raw_extend, *raw_gravity_parts = raw.split(":")
    extend = _parse_boolean(raw_extend, canonical)
    if raw_gravity_parts:
        _parse_gravity_parts(raw_gravity_parts, canonical, allow_smart=False)
    if not extend:
        return None

    gravity = (
        _parse_gravity_parts(raw_gravity_parts, canonical, allow_smart=False)
        if raw_gravity_parts
        else ""
    )
    return _create_transformation(canonical, f"true:{gravity}" if gravity else "true")


def _parse_gravity(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical,
        _parse_gravity_parts(_parse_string(value, canonical).split(":"), canonical),
    )


def _parse_crop(value: Any, canonical: str) -> TransformationEntry:
    raw = _parse_string(value, canonical)
    raw_width, raw_height, *raw_gravity_parts = raw.split(":")
    width = _parse_positive_number(raw_width or "", canonical)
    height = _parse_positive_number(raw_height or "", canonical)
    gravity = (
        _parse_gravity_parts(raw_gravity_parts, canonical)
        if raw_gravity_parts
        else "ce:0:0"
    )
    return _create_transformation(
        canonical,
        f"{_stringify_number(width)}:{_stringify_number(height)}:{gravity}",
    )


def _parse_padding(value: Any, canonical: str) -> TransformationEntry:
    parts = _parse_string(value, canonical).split(":")
    if len(parts) < 1 or len(parts) > 4:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(
        canonical,
        ":".join(
            _stringify_number(_parse_non_negative_number(part, canonical))
            for part in parts
        ),
    )


def _parse_rotate(value: Any, canonical: str) -> TransformationEntry:
    rotate = _parse_integer(value, canonical, minimum=0, maximum=360)
    if rotate not in IMAGE_URL_ROTATE_ANGLES:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(canonical, str(rotate))


def _parse_flip(value: Any, canonical: str) -> TransformationEntry:
    parts = _parse_string(value, canonical).split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(
        canonical,
        ":".join(_serialize_boolean(_parse_boolean(part, canonical)) for part in parts),
    )


def _parse_background(value: Any, canonical: str) -> TransformationEntry:
    raw = _parse_string(value, canonical)
    parts = raw.split(":")
    if len(parts) == 3:
        return _create_transformation(
            canonical,
            ":".join(
                str(_parse_integer(part, canonical, minimum=0, maximum=255))
                for part in parts
            ),
        )

    hex_color = raw[1:] if raw.startswith("#") else raw
    if len(hex_color) not in {3, 6, 8} or any(
        character not in "0123456789abcdefABCDEF" for character in hex_color
    ):
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(canonical, hex_color.lower())


def _parse_blur(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, _stringify_number(_parse_non_negative_number(value, canonical))
    )


def _parse_sharpen(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, _stringify_number(_parse_non_negative_number(value, canonical))
    )


def _parse_pixelate(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, _stringify_number(_parse_positive_number(value, canonical))
    )


def _parse_boolean_transformation(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, "true" if _parse_boolean(value, canonical) else "false"
    )


def _parse_quality(value: Any, canonical: str) -> TransformationEntry:
    return _create_transformation(
        canonical, str(_parse_integer(value, canonical, minimum=0, maximum=100))
    )


def _parse_format(value: Any, canonical: str) -> TransformationEntry:
    image_format = _parse_string(value, canonical).lower()
    if image_format not in IMAGE_URL_OUTPUT_FORMATS:
        raise ValueError(f"Invalid transformation rule value for {canonical}")
    return _create_transformation(canonical, image_format)


def _parse_integer(
    value: Any,
    label: str,
    *,
    minimum: int = -(2**53) + 1,
    maximum: int = (2**53) - 1,
) -> int:
    raw = _stringify_value(value, label)
    if raw.startswith("-"):
        digits = raw[1:]
    else:
        digits = raw
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


def _parse_positive_integer(value: Any, label: str) -> int:
    return _parse_integer(value, label, minimum=1)


def _parse_non_negative_number(value: Any, label: str) -> float:
    return _parse_number(value, label, minimum=0)


def _parse_positive_number(value: Any, label: str) -> float:
    return _parse_number(value, label, minimum=0, min_exclusive=True)


def _parse_boolean(value: Any, label: str) -> bool:
    if isinstance(value, bool):
        return value
    raw = _stringify_value(value, label).lower()
    if raw in {"true", "t", "1"}:
        return True
    if raw in {"false", "f", "0"}:
        return False
    raise ValueError(f"Invalid transformation rule value for {label}")


def _serialize_boolean(value: bool) -> str:
    return "t" if value else "f"


def _parse_string(value: Any, label: str) -> str:
    return _stringify_value(value, label)


def _stringify_value(value: Any, label: str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    raise ValueError(f"Invalid transformation rule value for {label}")


def _stringify_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def _parse_gravity_parts(
    parts: list[str], label: str, *, allow_smart: bool = True
) -> str:
    if len(parts) not in {1, 2, 3}:
        raise ValueError(f"Invalid transformation rule value for {label}")

    gravity_type, *offsets = parts
    if gravity_type not in IMAGE_URL_GRAVITY_TYPES:
        raise ValueError(f"Invalid transformation rule value for {label}")

    if len(offsets) == 0:
        return gravity_type
    if len(offsets) == 1:
        if not allow_smart or offsets[0] != "sm":
            raise ValueError(f"Invalid transformation rule value for {label}")
        return f"{gravity_type}:sm"

    first_offset, second_offset = offsets
    _parse_integer(first_offset, label)
    _parse_integer(second_offset, label)
    return f"{gravity_type}:{first_offset}:{second_offset}"


RULES = (
    Rule(canonical="background", aliases=("bg", "background"), parse=_parse_background),
    Rule(canonical="blur", aliases=("bl", "blur"), parse=_parse_blur),
    Rule(canonical="crop", aliases=("c", "crop"), parse=_parse_crop),
    Rule(canonical="dpr", aliases=("dpr",), parse=_parse_dpr),
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
    Rule(canonical="gravity", aliases=("g", "gravity"), parse=_parse_gravity),
    Rule(canonical="height", aliases=("h", "height"), parse=_parse_height),
    Rule(
        canonical="keep_copyright",
        aliases=("kcr", "keep_copyright"),
        parse=_parse_boolean_transformation,
    ),
    Rule(canonical="min-height", aliases=("mh", "min-height"), parse=_parse_min_height),
    Rule(canonical="min-width", aliases=("mw", "min-width"), parse=_parse_min_width),
    Rule(canonical="padding", aliases=("pd", "padding"), parse=_parse_padding),
    Rule(canonical="pixelate", aliases=("pix", "pixelate"), parse=_parse_pixelate),
    Rule(canonical="quality", aliases=("q", "quality"), parse=_parse_quality),
    Rule(
        canonical="resizing_type",
        aliases=("resizing_type",),
        parse=_parse_resizing_type,
    ),
    Rule(canonical="rotate", aliases=("rot", "rotate"), parse=_parse_rotate),
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
    Rule(canonical="width", aliases=("w", "width"), parse=_parse_width),
    Rule(canonical="zoom", aliases=("z", "zoom"), parse=_parse_zoom),
)
