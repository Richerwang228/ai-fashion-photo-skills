#!/usr/bin/env python3
"""Convert an approved clothing plan into a mobile PDP module blueprint.

This script is local-only.  It creates layout guidance for one-pass AI module
generation; it never calls an image provider.  The generated module image must
already contain its approved Chinese copy and callouts before page assembly.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from common import ValidationError, clean_text, dump_json, load_json


WIDTH = 750
SAFE_X = 48
GAP = 24

MODULE_SPECS = {
    "product-hero": ("hero", 920),
    "model-hero": ("fit-context", 980),
    "non-model-editorial": ("editorial-context", 900),
    "front-back-fit": ("two-up-evidence", 860),
    "macro-material": ("detail-grid", 820),
    "construction-selling-point": ("feature-callout", 860),
    "lifestyle-use": ("scene", 920),
    "size-module": ("fit-guide", 760),
    "fit-evidence": ("fit-guide", 760),
    "brand-close": ("brand-close", 640),
}

DEFAULT_ORDER = {
    "product-hero": 10,
    "model-hero": 20,
    "non-model-editorial": 20,
    "front-back-fit": 30,
    "construction-selling-point": 40,
    "macro-material": 50,
    "lifestyle-use": 60,
    "size-module": 70,
    "fit-evidence": 70,
    "brand-close": 80,
}

MODULE_TITLES = {
    "product-hero": "一眼看清这件衣服",
    "model-hero": "上身比例与整体廓形",
    "non-model-editorial": "整件轮廓与风格",
    "front-back-fit": "正背面都看清",
    "construction-selling-point": "结构细节，近一点看",
    "macro-material": "面料与表面质感",
    "lifestyle-use": "日常搭配参考",
    "size-module": "版型与尺码参考",
    "fit-evidence": "版型与穿着参考",
    "brand-close": "关于这件衣服",
}


def _has_cjk(value: Any) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in clean_text(value))


def _base_id(slot: dict[str, Any]) -> str:
    return clean_text(slot.get("base_slot_id", slot.get("id", "slot")))


def _height_for_aspect(slot: dict[str, Any], fallback: int) -> int:
    raw = clean_text(slot.get("aspect_ratio", ""))
    try:
        width, height = (float(part) for part in raw.split(":", 1))
        if width > 0 and height > 0:
            return max(600, min(1200, round(WIDTH * height / width)))
    except (TypeError, ValueError):
        pass
    return fallback


def _scale_vertical(items: list[dict[str, Any]], scale: float) -> list[dict[str, Any]]:
    output = copy.deepcopy(items)
    for item in output:
        for key in ("y", "height"):
            if key in item:
                item[key] = round(float(item[key]) * scale)
        for point_key in ("target", "label_anchor"):
            if isinstance(item.get(point_key), dict) and "y" in item[point_key]:
                item[point_key]["y"] = round(float(item[point_key]["y"]) * scale)
    return output


def _hex_palette(plan: dict[str, Any]) -> dict[str, str]:
    # The selected direction may contain prose rather than color codes.  Keep a
    # stable neutral base and let a user-approved theme override exact tokens.
    theme = plan.get("page_theme") if isinstance(plan.get("page_theme"), dict) else {}
    return {
        "paper": clean_text(theme.get("paper", "#F3F0EA")),
        "surface": clean_text(theme.get("surface", "#E4E1DB")),
        "ink": clean_text(theme.get("ink", "#171717")),
        "muted": clean_text(theme.get("muted", "#66635F")),
        "accent": clean_text(theme.get("accent", "#566675")),
        "dark": clean_text(theme.get("dark", "#232323")),
        "white": "#FFFFFF",
    }


def _regions(template: str, height: int) -> list[dict[str, Any]]:
    if template == "hero":
        return [{"id": "primary", "x": 0, "y": 0, "width": WIDTH, "height": 690, "fit": "cover"}]
    if template in {"fit-context", "editorial-context", "scene"}:
        return [{"id": "primary", "x": 0, "y": 150, "width": WIDTH, "height": height - 150, "fit": "cover"}]
    if template == "two-up-evidence":
        return [
            {"id": "front", "x": SAFE_X, "y": 150, "width": 315, "height": 610, "fit": "contain", "radius": 16},
            {"id": "back", "x": 387, "y": 150, "width": 315, "height": 610, "fit": "contain", "radius": 16},
        ]
    if template == "detail-grid":
        return [
            {"id": "macro", "x": SAFE_X, "y": 150, "width": 420, "height": 570, "fit": "cover", "radius": 18},
            {"id": "context", "x": 492, "y": 150, "width": 210, "height": 270, "fit": "cover", "radius": 18},
            {"id": "secondary", "x": 492, "y": 450, "width": 210, "height": 270, "fit": "cover", "radius": 18},
        ]
    if template == "feature-callout":
        return [
            {"id": "primary", "x": 310, "y": 120, "width": 392, "height": 650, "fit": "contain"},
            {"id": "detail", "x": SAFE_X, "y": 470, "width": 215, "height": 215, "fit": "cover", "radius": 108},
        ]
    if template == "fit-guide":
        return [{"id": "guide", "x": 420, "y": 140, "width": 282, "height": 500, "fit": "contain", "radius": 16}]
    if template == "brand-close":
        return [{"id": "primary", "x": 390, "y": 120, "width": 312, "height": 450, "fit": "contain"}]
    return [{"id": "primary", "x": SAFE_X, "y": 130, "width": WIDTH - SAFE_X * 2, "height": height - 200, "fit": "contain"}]


def _text_layers(slot: dict[str, Any], template: str, palette: dict[str, str]) -> list[dict[str, Any]]:
    title = clean_text(slot.get("headline", slot.get("role", "")))
    body = clean_text(slot.get("subcopy", ""))
    layers: list[dict[str, Any]] = []
    if template == "hero":
        layers.append({"id": "headline", "text": title, "x": SAFE_X, "y": 730, "width": 654, "font": "display", "size": 46, "color": palette["ink"], "line_height": 1.25})
        if body:
            layers.append({"id": "subcopy", "text": body, "x": SAFE_X, "y": 810, "width": 620, "font": "body", "size": 25, "color": palette["muted"], "line_height": 1.45})
    elif template == "feature-callout":
        layers.append({"id": "headline", "text": title, "x": SAFE_X, "y": 72, "width": 560, "font": "display", "size": 38, "color": palette["ink"], "line_height": 1.25})
        if body:
            layers.append({"id": "subcopy", "text": body, "x": SAFE_X, "y": 160, "width": 230, "font": "body", "size": 24, "color": palette["muted"], "line_height": 1.5})
    else:
        layers.append({"id": "headline", "text": title, "x": SAFE_X, "y": 58, "width": 640, "font": "display", "size": 36, "color": palette["ink"], "line_height": 1.25})
        if body:
            layers.append({"id": "subcopy", "text": body, "x": SAFE_X, "y": 110, "width": 620, "font": "body", "size": 23, "color": palette["muted"], "line_height": 1.45})
    return layers


def _annotations(slot: dict[str, Any], template: str, palette: dict[str, str]) -> list[dict[str, Any]]:
    if template != "feature-callout":
        return []
    labels = slot.get("annotation_labels") if isinstance(slot.get("annotation_labels"), list) else []
    if not labels:
        labels = ["结构细节", "位置与做工"]
    points = [((500, 370), (255, 300)), ((520, 540), (255, 590))]
    return [
        {
            "id": f"callout-{index + 1}",
            "label": clean_text(label),
            "target": {"x": target[0], "y": target[1]},
            "label_anchor": {"x": anchor[0], "y": anchor[1]},
            "color": palette["accent"],
        }
        for index, (label, (target, anchor)) in enumerate(zip(labels[:2], points))
    ]


def _verified_size_table(plan: dict[str, Any], base_dir: Path | None) -> dict[str, Any] | None:
    size = plan.get("size_module") if isinstance(plan.get("size_module"), dict) else {}
    if size.get("mode") != "numeric" or not size.get("source") or base_dir is None:
        return None
    path = Path(str(size["source"])).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    if path.suffix.lower() != ".json" or not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    rows = raw.get("rows", raw) if isinstance(raw, dict) else raw
    if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
        return None
    columns = list(rows[0].keys())[:6]
    return {
        "x": SAFE_X,
        "y": 190,
        "width": 340,
        "row_height": 48,
        "columns": columns,
        "rows": [[clean_text(row.get(column, "")) for column in columns] for row in rows[:8]],
        "source": str(path),
    }


def _module(slot: dict[str, Any], palette: dict[str, str], *, size_table: dict[str, Any] | None = None) -> dict[str, Any]:
    base = _base_id(slot)
    template, design_height = MODULE_SPECS.get(base, ("evidence", 760))
    height = _height_for_aspect(slot, design_height)
    vertical_scale = height / design_height
    display_slot = copy.deepcopy(slot)
    raw_headline = clean_text(display_slot.get("headline", ""))
    if not _has_cjk(raw_headline):
        display_slot["headline"] = MODULE_TITLES.get(base, "商品信息")
    if not clean_text(display_slot.get("subcopy", "")):
        display_slot["subcopy"] = clean_text(display_slot.get("question", ""))
    backgrounds = {
        "hero": palette["paper"],
        "fit-context": palette["surface"],
        "editorial-context": palette["surface"],
        "two-up-evidence": palette["paper"],
        "detail-grid": palette["white"],
        "feature-callout": palette["paper"],
        "scene": palette["surface"],
        "fit-guide": palette["white"],
        "brand-close": palette["dark"],
    }
    result = {
        "id": clean_text(slot.get("id", base)),
        "source_slot_id": clean_text(slot.get("id", base)),
        "source_base_slot_id": base,
        "template": template,
        "buyer_question": clean_text(slot.get("question", "")),
        "height": height,
        "background": backgrounds.get(template, palette["paper"]),
        "asset_policy": "final_module_image_with_embedded_chinese",
        "text_rendering": "ai_embedded_one_pass",
        "rendered_by": "gpt-image-2-one-pass",
        "regions": _scale_vertical(_regions(template, design_height), vertical_scale),
        # These are AI composition specifications, not local overlay layers.
        "text_layers": _scale_vertical(_text_layers(display_slot, template, palette), vertical_scale),
        "annotations": _scale_vertical(_annotations(slot, template, palette), vertical_scale),
        "facts_used": copy.deepcopy(slot.get("facts_used", [])),
        "risk_notes": copy.deepcopy(slot.get("risk_notes", [])),
        "status": "needs_assets",
    }
    if template == "brand-close":
        for layer in result["text_layers"]:
            layer["color"] = palette["white"]
    if template == "fit-guide" and size_table:
        result["table"] = copy.deepcopy(size_table)
        result["table"]["y"] = round(float(result["table"]["y"]) * vertical_scale)
        result["table"]["row_height"] = round(float(result["table"]["row_height"]) * vertical_scale)
    return result


def build_blueprint(plan: dict[str, Any], *, work_unit: str = "", base_dir: Path | None = None) -> dict[str, Any]:
    validation = plan.get("validation") if isinstance(plan.get("validation"), dict) else {}
    if plan.get("status") == "blocked" or validation.get("ok") is False:
        raise ValidationError("plan is blocked; resolve it before building a page blueprint")
    relationship = plan.get("product_relationship") if isinstance(plan.get("product_relationship"), dict) else {}
    sale_mode = clean_text(relationship.get("mode", "single_item"))
    if sale_mode == "separate_pairing" and work_unit not in {"top", "bottom"}:
        raise ValidationError("separate_pairing requires --work-unit top or --work-unit bottom")
    slots = ((plan.get("deliverables") or {}).get("slots") or [])
    if work_unit:
        slots = [item for item in slots if clean_text(item.get("work_unit_id", "")) == work_unit]
    active = [
        copy.deepcopy(item) for item in slots
        if clean_text(item.get("status", "planned")).lower().replace("-", "_") not in {"blocked", "needs_reference", "deferred", "rejected", "omitted"}
    ]
    if not 6 <= len(active) <= 10:
        raise ValidationError(f"a complete page blueprint requires 6-10 active modules; found {len(active)}")
    active.sort(key=lambda item: (DEFAULT_ORDER.get(_base_id(item), 90), clean_text(item.get("id", ""))))
    palette = _hex_palette(plan)
    size_table = _verified_size_table(plan, base_dir)
    modules = [_module(slot, palette, size_table=size_table) for slot in active]
    sku = plan.get("sku") if isinstance(plan.get("sku"), dict) else {}
    return {
        "schema_version": "1.0",
        "workflow": "clothing-pdp-page-blueprint",
        "classification": "editable_page_blueprint",
        "sku": copy.deepcopy(sku),
        "sale_mode": sale_mode,
        "work_unit_id": work_unit or clean_text(sku.get("id", "item")),
        "page": {
            "logical_width": WIDTH,
            "module_gap": GAP,
            "safe_margin_x": SAFE_X,
            "background": palette["paper"],
            "palette": palette,
            "text_rendering": "ai_embedded_per_module",
            "image_generation_scope": "final_module_images",
            "assembly_scope": "vertical_layout_only",
        },
        "typography": {
            "font_family": "PingFang SC or Noto Sans CJK SC",
            "display_size": 36,
            "body_size": 23,
            "minimum_body_size": 22,
        },
        "modules": modules,
        "completion_requirements": {
            "all_modules_have_assets": True,
            "minimum_modules": 6,
            "requires_ai_embedded_text_review": True,
            "local_compositor_adds_text": False,
            "requires_mobile_preview": True,
            "requires_full_page_render": True,
            "independent_posters_are_not_a_complete_page": True,
        },
        "status": "needs_assets",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", help="approved plan JSON")
    parser.add_argument("--work-unit", choices=("top", "bottom"), default="")
    parser.add_argument("--out", "-o")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        source = Path(args.plan).expanduser().resolve()
        raw = load_json(source)
        if not isinstance(raw, dict):
            raise ValidationError("plan JSON must be an object")
        dump_json(build_blueprint(raw, work_unit=args.work_unit, base_dir=source.parent), args.out)
        return 0
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
