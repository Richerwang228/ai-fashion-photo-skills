#!/usr/bin/env python3
"""Assemble local detail images into a non-destructive vertical preview.

The preview is a convenience package artifact, not a generation step.  Pillow
is optional: the rest of the planning/validation scripts remain stdlib-only,
and this command explains how to install Pillow when it is unavailable.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import ValidationError


def _load_pillow() -> tuple[Any, Any]:
    """Import Pillow lazily so planning works without a binary dependency."""

    try:
        from PIL import Image, ImageOps
    except ImportError as exc:  # pragma: no cover - depends on the host image
        raise ValidationError(
            "Pillow is required for assemble_preview.py; install it with "
            "'python3 -m pip install Pillow' and retry"
        ) from exc
    return Image, ImageOps


def _input_paths(positional: list[str], flagged: list[str] | None) -> list[Path]:
    values = list(positional)
    if flagged:
        values.extend(flagged)
    if not values:
        raise ValidationError("at least one input image is required")

    paths: list[Path] = []
    seen: set[Path] = set()
    for raw in values:
        path = Path(raw).expanduser().resolve()
        if path in seen:
            raise ValidationError(f"duplicate input image: {path}")
        if not path.is_file():
            raise ValidationError(f"input image file does not exist: {path}")
        seen.add(path)
        paths.append(path)
    return paths


def _background(value: str, image_module: Any) -> tuple[int, int, int, int]:
    """Parse a small CSS-like background color accepted by Pillow."""

    try:
        parsed = image_module.new("RGBA", (1, 1), value).getpixel((0, 0))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"invalid background color: {value}") from exc
    return tuple(parsed)


def assemble_preview(
    inputs: list[Path],
    output: Path,
    *,
    width: int | None = None,
    background: str = "white",
) -> dict[str, Any]:
    """Vertically concatenate *inputs* into a new image at *output*.

    If ``width`` is provided, each image is scaled to that width while its
    aspect ratio is retained.  Without it, source pixels are kept at their
    native size and the canvas uses the widest source image.  Existing output
    files are rejected so a preview can never silently replace an artifact.
    """

    if width is not None and width <= 0:
        raise ValidationError("--width must be a positive integer")
    image_module, image_ops = _load_pillow()

    destination = output.expanduser().resolve()
    if destination.exists():
        raise ValidationError(f"refusing to overwrite existing preview: {destination}")
    input_resolved = {path.expanduser().resolve() for path in inputs}
    if destination in input_resolved:
        raise ValidationError("output preview must be different from every input image")

    opened: list[Any] = []
    try:
        for path in inputs:
            try:
                image = image_module.open(path)
                image.load()
            except (OSError, ValueError) as exc:
                raise ValidationError(f"cannot open input image {path}: {exc}") from exc
            # EXIF orientation belongs to the source file, not to the preview
            # layout.  Normalize it before measuring dimensions.
            image = image_ops.exif_transpose(image)
            if width is not None and image.width != width:
                height = max(1, round(image.height * width / image.width))
                image = image.resize((width, height), image_module.Resampling.LANCZOS)
            opened.append(image.convert("RGBA"))

        canvas_width = width or max(image.width for image in opened)
        canvas_height = sum(image.height for image in opened)
        fill = _background(background, image_module)
        canvas = image_module.new("RGBA", (canvas_width, canvas_height), fill)
        top = 0
        for image in opened:
            left = (canvas_width - image.width) // 2
            canvas.alpha_composite(image, (left, top))
            top += image.height

        destination.parent.mkdir(parents=True, exist_ok=True)
        suffix = destination.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            # JPEG has no alpha channel; flatten only at this final export
            # boundary and keep the transparent-safe canvas internally.
            flattened = image_module.new("RGB", canvas.size, fill[:3])
            flattened.paste(canvas, mask=canvas.getchannel("A"))
            flattened.save(destination, format="JPEG", quality=95)
        else:
            canvas.save(destination, format="PNG")
    finally:
        for image in opened:
            image.close()

    return {
        "output": str(destination),
        "inputs": [str(path) for path in inputs],
        "width": canvas_width,
        "height": canvas_height,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="*", help="input image paths in top-to-bottom order")
    parser.add_argument("--inputs", nargs="+", dest="input_flags", help="additional input image paths")
    parser.add_argument("--output", "--out", "-o", required=True, help="new preview path")
    parser.add_argument("--width", type=int, help="optional target width; aspect ratio is preserved")
    parser.add_argument("--background", default="white", help="Pillow color used behind transparent images")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        inputs = _input_paths(args.images, args.input_flags)
        result = assemble_preview(inputs, Path(args.output), width=args.width, background=args.background)
        # A compact machine-readable summary is useful in a delivery log while
        # keeping the image itself as the only generated artifact.
        print(f"assembled {len(inputs)} images -> {result['output']} ({result['width']}x{result['height']})")
        return 0
    except (ValidationError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
