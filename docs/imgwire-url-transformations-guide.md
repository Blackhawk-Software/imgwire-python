# Imgwire URL Transformations Guide

Imgwire Fetch Worker accepts image transformation requests as URL query
parameters and converts them into the canonical `imgwire-viper` JSON
`transforms` object.

Example:

```text
https://cdn.imgwire.dev/org/env/image?width=800&height=600&resizing_type=cover&format=webp&q=80
```

Equivalent Viper transform payload:

```json
{
  "width": 800,
  "height": 600,
  "resizing_type": "cover",
  "format": "webp",
  "quality": 80
}
```

## General Rules

- Query parameter names may use the canonical transform name or any listed
  alias.
- Each canonical transform may appear at most once. For example,
  `?width=100&w=200` is rejected because both map to `width`.
- Multi-field values use colon-delimited syntax unless the table says
  otherwise.
- Object-style transforms also accept URL-encoded JSON objects where noted.
- Colors may be `rgb`, `rrggbb`, `rrggbbaa`, `#rgb`, `#rrggbb`,
  `#rrggbbaa`, or `r:g:b[:alpha]`. When using a leading `#` in a URL,
  encode it as `%23`; raw `#` starts the URL fragment and will not reach the
  Worker as part of the query value.
- `format=auto` asks the Worker to negotiate the output format from `Accept`.
  Omitted `format` behaves like `format=auto`.
- The Worker canonicalizes accepted query values before building cache keys.

## Gravity Values

Viper accepts:

```text
ce, center, north, south, east, west, northeast, northwest, southeast, southwest, attention, entropy
```

Imgwire also accepts these shorthand URL values and sends the full Viper value:

| Shorthand    | Viper value |
| ------------ | ----------- |
| `n`, `no`    | `north`     |
| `s`, `so`    | `south`     |
| `e`, `ea`    | `east`      |
| `w`, `we`    | `west`      |
| `ne`, `noea` | `northeast` |
| `se`, `soea` | `southeast` |
| `nw`, `nowe` | `northwest` |
| `sw`, `sowe` | `southwest` |

`ce:sm` is accepted for compatibility and maps to `attention`.

## Supported Transformations

| Canonical transform   | Aliases                                         | URL value syntax                                                                                                                                              | Viper payload                                             |
| --------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| `adjust`              | `a`, `adjust`                                   | `brightness[:saturation[:color]]` or JSON object                                                                                                              | `{ "brightness": n, "saturation"?: n, "color"?: n }`      |
| `background`          | `bg`, `background`                              | color                                                                                                                                                         | color                                                     |
| `background_alpha`    | `bga`, `background_alpha`                       | `0..1`                                                                                                                                                        | number                                                    |
| `blur`                | `bl`, `blur`                                    | `true` or sigma `0.3..100`                                                                                                                                    | `true` or number                                          |
| `brightness`          | `br`, `brightness`                              | `0.01..10`                                                                                                                                                    | number                                                    |
| `color_profile`       | `cp`, `icc`, `color_profile`                    | `srgb`, `rgb16`, `cmyk`, `keep`, `preserve`                                                                                                                   | string                                                    |
| `colorize`            | `col`, `colorize`                               | color                                                                                                                                                         | color                                                     |
| `contrast`            | `co`, `contrast`                                | `multiplier[:pivot]` or JSON object                                                                                                                           | number or `{ "multiplier": n, "pivot"?: n }`              |
| `crop`                | `c`, `crop`                                     | `width:height[:gravity]`, `x:y:width:height[:gravity]`, or JSON object                                                                                        | crop object                                               |
| `dpi`                 | `dpi`                                           | integer `1..600`                                                                                                                                              | number                                                    |
| `dpr`                 | `dpr`                                           | `0.01..8`                                                                                                                                                     | number                                                    |
| `duotone`             | `dt`, `duotone`                                 | `shadowColor:highlightColor` or JSON object                                                                                                                   | `{ "shadowColor": color, "highlightColor": color }`       |
| `enlarge`             | `el`, `enlarge`                                 | boolean                                                                                                                                                       | boolean                                                   |
| `extend`              | `ex`, `extend`                                  | `top[:right[:bottom[:left[:background]]]]` or JSON object                                                                                                     | `{ "top"?, "right"?, "bottom"?, "left"?, "background"? }` |
| `extend_aspect_ratio` | `exar`, `extend_ar`, `extend_aspect_ratio`      | ratio number, `width:height`, or JSON object                                                                                                                  | number, string, or object                                 |
| `flip`                | `fl`, `flip`                                    | `vertical`, `horizontal`, `both`, or legacy `horizontalBool:verticalBool`                                                                                     | string                                                    |
| `format`              | `f`, `format`, `ext`, `extension`               | `auto`, `jpg`, `jpeg`, `png`, `webp`, `avif`, `gif`, `tiff`                                                                                                   | output format string; `jpg` maps to `jpeg`                |
| `gradient`            | `gr`, `gradient`                                | `color1,color2[,colorN][:angle[:opacity[:blend]]]` or JSON object                                                                                             | gradient object                                           |
| `gravity`             | `g`, `gravity`                                  | gravity                                                                                                                                                       | string                                                    |
| `height`              | `h`, `height`                                   | integer `1..8192`                                                                                                                                             | number                                                    |
| `hue`                 | `hu`, `hue`                                     | number                                                                                                                                                        | number                                                    |
| `keep_copyright`      | `kcr`, `keep_copyright`                         | boolean                                                                                                                                                       | boolean                                                   |
| `lightness`           | `l`, `lightness`                                | `0.01..10`                                                                                                                                                    | number                                                    |
| `min-height`          | `mh`, `min_height`, `min-height`                | integer `1..8192`                                                                                                                                             | number                                                    |
| `min-width`           | `mw`, `min_width`, `min-width`                  | integer `1..8192`                                                                                                                                             | number                                                    |
| `monochrome`          | `mc`, `monochrome`                              | `true`, `false`, or color; `false` is a no-op                                                                                                                 | `true` or color                                           |
| `negate`              | `neg`, `negate`                                 | `true` or `alpha:boolean`                                                                                                                                     | `true` or `{ "alpha": boolean }`                          |
| `normalize`           | `norm`, `normalise`, `normalize`                | boolean or `lower:upper`                                                                                                                                      | boolean or `{ "lower": n, "upper": n }`                   |
| `padding`             | `pd`, `padding`                                 | `all`, `x:y`, `top:x:bottom`, `top:right:bottom:left`, or JSON object                                                                                         | number or padding object                                  |
| `pixelate`            | `pix`, `pixelate`                               | integer `2..256`                                                                                                                                              | number                                                    |
| `quality`             | `q`, `quality`                                  | integer `1..100`                                                                                                                                              | number                                                    |
| `resizing_algorithm`  | `ra`, `resizing_algorithm`                      | `nearest`, `cubic`, `mitchell`, `lanczos2`, `lanczos3`                                                                                                        | string                                                    |
| `resizing_type`       | `resizing_type`                                 | `cover`, `contain`, `fill`, `inside`, `outside`; legacy `fit` maps to `inside`, `fill-down` maps to `inside`, `force` maps to `fill`, `auto` maps to `inside` | string                                                    |
| `rotate`              | `rot`, `rotate`                                 | `angle`, `angle:background`, or JSON object                                                                                                                   | number or `{ "angle": n, "background"?: color }`          |
| `saturation`          | `sa`, `saturation`                              | `0.01..10`                                                                                                                                                    | number                                                    |
| `sharpen`             | `sh`, `sharpen`                                 | `true`, sigma number, or JSON object                                                                                                                          | `true` or sharpen object                                  |
| `strip_color_profile` | `scp`, `strip_color_profile`                    | boolean                                                                                                                                                       | boolean                                                   |
| `strip_metadata`      | `sm`, `strip_metadata`                          | boolean                                                                                                                                                       | boolean                                                   |
| `watermark`           | `wm`, `watermark`                               | `image_id[:gravity[:x[:y]]]` or JSON object with `image_id`/`imageId`                                                                                         | watermark source object resolved to internal bucket/key   |
| `watermark_position`  | `wmp`, `watermark_offset`, `watermark_position` | `gravity[:x[:y[:opacity[:blend]]]]` or JSON object                                                                                                            | watermark placement object                                |
| `watermark_rotate`    | `wmr`, `wm_rot`, `watermark_rotate`             | `angle`, `angle:background`, or JSON object                                                                                                                   | number or rotate object                                   |
| `watermark_shadow`    | `wmsh`, `watermark_shadow`                      | `true`, `color[:blur[:x[:y]]]`, or JSON object                                                                                                                | `true` or shadow object                                   |
| `watermark_size`      | `wms`, `watermark_size`                         | `width[:height[:scale]]` or JSON object                                                                                                                       | watermark size object                                     |
| `watermark_text`      | `wmt`, `watermark_text`                         | text string or JSON object                                                                                                                                    | string or text object                                     |
| `watermark_url`       | `wmu`, `watermark_url`                          | base64-encoded public HTTPS URL                                                                                                                               | string                                                    |
| `width`               | `w`, `width`                                    | integer `1..8192`                                                                                                                                             | number                                                    |
| `zoom`                | `z`, `zoom`                                     | `factor` or `factor:gravity`                                                                                                                                  | number or `{ "factor": n, "gravity"?: gravity }`          |

## Examples

Resize and automatic WebP negotiation:

```text
?w=800&h=600&resizing_type=cover
```

Explicit JPEG output:

```text
?width=1200&format=jpg&q=85
```

Region crop with shorthand gravity:

```text
?crop=400:300:noea
```

Watermark from a public URL:

```text
?watermark_url=aHR0cHM6Ly9leGFtcGxlLmNvbS9sb2dvLnBuZw==&watermark_position=southeast:-24:-24:0.85&format=webp
```

Watermark from an Imgwire image ID:

```text
?watermark=logo_image_id&watermark_position=se:-24:-24&format=webp
```

Watermark bucket and key values are internal and are not accepted in the URL.
The Worker resolves the supplied image ID and verifies it belongs to the same
organization and environment before sending the bucket/key to Imgwire-Viper.

JSON object values must be URL-encoded by clients:

```text
?duotone=%7B%22shadowColor%22%3A%22%230b1f5e%22%2C%22highlightColor%22%3A%22%23ff2a2a%22%7D
```
