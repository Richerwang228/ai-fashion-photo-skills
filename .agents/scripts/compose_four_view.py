#!/usr/bin/env python3
"""Compose four independently generated photos into one clean contact sheet."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageOps


def compose(
    inputs: Sequence[Path],
    output: Path,
    *,
    panel_width: int = 800,
    height: int = 1600,
    gap: int = 16,
) -> None:
    if len(inputs) != 4:
        raise ValueError("Exactly four input images are required.")
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing input image(s): " + ", ".join(missing))
    if panel_width <= 0 or height <= 0 or gap < 0:
        raise ValueError("panel_width and height must be positive; gap cannot be negative.")

    canvas_width = panel_width * 4 + gap * 3
    canvas = Image.new("RGB", (canvas_width, height), "white")

    for index, path in enumerate(inputs):
        with Image.open(path) as source:
            source_rgb = ImageOps.exif_transpose(source).convert("RGB")
            panel = ImageOps.fit(
                source_rgb,
                (panel_width, height),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
        canvas.paste(panel, (index * (panel_width + gap), 0))

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compose portrait, front, side, and back photos into a four-view PNG."
    )
    parser.add_argument("portrait", type=Path)
    parser.add_argument("front", type=Path)
    parser.add_argument("side", type=Path)
    parser.add_argument("back", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--panel-width", type=int, default=800)
    parser.add_argument("--height", type=int, default=1600)
    parser.add_argument("--gap", type=int, default=16)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    compose(
        [args.portrait, args.front, args.side, args.back],
        args.output,
        panel_width=args.panel_width,
        height=args.height,
        gap=args.gap,
    )
    print(f"Saved: {args.output.expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
