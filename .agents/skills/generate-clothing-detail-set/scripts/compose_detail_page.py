#!/usr/bin/env python3
"""Assemble final AI-rendered modules into a deterministic vertical long page.

The default path never adds or redraws text, labels, arrows, tables, or other
annotations.  Each input module is already a finished ecommerce image.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from common import ValidationError, clean_text, dump_json, load_json, resolve_path, validate_local_image


def _pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except ImportError as exc:
        raise ValidationError("Pillow is required for deterministic page composition") from exc
    return Image, ImageDraw, ImageFont, ImageOps


def _font_path(raw: str = "") -> str:
    candidates = [
        raw,
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for value in candidates:
        if value and Path(value).expanduser().is_file():
            return str(Path(value).expanduser())
    return ""


def _font(ImageFont: Any, path: str, size: int):
    if path:
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _color(value: Any, fallback: str = "#FFFFFF") -> str:
    text = clean_text(value)
    return text if text.startswith("#") and len(text) in {4, 7, 9} else fallback


def _fit_image(Image: Any, ImageOps: Any, source: Any, width: int, height: int, fit: str):
    image = source.convert("RGB")
    if fit == "cover":
        return ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    contained = ImageOps.contain(image, (width, height), method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (width, height), "#F7F5F1")
    canvas.paste(contained, ((width - contained.width) // 2, (height - contained.height) // 2))
    return canvas


def _rounded_mask(Image: Any, ImageDraw: Any, size: tuple[int, int], radius: int):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def _wrap(draw: Any, text: str, font: Any, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def _asset_values(raw: Any) -> list[str]:
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [clean_text(item) for item in raw if clean_text(item)]
    if isinstance(raw, dict):
        values = raw.get("assets", raw.get("paths", raw.get("path", [])))
        return _asset_values(values)
    return []


def _resolve_assets(module: dict[str, Any], asset_map: dict[str, Any], base_dir: Path) -> list[Path]:
    raw = asset_map.get(module["id"], asset_map.get(module.get("source_slot_id", ""), []))
    paths: list[Path] = []
    for value in _asset_values(raw):
        path = resolve_path(value, base_dir=base_dir)
        ok, reason = validate_local_image(value, base_dir=base_dir)
        if path is None or not ok:
            raise ValidationError(f"module {module['id']} asset is invalid ({value}): {reason}")
        paths.append(path)
    if not paths:
        raise ValidationError(f"module {module['id']} has no assets in the asset map")
    return paths


def _render_module(
    module: dict[str, Any],
    paths: list[Path],
    *,
    font_path: str,
    assembly_only: bool,
) -> Any:
    Image, ImageDraw, ImageFont, ImageOps = _pillow()
    width = 750
    height = int(module.get("height", 760))
    canvas = Image.new("RGB", (width, height), _color(module.get("background"), "#F3F0EA"))
    draw = ImageDraw.Draw(canvas)
    if assembly_only:
        if len(paths) != 1:
            raise ValidationError(
                f"module {module.get('id', 'module')} requires exactly one final AI-rendered image; found {len(paths)}"
            )
        with Image.open(paths[0]) as source:
            return _fit_image(Image, ImageOps, source, width, height, "contain")
    regions = module.get("regions") if isinstance(module.get("regions"), list) else []
    for index, region in enumerate(regions):
        source_path = paths[min(index, len(paths) - 1)]
        with Image.open(source_path) as source:
            rw, rh = int(region["width"]), int(region["height"])
            fitted = _fit_image(Image, ImageOps, source, rw, rh, clean_text(region.get("fit", "contain")))
        x, y = int(region["x"]), int(region["y"])
        radius = int(region.get("radius", 0) or 0)
        if radius:
            canvas.paste(fitted, (x, y), _rounded_mask(Image, ImageDraw, (rw, rh), radius))
        else:
            canvas.paste(fitted, (x, y))

    for annotation in module.get("annotations", []):
        target = annotation.get("target", {})
        anchor = annotation.get("label_anchor", {})
        tx, ty = int(target.get("x", 0)), int(target.get("y", 0))
        ax, ay = int(anchor.get("x", 0)), int(anchor.get("y", 0))
        color = _color(annotation.get("color"), "#566675")
        draw.line((ax, ay, (ax + tx) // 2, ay, tx, ty), fill=color, width=3, joint="curve")
        draw.ellipse((tx - 6, ty - 6, tx + 6, ty + 6), fill=color)
        label_font = _font(ImageFont, font_path, 22)
        label = clean_text(annotation.get("label", ""))
        draw.text((ax, ay - 34), label, font=label_font, fill=color)

    table = module.get("table") if isinstance(module.get("table"), dict) else None
    if table:
        columns = table.get("columns", [])
        rows = table.get("rows", [])
        x, y = int(table.get("x", 48)), int(table.get("y", 190))
        width = int(table.get("width", 340))
        row_height = int(table.get("row_height", 48))
        cell_width = max(1, width // max(1, len(columns)))
        table_font = _font(ImageFont, font_path, 18)
        all_rows = [columns] + rows
        for row_index, row in enumerate(all_rows):
            fill = "#E7E2DA" if row_index == 0 else ("#FFFFFF" if row_index % 2 else "#F7F5F1")
            for column_index, value in enumerate(row):
                left = x + column_index * cell_width
                top = y + row_index * row_height
                draw.rectangle((left, top, left + cell_width, top + row_height), fill=fill, outline="#D0CBC3", width=1)
                draw.text((left + 8, top + 13), clean_text(value), font=table_font, fill="#242424")

    for layer in module.get("text_layers", []):
        text = clean_text(layer.get("text", ""))
        if not text:
            continue
        size = max(22, int(layer.get("size", 24)))
        font = _font(ImageFont, font_path, size)
        x, y = int(layer.get("x", 48)), int(layer.get("y", 48))
        max_width = int(layer.get("width", 654))
        line_height = int(size * float(layer.get("line_height", 1.35)))
        for line in _wrap(draw, text, font, max_width):
            draw.text((x, y), line, font=font, fill=_color(layer.get("color"), "#171717"))
            y += line_height
    return canvas


def compose(
    blueprint: dict[str, Any],
    asset_map: dict[str, Any],
    *,
    base_dir: Path,
    output: Path,
    slices_dir: Path | None = None,
    font_override: str = "",
    overwrite: bool = False,
) -> dict[str, Any]:
    Image, ImageDraw, _, _ = _pillow()
    if output.exists() and not overwrite:
        raise ValidationError(f"output exists; refuse to overwrite: {output}")
    modules = blueprint.get("modules") if isinstance(blueprint.get("modules"), list) else []
    if not 6 <= len(modules) <= 10:
        raise ValidationError("blueprint must contain 6-10 modules")
    font_path = _font_path(font_override)
    page_contract = blueprint.get("page") if isinstance(blueprint.get("page"), dict) else {}
    assembly_only = page_contract.get("text_rendering") == "ai_embedded_per_module"
    rendered: list[tuple[dict[str, Any], Any, list[Path]]] = []
    for module in modules:
        paths = _resolve_assets(module, asset_map, base_dir)
        rendered.append((module, _render_module(module, paths, font_path=font_path, assembly_only=assembly_only), paths))
    gap = int((blueprint.get("page") or {}).get("module_gap", 24))
    total_height = sum(image.height for _, image, _ in rendered) + gap * (len(rendered) - 1)
    page = Image.new("RGB", (750, total_height), _color((blueprint.get("page") or {}).get("background"), "#F3F0EA"))
    y = 0
    manifest_modules: list[dict[str, Any]] = []
    if slices_dir:
        slices_dir.mkdir(parents=True, exist_ok=True)
    for index, (module, image, paths) in enumerate(rendered, 1):
        page.paste(image, (0, y))
        slice_path = None
        if slices_dir:
            slice_path = slices_dir / f"{index:02d}_{module['id']}.png"
            image.save(slice_path, format="PNG")
        manifest_modules.append({
            "id": module["id"],
            "template": module.get("template"),
            "y": y,
            "height": image.height,
            "assets": [str(path) for path in paths],
            "slice": str(slice_path) if slice_path else None,
            "local_text_overlay_count": 0 if assembly_only else len(module.get("text_layers", [])),
            "local_annotation_overlay_count": 0 if assembly_only else len(module.get("annotations", [])),
            "embedded_text_expected": assembly_only,
        })
        y += image.height + gap
    output.parent.mkdir(parents=True, exist_ok=True)
    page.save(output, format="PNG")
    return {
        "schema_version": "1.0",
        "classification": "composed_mobile_product_detail_page",
        "output": str(output),
        "width": page.width,
        "height": page.height,
        "module_count": len(rendered),
        "layout_engine": "deterministic_pillow_vertical_assembly",
        "assembly_only": assembly_only,
        "local_text_overlays": not assembly_only,
        "font_path": None if assembly_only else (font_path or "Pillow default"),
        "modules": manifest_modules,
        "status": "rendered_needs_mobile_visual_qa",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("blueprint")
    parser.add_argument("--assets", required=True, help="JSON mapping module ids to local image paths")
    parser.add_argument("--out", "-o", required=True)
    parser.add_argument("--slices-dir")
    parser.add_argument("--manifest-out")
    parser.add_argument("--font")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        blueprint_path = Path(args.blueprint).expanduser().resolve()
        assets_path = Path(args.assets).expanduser().resolve()
        blueprint = load_json(blueprint_path)
        asset_map = load_json(assets_path)
        if not isinstance(blueprint, dict) or not isinstance(asset_map, dict):
            raise ValidationError("blueprint and asset map must be JSON objects")
        result = compose(
            blueprint,
            asset_map,
            base_dir=assets_path.parent,
            output=Path(args.out).expanduser().resolve(),
            slices_dir=Path(args.slices_dir).expanduser().resolve() if args.slices_dir else None,
            font_override=clean_text(args.font),
            overwrite=args.overwrite,
        )
        dump_json(result, args.manifest_out)
        return 0
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
