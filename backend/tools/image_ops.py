"""Image edit operations (Pillow).

Each operation is a dict like {"op": "brightness", "factor": 1.3}. Positions and
sizes are fractions of the picture (0–1), because Claude only sees a small copy
and can't know exact pixel coordinates.
"""

from typing import Any, Callable

from PIL import Image, ImageColor, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

Op = dict[str, Any]

MAX_SIDE = 6000
FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


class EditError(ValueError):
    """A problem with the requested edit; the message goes back to Claude."""


def _num(op: Op, key: str, default: float | None = None, lo: float | None = None, hi: float | None = None) -> float:
    value = op.get(key, default)
    if value is None:
        raise EditError(f"{op.get('op')}: '{key}' is required")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise EditError(f"{op.get('op')}: '{key}' must be a number") from None
    if (lo is not None and value < lo) or (hi is not None and value > hi):
        raise EditError(f"{op.get('op')}: '{key}' must be between {lo} and {hi}")
    return value


def _color(op: Op, key: str, default: str) -> tuple[int, ...]:
    try:
        return ImageColor.getrgb(str(op.get(key, default)))
    except ValueError:
        raise EditError(f"{op.get('op')}: unknown color {op.get(key)!r}") from None


def _rgb(img: Image.Image) -> Image.Image:
    return img if img.mode == "RGB" else img.convert("RGB")


# ---- Operations ---------------------------------------------------------------------

def crop(img: Image.Image, op: Op) -> Image.Image:
    w, h = img.size
    if "aspect" in op:  # centred crop to an aspect ratio, e.g. "1:1", "16:9"
        try:
            aw, ah = (float(x) for x in str(op["aspect"]).split(":"))
            target = aw / ah
        except (ValueError, ZeroDivisionError):
            raise EditError("crop: aspect must look like '16:9'") from None
        if w / h > target:
            new_w = round(h * target)
            box = ((w - new_w) // 2, 0, (w - new_w) // 2 + new_w, h)
        else:
            new_h = round(w / target)
            box = (0, (h - new_h) // 2, w, (h - new_h) // 2 + new_h)
        return img.crop(box)
    left = _num(op, "left", 0, 0, 1)
    top = _num(op, "top", 0, 0, 1)
    right = _num(op, "right", 1, 0, 1)
    bottom = _num(op, "bottom", 1, 0, 1)
    if right - left < 0.02 or bottom - top < 0.02:
        raise EditError("crop: the area is too small (right > left and bottom > top, as fractions 0–1)")
    return img.crop((round(left * w), round(top * h), round(right * w), round(bottom * h)))


def resize(img: Image.Image, op: Op) -> Image.Image:
    w, h = img.size
    if "scale" in op:
        s = _num(op, "scale", lo=0.05, hi=4)
        size = (round(w * s), round(h * s))
    elif "width" in op and "height" in op:
        size = (int(_num(op, "width", lo=8, hi=MAX_SIDE)), int(_num(op, "height", lo=8, hi=MAX_SIDE)))
    elif "width" in op:
        nw = int(_num(op, "width", lo=8, hi=MAX_SIDE))
        size = (nw, round(h * nw / w))
    elif "height" in op:
        nh = int(_num(op, "height", lo=8, hi=MAX_SIDE))
        size = (round(w * nh / h), nh)
    else:
        raise EditError("resize: give scale, width and/or height")
    if max(size) > MAX_SIDE:
        raise EditError(f"resize: the result would be larger than {MAX_SIDE}px")
    return img.resize(size, Image.Resampling.LANCZOS)


def rotate(img: Image.Image, op: Op) -> Image.Image:
    degrees = _num(op, "degrees", lo=-360, hi=360)  # positive = clockwise
    if degrees % 90 == 0:
        turns = {90: Image.Transpose.ROTATE_270, 180: Image.Transpose.ROTATE_180, 270: Image.Transpose.ROTATE_90}
        t = turns.get(int(degrees) % 360)
        return img.transpose(t) if t else img
    return _rgb(img).rotate(-degrees, expand=True, resample=Image.Resampling.BICUBIC,
                            fillcolor=_color(op, "fill", "white"))


def flip(img: Image.Image, op: Op) -> Image.Image:
    direction = op.get("direction", "horizontal")
    if direction == "horizontal":
        return ImageOps.mirror(img)
    if direction == "vertical":
        return ImageOps.flip(img)
    raise EditError("flip: direction must be 'horizontal' or 'vertical'")


def _enhance(kind: type) -> Callable[[Image.Image, Op], Image.Image]:
    def apply(img: Image.Image, op: Op) -> Image.Image:
        return kind(_rgb(img)).enhance(_num(op, "factor", lo=0, hi=5))  # 1 = unchanged
    return apply


def sharpen(img: Image.Image, op: Op) -> Image.Image:
    return ImageEnhance.Sharpness(_rgb(img)).enhance(_num(op, "factor", 2, 0, 5))


def blur(img: Image.Image, op: Op) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(_num(op, "radius", 4, 0, 60)))


def grayscale(img: Image.Image, op: Op) -> Image.Image:
    return ImageOps.grayscale(img).convert("RGB")


def sepia(img: Image.Image, op: Op) -> Image.Image:
    gray = ImageOps.grayscale(img)
    return ImageOps.colorize(gray, black="#2e1f0f", white="#fff2d6", mid="#a0785a")


def _font(px: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, px)
        except OSError:
            continue
    return ImageFont.load_default(px)


POSITIONS = {"top", "center", "bottom", "top-left", "top-right", "bottom-left", "bottom-right"}


def add_text(img: Image.Image, op: Op) -> Image.Image:
    text = str(op.get("text") or "").strip()
    if not text:
        raise EditError("add_text: 'text' is required")
    position = op.get("position", "bottom")
    if position not in POSITIONS:
        raise EditError(f"add_text: position must be one of {sorted(POSITIONS)}")
    img = _rgb(img).copy()
    w, h = img.size
    px = max(10, round(h * _num(op, "size", 0.08, 0.02, 0.4)))  # text height as a fraction of image height
    font = _font(px)
    draw = ImageDraw.Draw(img)
    stroke = max(1, px // 14) if op.get("outline", True) else 0
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    tw, th = right - left, bottom - top
    margin = round(min(w, h) * 0.04)
    x = {"left": margin, "right": w - tw - margin}.get(position.split("-")[-1], (w - tw) // 2)
    y = {"top": margin, "bottom": h - th - margin}.get(position.split("-")[0], (h - th) // 2)
    draw.text((x - left, y - top), text, font=font, fill=_color(op, "color", "white"),
              stroke_width=stroke, stroke_fill=_color(op, "outline_color", "black"))
    return img


def add_border(img: Image.Image, op: Op) -> Image.Image:
    width = max(1, round(min(img.size) * _num(op, "width", 0.03, 0.002, 0.3)))  # fraction of the shorter side
    return ImageOps.expand(_rgb(img), border=width, fill=_color(op, "color", "white"))


OPERATIONS: dict[str, Callable[[Image.Image, Op], Image.Image]] = {
    "crop": crop,
    "resize": resize,
    "rotate": rotate,
    "flip": flip,
    "brightness": _enhance(ImageEnhance.Brightness),
    "contrast": _enhance(ImageEnhance.Contrast),
    "saturation": _enhance(ImageEnhance.Color),
    "sharpen": sharpen,
    "blur": blur,
    "grayscale": grayscale,
    "sepia": sepia,
    "add_text": add_text,
    "add_border": add_border,
}


def apply_all(img: Image.Image, operations: list[Op]) -> tuple[Image.Image, str]:
    """Apply operations in order. Returns the new image and a short note like 'crop, sepia'."""
    if not operations:
        raise EditError("No operations given")
    if len(operations) > 20:
        raise EditError("Too many operations at once (max 20)")
    for i, op in enumerate(operations, 1):
        if not isinstance(op, dict) or op.get("op") not in OPERATIONS:
            raise EditError(f"Operation {i}: 'op' must be one of {sorted(OPERATIONS)}")
        img = OPERATIONS[op["op"]](img, op)
    note = ", ".join(str(op["op"]).replace("_", " ") for op in operations)
    return img, note
