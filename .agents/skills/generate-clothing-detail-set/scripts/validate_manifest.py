#!/usr/bin/env python3
"""Validate a completed clothing-detail manifest without external services."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from common import (
    ALLOWED_FACT_STATUSES,
    APPROVED_FACT_STATUSES,
    APPROVED_GATE_STATUSES,
    ValidationError,
    as_bool,
    as_list,
    clean_text,
    dump_json,
    first,
    load_json,
    path_exists,
    resolve_path,
)


GATE_ALIASES = {
    "facts-blueprint",
    "fact-blueprint",
    "facts_and_blueprint",
    "facts-blueprint-approval",
    "sample-package",
    "sample_package",
    "sample-approval",
    "sample-package-approval",
}
VOLATILE_TERMS = (
    "price", "discount", "stock", "availability", "review", "rating", "performance",
    "价格", "折扣", "库存", "缺货", "有货", "现货", "售罄", "评价", "评分", "销量",
    "功效", "性能", "限时", "仅剩", "马上抢", "抢购", "促销",
)
FIT_FORBIDDEN_PATTERN = re.compile(r"(?:\b(?:XS|S|M|L|XL|XXL)\b|cm\b|厘米|kg\b|公斤|斤|身高|体重|\d)", re.IGNORECASE)


def _path_value(item: Any) -> str:
    if isinstance(item, dict):
        return clean_text(first(item, "path", "file", "output", "src", "filename", default=""))
    return clean_text(item)


def _check_local_path(raw: str, base_dir: Path, label: str, errors: list[str], warnings: list[str]) -> None:
    if not raw:
        errors.append(f"{label} has no path")
        return
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw):
        errors.append(f"{label} is a URL; manifest validation is local-only: {raw}")
        return
    if not path_exists(raw, base_dir=base_dir):
        errors.append(f"{label} file does not exist: {raw}")


def _contains_volatile(value: Any) -> bool:
    text = clean_text(value).lower()
    return any(clean_text(term).lower() in text for term in VOLATILE_TERMS)


def _json_has_numeric_size_row(value: Any) -> bool:
    if isinstance(value, list):
        return any(_json_has_numeric_size_row(item) for item in value)
    if not isinstance(value, dict):
        return False
    normalized_keys = {clean_text(key).lower().replace("_", " ") for key in value}
    has_size = bool(normalized_keys & {"size", "尺码", "size label", "尺码标签"})
    has_measurement = any("measure" in key or key in {"chest", "bust", "waist", "hip", "length", "胸围", "腰围", "臀围", "衣长", "裤长"} for key in normalized_keys)
    if has_size and has_measurement and any(re.search(r"\d", clean_text(item)) for item in value.values()):
        return True
    return any(_json_has_numeric_size_row(item) for item in value.values())


def _check_image_path(raw: str, base_dir: Path, label: str, errors: list[str], warnings: list[str]) -> None:
    """Require a non-empty, decodable image without making Pillow mandatory."""

    path = resolve_path(raw, base_dir=base_dir)
    if path is None or not path.is_file():
        _check_local_path(raw, base_dir, label, errors, warnings)
        return
    if path.stat().st_size == 0:
        errors.append(f"{label} image is empty: {raw}")
        return
    try:
        from PIL import Image
    except ImportError:
        data = path.read_bytes()[:16]
        signatures = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"GIF87a", b"GIF89a", b"RIFF")
        if not any(data.startswith(signature) for signature in signatures):
            errors.append(f"{label} is not a recognized image (Pillow unavailable): {raw}")
        return
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.width <= 0 or image.height <= 0:
                errors.append(f"{label} image has invalid dimensions: {raw}")
    except Exception as exc:  # Pillow raises format-specific subclasses.
        errors.append(f"{label} is not a valid readable image: {raw} ({exc})")


def _validate_page_delivery(manifest: dict[str, Any], base_dir: Path, errors: list[str], warnings: list[str]) -> str:
    classification = clean_text(manifest.get("delivery_classification", "asset_pack_only")) or "asset_pack_only"
    if classification != "complete_mobile_detail_page":
        warnings.append("delivery is an asset pack only; it must not be reported as a complete ecommerce detail page")
        return "asset_pack_only"
    blueprint_path = _path_value(manifest.get("page_blueprint"))
    composed_path = _path_value(manifest.get("composed_page"))
    render_manifest_path = _path_value(manifest.get("page_render_manifest"))
    for value, label in (
        (blueprint_path, "page_blueprint"),
        (composed_path, "composed_page"),
        (render_manifest_path, "page_render_manifest"),
    ):
        if not value:
            errors.append(f"complete_mobile_detail_page requires {label}")
    if composed_path:
        _check_image_path(composed_path, base_dir, "composed mobile detail page", errors, warnings)
        path = resolve_path(composed_path, base_dir=base_dir)
        if path and path.is_file():
            try:
                from PIL import Image
                with Image.open(path) as image:
                    if image.width != 750:
                        errors.append(f"composed mobile detail page must be 750px logical width (got {image.width})")
                    if image.height < 3000:
                        errors.append(f"composed mobile detail page is too short to contain a complete module story (got {image.height}px)")
            except ImportError:
                warnings.append("Pillow unavailable; composed page dimensions were not checked")
    if blueprint_path:
        path = resolve_path(blueprint_path, base_dir=base_dir)
        if path and path.is_file():
            try:
                blueprint = load_json(path)
                modules = blueprint.get("modules", []) if isinstance(blueprint, dict) else []
                page = blueprint.get("page", {}) if isinstance(blueprint, dict) else {}
                if not 6 <= len(modules) <= 10:
                    errors.append("page_blueprint must contain 6-10 modules")
                if page.get("text_rendering") != "ai_embedded_per_module":
                    errors.append("page_blueprint must use ai_embedded_per_module")
                if page.get("image_generation_scope") != "final_module_images":
                    errors.append("page_blueprint must classify generated images as final_module_images")
                if page.get("assembly_scope") != "vertical_layout_only":
                    errors.append("page_blueprint must limit local composition to vertical_layout_only")
            except ValidationError as exc:
                errors.append(f"page_blueprint is invalid: {exc}")
    if render_manifest_path:
        path = resolve_path(render_manifest_path, base_dir=base_dir)
        if path and path.is_file():
            try:
                render_manifest = load_json(path)
                if not isinstance(render_manifest, dict) or render_manifest.get("assembly_only") is not True:
                    errors.append("page_render_manifest must confirm assembly_only=true")
                if isinstance(render_manifest, dict) and render_manifest.get("local_text_overlays") is not False:
                    errors.append("page_render_manifest must confirm local_text_overlays=false")
            except ValidationError as exc:
                errors.append(f"page_render_manifest is invalid: {exc}")
    return classification


def _fact_items(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    raw = manifest.get("facts")
    if isinstance(raw, dict):
        raw = raw.get("items", raw.get("facts", []))
    items: list[dict[str, Any]] = []
    for item in as_list(raw):
        if isinstance(item, dict):
            items.append(item)
    return items


def _validate_facts(manifest: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    items = _fact_items(manifest)
    if not items:
        warnings.append("manifest has no fact items; all unspecified product details remain unknown")
        return
    for index, item in enumerate(items, 1):
        key = clean_text(first(item, "key", "name", "field", default=f"fact-{index}"))
        status = clean_text(first(item, "status", "fact_status", default="")).lower()
        if status not in ALLOWED_FACT_STATUSES:
            errors.append(f"fact {key} has unsupported status: {status or '[missing]'}")
        elif status not in APPROVED_FACT_STATUSES:
            warnings.append(f"fact {key} is not an approved fact ({status})")
        if status in APPROVED_FACT_STATUSES:
            value = first(item, "value", "fact", "text", default=None)
            evidence = first(item, "evidence", "source", "source_path", default=None)
            if not value:
                errors.append(f"approved fact {key} has no value")
            if not evidence:
                errors.append(f"approved fact {key} has no evidence")
            temporary = bool(first(item, "temporary_asset", "temporary_asset_id", default=False))
            temporary_surface = clean_text(first(item, "allowed_surface", "surface", default="")).lower() in {"temporary", "temporary_asset", "temporary asset", "campaign"}
            if (_contains_volatile(key) or _contains_volatile(value)) and not (temporary and temporary_surface):
                errors.append(f"volatile fact {key} is not allowed in permanent product facts")


def _validate_size(manifest: dict[str, Any], base_dir: Path, errors: list[str], warnings: list[str]) -> None:
    size = manifest.get("size_module")
    if not isinstance(size, dict):
        deliverables = manifest.get("deliverables") if isinstance(manifest.get("deliverables"), dict) else {}
        if first(deliverables, "include_size", "include_size_module", default=first(manifest, "include_size", default=True)) is False:
            warnings.append("size_module omitted because include_size=false")
        else:
            errors.append("size_module is required")
        return
    mode = clean_text(first(size, "mode", "type", default="")).lower()
    source = clean_text(first(size, "source", "source_path", "path", default=""))
    status = clean_text(first(size, "source_status", "status", default="")).lower()
    numeric = mode in {"numeric", "size_chart", "verified-size-chart", "numeric-size"}
    fit = mode in {"fit-guidance", "fit", "styling-guidance"}
    if mode in {"omitted", "none", "disabled"}:
        deliverables = manifest.get("deliverables") if isinstance(manifest.get("deliverables"), dict) else {}
        if first(deliverables, "include_size", "include_size_module", default=first(manifest, "include_size", default=True)) is not False:
            errors.append("size_module.mode=omitted requires include_size=false")
        return
    if numeric:
        if not source:
            errors.append("numeric size module requires a real size source")
        elif re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", source):
            errors.append("numeric size source is a URL; local validation cannot treat it as verified")
        else:
            path = resolve_path(source, base_dir=base_dir)
            if path is None or not path.is_file() or path.stat().st_size == 0:
                errors.append(f"numeric size source is missing or empty: {source}")
            elif status not in APPROVED_FACT_STATUSES:
                errors.append("numeric size module source must be confirmed/approved")
            elif path.suffix.lower() == ".json":
                try:
                    parsed = json.loads(path.read_text(encoding="utf-8"))
                    serialized = json.dumps(parsed, ensure_ascii=False).lower()
                    if not any(token in serialized for token in ("size", "尺码", "measurement", "measure", "胸围", "腰围", "衣长")):
                        errors.append("JSON size source has no measurement fields")
                    if not any(token in serialized for token in ("unit", "cm", "厘米", "inch", "英寸")):
                        errors.append("JSON size source has no measurement unit")
                    if not _json_has_numeric_size_row(parsed):
                        errors.append("JSON size source has no numeric size row")
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    errors.append("JSON size source is not valid readable JSON")
            elif path.suffix.lower() in {".csv", ".tsv", ".txt"}:
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    text = ""
                lowered = text.lower()
                if not text.strip() or not any(token in lowered for token in ("size", "尺码", "measurement", "measure", "胸围", "腰围", "衣长")):
                    errors.append("text size source has no measurement fields")
                if not any(token in lowered for token in ("unit", "cm", "厘米", "inch", "英寸")):
                    errors.append("text size source has no measurement unit")
                lines = [line for line in text.splitlines() if line.strip()]
                if len(lines) < 2 or not any(char.isdigit() for char in " ".join(lines[1:])):
                    errors.append("text size source has no numeric data row")
            elif path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".pdf"}:
                if not first(size, "verified_by", "reviewer", default="") or not first(size, "approved_at", "approval_time", default=""):
                    errors.append("image/PDF size source requires verified_by/reviewer and approved_at")
    elif fit:
        required = {"fit", "ease", "measuring_positions", "styling_guidance"}
        fields = set(size)
        # A nested guidance object is also accepted when it supplies all four
        # named concepts; the values still must not be numeric size guesses.
        guidance = size.get("guidance") if isinstance(size.get("guidance"), dict) else {}
        missing = [field for field in required if not size.get(field) and not guidance.get(field)]
        if missing:
            errors.append("fit-guidance size replacement is missing: " + ", ".join(sorted(missing)))
        guidance_values = [size.get(field, guidance.get(field, "")) for field in required]
        for value in guidance_values:
            if FIT_FORBIDDEN_PATTERN.search(clean_text(value)):
                errors.append("fit-guidance cannot contain numeric size/unit or height/weight language")
                break
        if source:
            warnings.append("fit-guidance module retains a source note; no numeric values will be inferred")
    else:
        errors.append("size_module.mode must be numeric or fit-guidance")


def _validate_models(manifest: dict[str, Any], base_dir: Path, errors: list[str], warnings: list[str]) -> None:
    """Validate each model identity pack independently, including model two."""

    deliverables = manifest.get("deliverables") if isinstance(manifest.get("deliverables"), dict) else {}
    requested = first(deliverables, "model_count", "models", default=first(manifest, "model_count", default=None))
    try:
        requested_count = int(requested) if requested is not None else None
    except (TypeError, ValueError):
        errors.append("model_count must be an integer")
        requested_count = None

    raw_packs = manifest.get("models", manifest.get("model_packs"))
    packs = [item for item in as_list(raw_packs) if isinstance(item, dict)]
    seen_ids: set[str] = set()
    for pack in packs:
        pack_id = clean_text(first(pack, "id", "name", "model_id", default=""))
        if pack_id and pack_id in seen_ids:
            errors.append(f"duplicate model pack id: {pack_id}")
        seen_ids.add(pack_id)
    if requested_count is None:
        requested_count = len(packs)
    if requested_count < 0:
        errors.append("model_count cannot be negative")
        return
    if requested_count > len(packs):
        # A legacy one-model manifest may still use top-level fields; permit it
        # only for a requested count of one.  Two must be explicit and separate.
        if requested_count == 1 and not packs:
            packs = [{
                "id": first(manifest.get("model"), "id", "name", "model_id", default="") if isinstance(manifest.get("model"), dict) else "",
                "approved": first(manifest.get("model"), "approved", "selected", default=False) if isinstance(manifest.get("model"), dict) else False,
                "reference_images": manifest.get("model_reference_images", []),
            }]
        else:
            errors.append(
                f"model_count={requested_count} requires {requested_count} independent model packs; only {len(packs)} supplied"
            )
    for index, pack in enumerate(packs[:requested_count], 1):
        label = f"model pack {index}"
        if not clean_text(first(pack, "id", "name", "model_id", default="")):
            errors.append(f"{label} id is required")
        approved = as_bool(first(pack, "approved", "selected", default=False))
        status = clean_text(first(pack, "status", "approval_status", default="")).lower()
        if not approved and status not in APPROVED_GATE_STATUSES:
            errors.append(f"{label} is not approved")
        refs = first(pack, "reference_images", "references", "images", "identity_pack", default=[])
        for ref_index, entry in enumerate(as_list(refs), 1):
            _check_image_path(_path_value(entry), base_dir, f"{label} reference {ref_index}", errors, warnings)
        if not refs:
            errors.append(f"{label} reference images are required")
    master_entries = []
    for source_key in ("slots", "extra_outputs", "outputs"):
        values = manifest.get(source_key, [])
        master_entries.extend(item for item in as_list(values) if isinstance(item, dict))
    for pack in packs[:requested_count]:
        pack_id = clean_text(first(pack, "id", "name", "model_id", default=""))
        if pack_id and not any(
            clean_text(first(item, "model_group_id", default="")) == pack_id
            and "master" in clean_text(first(item, "type", "role", default="")).lower()
            for item in master_entries
        ):
            errors.append(f"model group {pack_id} has no independent model master output/slot")


def _manifest_copy_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    raw = manifest.get("copy_ledger", manifest.get("copy"))
    if isinstance(raw, dict):
        raw = raw.get("rows", raw.get("items", [raw]))
    return [dict(item) for item in as_list(raw) if isinstance(item, dict)]


def _validate_copy_and_moments(manifest: dict[str, Any], base_dir: Path, errors: list[str], warnings: list[str]) -> None:
    rows = _manifest_copy_rows(manifest)
    if not rows:
        errors.append("manifest must contain a copy ledger for the complete detail package")
    for index, row in enumerate(rows, 1):
        row_id = clean_text(first(row, "id", "copy_id", default=f"copy-{index}"))
        status = clean_text(first(row, "status", "state", default="")).lower()
        evidence = first(row, "evidence", "source", "source_path", default="")
        surface = clean_text(first(row, "allowed_surface", "surface", default="")).lower().replace("-", "_")
        text = first(row, "text", "copy", "value", default="")
        if not status:
            errors.append(f"copy row {row_id} requires status")
        if not evidence:
            errors.append(f"copy row {row_id} requires evidence")
        if not surface:
            errors.append(f"copy row {row_id} requires allowed_surface")
        temporary = surface in {"temporary", "temporary_asset", "campaign"}
        if _contains_volatile(text) and not temporary:
            errors.append(f"volatile copy row {row_id} is not allowed on a permanent surface")

    moments = manifest.get("moments", manifest.get("moments_entries"))
    if moments is None:
        errors.append("moments must contain the default six entries")
        return
    moment_items = [item for item in as_list(moments) if isinstance(item, dict)]
    if len(moment_items) != 6:
        errors.append(f"moments must contain exactly six entries (got {len(moment_items)})")
    for index, item in enumerate(moment_items, 1):
        text_parts: list[str] = []
        for key in ("text", "content", "owner_text", "caption", "short_caption"):
            if item.get(key):
                text_parts.append(clean_text(item[key]))
        if _contains_volatile(" ".join(text_parts)):
            errors.append(f"Moments entry {index} contains price/discount/stock/urgency language")

    temporary_assets = manifest.get("temporary_assets", manifest.get("temporary_asset", []))
    for index, asset in enumerate(as_list(temporary_assets), 1):
        if not isinstance(asset, dict):
            errors.append(f"temporary asset {index} must be an object")
            continue
        surface = clean_text(first(asset, "allowed_surface", "surface", default="")).lower().replace("-", "_")
        if surface not in {"temporary", "temporary_asset", "campaign"}:
            errors.append(f"temporary asset {index} must declare a temporary surface")
        path = _path_value(asset)
        if path:
            # The asset is still local-only; a temporary label does not permit
            # an untracked URL or missing file.
            _check_local_path(path, base_dir, f"temporary asset {index}", errors, warnings)


def _gate_statuses(manifest: dict[str, Any]) -> dict[str, str]:
    raw = manifest.get("approval_gates", manifest.get("gates", []))
    statuses: dict[str, str] = {}
    aliases = {
        "facts": {"facts-blueprint", "fact-blueprint", "facts_and_blueprint", "facts-blueprint-approval"},
        "sample": {"sample-package", "sample_package", "sample-approval", "sample-package-approval"},
    }
    for gate in as_list(raw):
        if not isinstance(gate, dict):
            continue
        gate_id = clean_text(first(gate, "id", "name", "gate", default="")).lower().replace(" ", "-")
        status = clean_text(first(gate, "status", "state", default="")).lower()
        for label, candidates in aliases.items():
            if gate_id in candidates:
                statuses[label] = status
    return statuses


def _validate_sample_package(manifest: dict[str, Any], base_dir: Path, errors: list[str], warnings: list[str]) -> None:
    gate1 = first(manifest, "gate1_paid_calls", default=None)
    paid = manifest.get("paid_calls") if isinstance(manifest.get("paid_calls"), dict) else {}
    if gate1 is None:
        gate1 = first(paid, "gate1_paid_calls", "sample_calls", default=None)
    try:
        gate1_count = int(gate1) if gate1 is not None else None
    except (TypeError, ValueError):
        gate1_count = None
    if gate1_count != 3:
        errors.append("gate1_paid_calls must equal exactly 3")

    raw_outputs = manifest.get("sample_outputs", [])
    outputs = [item for item in as_list(raw_outputs) if isinstance(item, dict)]
    if len(outputs) != 3:
        errors.append(f"sample_outputs must contain exactly 3 outputs (got {len(outputs)})")
    masters = 0
    details = 0
    designed = 0
    editorial = 0
    manifest_slots = [item for item in as_list(manifest.get("slots", [])) if isinstance(item, dict)]
    family_by_path = {
        str(resolve_path(_path_value(item), base_dir=base_dir) or _path_value(item)): clean_text(item.get("visual_family", ""))
        for item in manifest_slots if _path_value(item)
    }
    sample_seen: set[str] = set()
    for index, item in enumerate(outputs, 1):
        kind = clean_text(first(item, "kind", "output_type", "role", "type", default="")).lower()
        if "master" in kind:
            masters += 1
        if "detail" in kind and ("final" in kind or "slice" in kind):
            details += 1
        path = _path_value(item)
        normalized_path = str(resolve_path(path, base_dir=base_dir) or path) if path else ""
        family = clean_text(item.get("visual_family", "")) or family_by_path.get(normalized_path, "")
        if family in {"designed_selling_point", "information_graphic"}:
            designed += 1
        if family in {"worn_editorial", "lifestyle_scene", "editorial_scene", "brand_close"}:
            editorial += 1
        if path:
            _check_image_path(path, base_dir, f"sample output {index}", errors, warnings)
            if normalized_path in sample_seen:
                errors.append(f"sample output path is listed more than once: {path}")
            sample_seen.add(normalized_path)
        else:
            errors.append(f"sample output {index} has no path")
    if masters != 1 or details != 2:
        errors.append("sample_outputs must be one master plus two final detail slices")
    if designed != 1 or editorial != 1:
        errors.append("sample_outputs must represent one designed information/selling-point screen and one editorial/lifestyle/brand-close screen")

    preview = manifest.get("two_slice_preview", manifest.get("two_slice_preview_path"))
    preview_path = _path_value(preview) if isinstance(preview, dict) else clean_text(preview)
    preview_inputs = []
    if isinstance(preview, dict):
        preview_inputs = as_list(first(preview, "inputs", "input_paths", "source_outputs", default=[]))
    if not preview_path:
        errors.append("two_slice_preview path is required")
    else:
        _check_image_path(preview_path, base_dir, "two_slice_preview", errors, warnings)
        existing_outputs = []
        for source_key in ("slots", "files", "outputs"):
            values = manifest.get(source_key, [])
            existing_outputs.extend(_path_value(item) for item in as_list(values) if _path_value(item))
        deliverables = manifest.get("deliverables") if isinstance(manifest.get("deliverables"), dict) else {}
        existing_outputs.extend(_path_value(item) for item in as_list(deliverables.get("slots", [])) if _path_value(item))
        normalized_preview = str(resolve_path(preview_path, base_dir=base_dir) or preview_path)
        if normalized_preview in {str(resolve_path(path, base_dir=base_dir) or path) for path in existing_outputs}:
            errors.append("two_slice_preview must not reuse a master/slot output path")
    if len(preview_inputs) != 2:
        errors.append("two_slice_preview must record exactly two input paths")
    for index, path in enumerate(preview_inputs, 1):
        _check_image_path(_path_value(path), base_dir, f"two_slice_preview input {index}", errors, warnings)

    actual = first(paid, "actual", "actual_calls", "count", default=first(manifest, "actual_paid_calls", "actual_calls", default=None))
    try:
        actual_count = int(actual) if actual is not None else None
    except (TypeError, ValueError):
        actual_count = None
    gate2_status = _gate_statuses(manifest).get("sample", "")
    if actual_count is not None and actual_count > 3 and gate2_status not in APPROVED_GATE_STATUSES:
        errors.append("remaining paid calls are forbidden before Gate2 sample-package approval")


def _validate_gates(manifest: dict[str, Any], errors: list[str], warnings: list[str], allow_pending: bool) -> None:
    raw = manifest.get("approval_gates", manifest.get("gates", []))
    gates = [item for item in as_list(raw) if isinstance(item, dict)]
    found: dict[str, dict[str, Any]] = {}
    canonical_seen: set[str] = set()
    canonical_aliases = {
        "facts": {"facts-blueprint", "fact-blueprint", "facts_and_blueprint", "facts-blueprint-approval"},
        "sample": {"sample-package", "sample_package", "sample-approval", "sample-package-approval"},
    }
    for gate in gates:
        gate_id = clean_text(first(gate, "id", "name", "gate", default="")).lower().replace(" ", "-")
        if gate_id:
            if gate_id in found:
                errors.append(f"duplicate approval gate id: {gate_id}")
                continue
            for canonical, aliases in canonical_aliases.items():
                if gate_id in aliases:
                    if canonical in canonical_seen:
                        errors.append(f"duplicate approval gate alias: {canonical}")
                    canonical_seen.add(canonical)
            found[gate_id] = gate
    aliases = {
        "facts": {"facts-blueprint", "fact-blueprint", "facts_and_blueprint", "facts-blueprint-approval"},
        "sample": {"sample-package", "sample_package", "sample-approval", "sample-package-approval"},
    }
    for label, candidates in aliases.items():
        match = next((found[key] for key in candidates if key in found), None)
        if match is None:
            errors.append(f"missing approval gate: {label}")
            continue
        status = clean_text(first(match, "status", "state", default="")).lower()
        if status not in APPROVED_GATE_STATUSES:
            if allow_pending:
                warnings.append(f"approval gate {label} is not approved ({status or '[missing]'})")
            else:
                errors.append(f"approval gate {label} is not approved ({status or '[missing]'})")
    facts_gate = next((found[key] for key in aliases["facts"] if key in found), None)
    sample_gate = next((found[key] for key in aliases["sample"] if key in found), None)
    def parse_time(value: Any) -> datetime | None:
        text = clean_text(value)
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    facts_time = parse_time(first(facts_gate, "approved_at", "approval_time", default="")) if facts_gate else None
    sample_time = parse_time(first(sample_gate, "approved_at", "approval_time", default="")) if sample_gate else None
    try:
        if facts_time and sample_time and sample_time < facts_time:
            errors.append("sample-package approval cannot precede facts-blueprint approval")
    except TypeError:
        warnings.append("approval gate timestamps use mixed timezone forms; order was not compared")
    remaining_time = parse_time(first(manifest, "remaining_calls_started_at", "remaining_generation_started_at", default=""))
    try:
        if remaining_time and sample_time and remaining_time < sample_time:
            errors.append("remaining paid calls cannot start before sample-package approval")
    except TypeError:
        warnings.append("remaining-call timestamp uses a mixed timezone form; order was not compared")


def _validate_calls(manifest: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    paid = manifest.get("paid_calls") if isinstance(manifest.get("paid_calls"), dict) else {}
    estimate = manifest.get("paid_calls_estimate")
    if estimate is None:
        estimate = paid.get("estimated", paid.get("estimate"))
    if isinstance(estimate, dict):
        planned = first(estimate, "planned_total", "total", "estimated", "count", default=None)
    else:
        planned = estimate
    actual = first(paid, "actual", "actual_calls", "count", default=first(manifest, "actual_paid_calls", "actual_calls", "call_count", default=None))
    try:
        planned_int = int(planned) if planned is not None else None
    except (TypeError, ValueError):
        errors.append("paid call estimate must be an integer")
        planned_int = None
    try:
        actual_int = int(actual) if actual is not None else None
    except (TypeError, ValueError):
        errors.append("actual paid call count must be an integer")
        actual_int = None
    if planned_int is None:
        errors.append("paid call estimate is required")
    elif planned_int < 0:
        errors.append("paid call estimate cannot be negative")
    if actual_int is None:
        warnings.append("actual paid call count is not recorded yet")
    elif actual_int < 0:
        errors.append("actual paid call count cannot be negative")
    elif planned_int is not None and actual_int > planned_int:
        errors.append(f"actual paid calls ({actual_int}) exceed estimate ({planned_int})")


def validate_manifest(manifest: dict[str, Any], *, base_dir: Path, allow_pending: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    sku = manifest.get("sku")
    sku_id = clean_text(first(sku, "id", "sku", "code", default=sku if isinstance(sku, str) else ""))
    if not sku_id:
        errors.append("sku id is required")

    for label, key in (("product reference", "product_reference_images"),):
        values = manifest.get(key, [])
        for index, entry in enumerate(as_list(values), 1):
            _check_image_path(_path_value(entry), base_dir, f"{label} {index}", errors, warnings)
    if not isinstance(manifest.get("models"), list) and not isinstance(manifest.get("model_packs"), list):
        values = manifest.get("model_reference_images", [])
        for index, entry in enumerate(as_list(values), 1):
            _check_image_path(_path_value(entry), base_dir, f"model reference {index}", errors, warnings)

    slots = [item for item in as_list(manifest.get("slots", manifest.get("deliverables", {}).get("slots", []) if isinstance(manifest.get("deliverables"), dict) else [])) if isinstance(item, dict)]
    if slots and not 6 <= len(slots) <= 10:
        errors.append(f"manifest must contain 6-10 planned slots (got {len(slots)})")
    slot_ids: set[str] = set()
    output_paths: list[str] = []
    for index, slot in enumerate(slots, 1):
        slot_id = clean_text(first(slot, "id", "slot_id", default=f"slot-{index}"))
        if slot_id in slot_ids:
            errors.append(f"duplicate slot id: {slot_id}")
        slot_ids.add(slot_id)
        raw_path = _path_value(slot)
        if raw_path:
            output_paths.append(raw_path)
            if clean_text(first(slot, "status", default="")).lower() not in {"deferred", "blocked", "needs_reference", "needs-reference", "omitted", "rejected"}:
                _check_image_path(raw_path, base_dir, f"slot {slot_id}", errors, warnings)
            else:
                _check_local_path(raw_path, base_dir, f"slot {slot_id}", errors, warnings)
        elif clean_text(first(slot, "status", default="")).lower().replace("-", "_") not in {"rejected", "omitted", "deferred", "blocked", "needs_reference"}:
            errors.append(f"slot {slot_id} has no output path")
    files = as_list(manifest.get("files", manifest.get("outputs", [])))
    for index, item in enumerate(files, 1):
        raw_path = _path_value(item)
        if raw_path:
            output_paths.append(raw_path)
            _check_image_path(raw_path, base_dir, f"file {index}", errors, warnings)
    if not slots and not files:
        errors.append("manifest must list slots or output files")
    seen_paths: set[str] = set()
    for raw_path in output_paths:
        normalized = str(resolve_path(raw_path, base_dir=base_dir) or raw_path)
        if normalized in seen_paths:
            errors.append(f"same output path is listed more than once: {raw_path}")
        seen_paths.add(normalized)

    _validate_facts(manifest, errors, warnings)
    _validate_models(manifest, base_dir, errors, warnings)
    _validate_size(manifest, base_dir, errors, warnings)
    _validate_gates(manifest, errors, warnings, allow_pending)
    _validate_calls(manifest, errors, warnings)
    _validate_copy_and_moments(manifest, base_dir, errors, warnings)
    _validate_sample_package(manifest, base_dir, errors, warnings)
    delivery_classification = _validate_page_delivery(manifest, base_dir, errors, warnings)
    return {"ok": not errors, "delivery_classification": delivery_classification, "errors": errors, "warnings": warnings}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", help="manifest JSON path")
    parser.add_argument("--manifest", dest="manifest_flag")
    parser.add_argument("--out", "-o")
    parser.add_argument("--allow-pending", action="store_true", help="report unapproved gates as warnings")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    path = args.manifest_flag or args.manifest
    if not path:
        print("validate_manifest.py requires a manifest JSON path", file=sys.stderr)
        return 2
    try:
        source = Path(path).expanduser().resolve()
        raw = load_json(source)
        if not isinstance(raw, dict):
            raise ValidationError("manifest JSON must be an object")
        report = validate_manifest(raw, base_dir=source.parent, allow_pending=args.allow_pending)
        result = {"manifest": str(source), **report}
        dump_json(result, args.out)
        return 0 if report["ok"] else 2
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
