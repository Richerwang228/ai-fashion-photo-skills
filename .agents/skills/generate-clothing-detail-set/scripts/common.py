"""Shared, local-only helpers for the clothing detail-set scripts.

The helpers in this module deliberately avoid network access, third-party
providers, and environment based credentials.  The public scripts use these
functions to keep their JSON contracts small and predictable.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


ALLOWED_FACT_STATUSES = {
    "confirmed",
    "approved",
    "verified",
    "documented",
    "creative",
    "recommendation",
    "provisional",
    "pending",
    "unknown",
    "unconfirmed",
}
APPROVED_FACT_STATUSES = {"confirmed", "approved", "verified", "documented"}
APPROVED_GATE_STATUSES = {"approved", "confirmed", "passed", "complete", "completed"}


class ValidationError(ValueError):
    """A user-fixable input error exposed by a CLI script."""


def load_json(path: str | Path) -> Any:
    """Load UTF-8 JSON from *path* with a useful error message."""

    source = Path(path).expanduser()
    try:
        with source.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise ValidationError(f"JSON file not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in {source}: {exc}") from exc


def dump_json(value: Any, path: str | Path | None = None) -> None:
    """Write JSON to *path* or stdout without contacting a service."""

    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path is None:
        sys.stdout.write(text)
        return
    destination = Path(path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def first(value: Any, *keys: str, default: Any = None) -> Any:
    """Return the first non-empty mapping value for the supplied keys."""

    if not isinstance(value, Mapping):
        return default
    for key in keys:
        candidate = value.get(key)
        if candidate is not None and candidate != "":
            return candidate
    return default


def as_list(value: Any) -> list[Any]:
    """Normalize a scalar/null/list into a list."""

    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def as_bool(value: Any, *, default: bool = False) -> bool:
    """Parse the common JSON/string spellings of a boolean flag.

    ``bool("false")`` is true in Python, which is an unsafe default for
    approval fields.  Treat explicit false-like strings as false and retain a
    caller-supplied default only for null/empty values.
    """

    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"false", "0", "no", "n", "off", "rejected", "pending"}:
            return False
        if normalized in {"true", "1", "yes", "y", "on", "approved", "selected"}:
            return True
        return default
    return bool(value)


def resolve_path(raw: Any, *, base_dir: Path | None = None) -> Path | None:
    """Resolve a local path without fetching URLs.

    URLs are intentionally returned as ``None``: these scripts never perform
    network access.  Callers may record them as unverified references.
    """

    text = clean_text(raw)
    if not text or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", text):
        return None
    path = Path(text).expanduser()
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path
    return path.resolve()


def path_exists(raw: Any, *, base_dir: Path | None = None) -> bool:
    path = resolve_path(raw, base_dir=base_dir)
    return path is not None and path.is_file()


def validate_local_image(raw: Any, *, base_dir: Path | None = None) -> tuple[bool, str]:
    """Validate a local image before it can become paid-generation evidence."""

    path = resolve_path(raw, base_dir=base_dir)
    if path is None:
        return False, "path is empty or is not a local file path"
    if not path.is_file():
        return False, "file does not exist"
    if path.stat().st_size == 0:
        return False, "file is empty"
    try:
        from PIL import Image
    except ImportError:
        data = path.read_bytes()[:16]
        signatures = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"GIF87a", b"GIF89a", b"RIFF")
        if not any(data.startswith(signature) for signature in signatures):
            return False, "file has no recognized image signature and Pillow is unavailable"
        return True, ""
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.width <= 0 or image.height <= 0:
                return False, "image has invalid dimensions"
    except Exception as exc:  # Pillow raises format-specific subclasses.
        return False, f"image cannot be decoded: {exc}"
    return True, ""


def normalize_fact_items(job: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Normalize facts while preserving whether they were seen, supplied, or unknown."""

    product = job.get("product") if isinstance(job.get("product"), Mapping) else {}
    raw = first(job, "facts", "product_facts", default=None)
    if raw is None:
        raw = first(product, "facts", "product_facts", default=[])
    items: list[dict[str, Any]] = []
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            if isinstance(value, Mapping):
                item = dict(value)
                item.setdefault("key", key)
            else:
                item = {"key": key, "value": value}
            items.append(item)
    else:
        for value in as_list(raw):
            if isinstance(value, Mapping):
                items.append(dict(value))
            elif isinstance(value, str) and ":" in value:
                key, item_value = value.split(":", 1)
                items.append({"key": key.strip(), "value": item_value.strip()})
    for item in items:
        item["key"] = clean_text(first(item, "key", "name", "field"))
        item["value"] = first(item, "value", "fact", "text", default="")
        item["status"] = clean_text(first(item, "status", "fact_status", default="unknown")).lower()
        item["source"] = first(item, "source", "source_path", "evidence", default=None)
        raw_origin = clean_text(first(item, "origin", "fact_origin", "source_type", default="")).lower()
        origin_aliases = {
            "visual": "visible",
            "image": "visible",
            "observed": "visible",
            "visible_fact": "visible",
            "owner": "user_provided",
            "user": "user_provided",
            "merchant": "user_provided",
            "provided": "user_provided",
            "user-provided": "user_provided",
            "unknown": "unconfirmed",
            "pending": "unconfirmed",
        }
        origin = origin_aliases.get(raw_origin, raw_origin)
        if origin not in {"visible", "user_provided", "unconfirmed"}:
            source_text = clean_text(item["source"]).lower()
            if item["status"] in {"unknown", "unconfirmed", "pending", "provisional"}:
                origin = "unconfirmed"
            elif source_text.endswith((".png", ".jpg", ".jpeg", ".webp", ".heic", ".avif")):
                origin = "visible"
            else:
                origin = "user_provided"
        item["origin"] = origin
    return [item for item in items if item["key"]]


def normalize_references(job: Mapping[str, Any], *, kind: str) -> list[dict[str, Any]]:
    """Normalize product/model reference entries and retain their roles."""

    product = job.get("product") if isinstance(job.get("product"), Mapping) else {}
    model = job.get("model") if isinstance(job.get("model"), Mapping) else {}
    if kind == "product":
        raw = first(job, "product_reference_images", "garment_reference_images", default=None)
        if raw is None:
            raw = first(product, "reference_images", "references", "images", default=[])
        default_role = "product_reference"
    else:
        raw = first(job, "model_reference_images", default=None)
        if raw is None:
            raw = first(model, "reference_images", "images", "identity_pack", default=[])
        default_role = "model_identity"
    normalized: list[dict[str, Any]] = []
    for index, entry in enumerate(as_list(raw), 1):
        if isinstance(entry, Mapping):
            item = dict(entry)
            path = first(item, "path", "file", "image", "url", "src")
            role = clean_text(first(item, "role", "reference_role", default=default_role)) or default_role
        else:
            path = entry
            role = default_role
            item = {}
        normalized.append({
            "id": clean_text(first(item, "id", default=f"{kind}-ref-{index}")),
            "path": clean_text(path),
            "role": role,
            "required": as_bool(first(item, "required", default=True), default=True),
            "status": clean_text(first(item, "status", default="provided")).lower(),
        })
    return normalized


def normalize_directions(job: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = first(job, "visual_directions", "directions", "visual_direction", default=[])
    directions: list[dict[str, Any]] = []
    for index, entry in enumerate(as_list(raw), 1):
        if isinstance(entry, Mapping):
            item = dict(entry)
            name = first(item, "name", "title", "label", "id", default=f"direction-{index}")
            selected = as_bool(first(item, "selected", "approved", "active", default=False))
        else:
            name = entry
            item = {}
            selected = False
        direction_id = clean_text(first(item, "id", default=f"direction-{index}")) or f"direction-{index}"
        directions.append({
            "id": direction_id,
            "name": clean_text(name),
            "selected": selected,
            "modules": first(item, "modules", "roles", default=[]),
            "product_fit": first(item, "product_fit", "garment_fit", "fit", default=""),
            "camera": first(item, "camera", "camera_language", "lens", default=""),
            "negative_space": first(item, "negative_space", "safe_space", default=""),
            "why": first(item, "why", "rationale", "reason", default=""),
            "composability": first(item, "composability", "composable_with", "compatible_with", default=""),
            "scene": first(item, "scene", "environment", default=""),
            "lighting": first(item, "lighting", default=""),
            "palette": first(item, "palette", "color_palette", default=""),
            "risk": first(item, "risk", "risks", default=""),
            "paid_calls": first(item, "paid_calls", "estimated_calls", default=None),
            "moments": first(item, "moments", "moments_suitable", default=None),
        })
    return directions


def normalize_sku(job: Mapping[str, Any]) -> dict[str, str]:
    raw = first(job, "sku", "product_sku", default=None)
    product = job.get("product") if isinstance(job.get("product"), Mapping) else {}
    if raw is None:
        raw = first(product, "sku", "id", "code", default=None)
    if isinstance(raw, Mapping):
        return {
            "id": clean_text(first(raw, "id", "code", "sku", "value")),
            "name": clean_text(first(raw, "name", "title", default="")),
            "variant": clean_text(first(raw, "variant", "color", "option", default="")),
        }
    return {
        "id": clean_text(raw),
        "name": clean_text(first(job, "product_name", "name", default=first(product, "name", "title", default=""))),
        "variant": clean_text(first(job, "variant", "color", default=first(product, "variant", "color", default=""))),
    }


def normalize_model(job: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one or more independent approved model identity packs.

    The legacy ``model`` object remains accepted for one model.  A two-model
    job must use ``models: [...]`` so each identity has its own id, approval
    flag, and reference-image list; callers can validate those packs
    independently instead of accidentally reusing one identity.
    """

    raw_models = job.get("models")
    using_models_array = isinstance(raw_models, list)
    if using_models_array:
        entries = list(raw_models)
    elif isinstance(job.get("model"), Mapping):
        entries = [job["model"]]
    elif first(job, "model_id", default="") or first(job, "model_reference_images", default=None):
        # Preserve the compact legacy shape where model id/refs live at the
        # top level.  This path is intentionally only one pack.
        entries = [{
            "id": first(job, "model_id", default=""),
            "reference_images": first(job, "model_reference_images", default=[]),
        }]
    else:
        entries = []

    packs: list[dict[str, Any]] = []
    top_level_refs = first(job, "model_reference_images", default=None)
    for index, entry in enumerate(entries, 1):
        raw = dict(entry) if isinstance(entry, Mapping) else {"id": entry}
        if "reference_images" in raw or "references" in raw or "images" in raw or "identity_pack" in raw:
            refs = normalize_references({"model": raw}, kind="model")
        elif top_level_refs is not None and not using_models_array:
            refs = normalize_references({"model_reference_images": top_level_refs}, kind="model")
        else:
            refs = []
        pack = {
            "id": clean_text(first(raw, "id", "name", "model_id", default="")),
            "name": clean_text(first(raw, "name", "label", default="")),
            "approved": as_bool(first(raw, "approved", "selected", default=False)),
            "reference_images": refs,
        }
        pack["pack_index"] = index
        packs.append(pack)

    primary = packs[0] if packs else {
        "id": "",
        "name": "",
        "approved": False,
        "reference_images": [],
        "pack_index": 1,
    }
    return {
        "id": primary["id"],
        "name": primary["name"],
        "approved": primary["approved"],
        "reference_images": primary["reference_images"],
        "packs": packs,
        "models": packs,
    }


def normalize_deliverables(job: Mapping[str, Any]) -> dict[str, Any]:
    raw = job.get("deliverables") if isinstance(job.get("deliverables"), Mapping) else {}
    count = first(raw, "detail_slices", "detail_slice_count", "detail_screen_count", "detail_count", default=None)
    if count is None:
        count = first(job, "detail_slices", "detail_slice_count", "detail_screen_count", "detail_count", default=8)
    try:
        count = int(count)
    except (TypeError, ValueError):
        count = -1
    include_size = first(raw, "include_size", "size_module", "include_size_module", default=None)
    if isinstance(include_size, Mapping):
        include_size = True
    if include_size is None:
        include_size = True
    model_count = first(raw, "model_count", "models", default=first(job, "model_count", default=None))
    if isinstance(model_count, list):
        model_count = len(model_count)
    if model_count is None:
        model_entries = job.get("models")
        model_count = len(model_entries) if isinstance(model_entries, list) else 1
    try:
        model_count = int(model_count)
    except (TypeError, ValueError):
        model_count = -1
    requested_views = first(
        raw,
        "requested_views",
        "views",
        default=first(job, "requested_views", "views", default=[]),
    )
    return {
        "detail_slices": count,
        "include_size": as_bool(include_size, default=True),
        "model_count": model_count,
        "slots": as_list(first(raw, "slots", "image_slots", default=first(job, "slots", default=[]))),
        "requested_views": as_list(requested_views),
        "channels": as_list(first(raw, "channels", "targets", default=first(job, "channels", default=[]))),
        "additional_model_variant_calls": first(
            raw,
            "additional_model_variant_calls",
            "model_variant_calls",
            default=first(job, "additional_model_variant_calls", "model_variant_calls", default=0),
        ),
    }


def size_source(job: Mapping[str, Any], *, base_dir: Path | None = None) -> dict[str, Any] | None:
    product = job.get("product") if isinstance(job.get("product"), Mapping) else {}
    raw = first(job, "size_source", "size_chart", "sizing_source", default=None)
    if raw is None:
        raw = first(product, "size_source", "size_chart", "sizing_source", default=None)
    if raw is None:
        return None
    if isinstance(raw, Mapping):
        item = dict(raw)
        path = first(item, "path", "file", "source_path", "url")
        status = clean_text(first(item, "status", "fact_status", default="unknown")).lower()
        kind = clean_text(first(item, "type", "kind", default="size_chart"))
    else:
        path = raw
        status = "provided"
        kind = "size_chart"
        item = {}
    item.update({"path": clean_text(path), "status": status, "type": kind})
    # A URL has not been read or verified by this local-only helper.  It is
    # retained as provenance text but must fall back to qualitative guidance;
    # numeric size output is allowed only for an approved local file.
    item["available"] = status in APPROVED_FACT_STATUSES and path_exists(path, base_dir=base_dir)
    return item


def relative_or_absolute(raw: Any, *, base_dir: Path | None = None) -> str:
    text = clean_text(raw)
    if not text:
        return ""
    path = resolve_path(text, base_dir=base_dir)
    if path is None:
        return text
    if base_dir is not None:
        try:
            return str(path.relative_to(base_dir.resolve()))
        except ValueError:
            pass
    return str(path)


def error_result(errors: Iterable[str], warnings: Iterable[str] = ()) -> dict[str, Any]:
    errors_list = list(errors)
    return {"ok": not errors_list, "errors": errors_list, "warnings": list(warnings)}
