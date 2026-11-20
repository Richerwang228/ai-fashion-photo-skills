#!/usr/bin/env python3
"""Build a local, approval-gated plan for one clothing SKU.

This command only reads and writes JSON.  It never calls an image provider,
resolves a URL, or reads an API key.  The output is intentionally useful both
as a human approval sheet and as the input contract for ``build_prompt.py``.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

from common import (
    APPROVED_FACT_STATUSES,
    ValidationError,
    dump_json,
    load_json,
    normalize_deliverables,
    normalize_directions,
    normalize_fact_items,
    normalize_model,
    normalize_references,
    normalize_sku,
    relative_or_absolute,
    size_source,
    validate_local_image,
)


SLOT_LIBRARY = [
    {
        "id": "product-hero",
        "type": "product-main",
        "role": "product-only hero",
        "question": "这件商品本身是什么样？",
        "aspect_ratio": "1:1",
        "template": "product-main.txt",
        "reference_roles": ["front"],
        "presentation_mode": "product_only",
        "visual_family": "product_truth_clean",
        "background_treatment": "克制暖白无缝棚拍，仅此一屏作为商品真值母图",
    },
    {
        "id": "model-hero",
        "type": "model-master",
        "role": "approved-model hero",
        "question": "穿上后的整体廓形与长度如何？",
        "aspect_ratio": "4:5",
        "template": "model-master.txt",
        "reference_roles": ["front"],
        "model_group_id": "primary",
        "presentation_mode": "model",
        "visual_family": "worn_editorial",
        "background_treatment": "品牌中性色的安静编辑场景，与白底商品母图区分",
    },
    {
        "id": "front-back-fit",
        "type": "detail-slice",
        "role": "front/back and fit evidence",
        "question": "正背面和版型是否一致？",
        "aspect_ratio": "4:5",
        "template": "detail-slice.txt",
        "reference_roles": ["front", "back"],
        "presentation_mode": "product_only",
        "visual_family": "evidence_layout",
        "background_treatment": "浅暖灰分栏或前后对照版式，不做第二张纯白主图",
    },
    {
        "id": "macro-material",
        "type": "macro-detail",
        "role": "fabric and surface detail",
        "question": "面料表面、纹理和质感是什么样？",
        "aspect_ratio": "1:1",
        "template": "macro-detail.txt",
        "reference_roles": ["material"],
        "presentation_mode": "product_only",
        "visual_family": "material_macro",
        "background_treatment": "同一品牌色系的侧光微距与局部暗角，强调真实纹理",
    },
    {
        "id": "construction-selling-point",
        "type": "selling-point",
        "role": "verified construction selling point",
        "question": "口袋、拉链、五金、缝线或下摆有哪些可核验细节？",
        "aspect_ratio": "4:5",
        "template": "selling-point.txt",
        "reference_roles": ["construction"],
        "presentation_mode": "floating_product_poster",
        "visual_family": "designed_selling_point",
        "background_treatment": "品牌色块、留白与结构标注组成的卖点海报",
    },
    {
        "id": "lifestyle-use",
        "type": "lifestyle",
        "role": "plausible styling or lifestyle use",
        "question": "真实穿着场景如何？",
        "aspect_ratio": "4:5",
        "template": "lifestyle.txt",
        "reference_roles": ["front"],
        "presentation_mode": "model",
        "visual_family": "lifestyle_scene",
        "background_treatment": "自然但克制的穿着场景，保持商品为视觉中心",
    },
    {
        "id": "size-module",
        "type": "detail-slice",
        "role": "size and fit guidance",
        "question": "尺码、松量和测量位置如何理解？",
        "aspect_ratio": "4:5",
        "template": "detail-slice.txt",
        "reference_roles": [],
        "presentation_mode": "floating_product_poster",
        "visual_family": "information_graphic",
        "background_treatment": "品牌信息卡与版型示意，不使用第二张白底商品照",
    },
    {
        "id": "brand-close",
        "type": "detail-slice",
        "role": "brand close and next action",
        "question": "购买前最后需要记住什么？",
        "aspect_ratio": "4:5",
        "template": "detail-slice.txt",
        "reference_roles": ["front"],
        "presentation_mode": "floating_product_poster",
        "visual_family": "brand_close",
        "background_treatment": "深一档品牌底色或纸张质感的收束页，轻提示下一步",
    },
]


VOLATILE_TERMS = (
    "price", "discount", "stock", "availability", "review", "rating", "performance",
    "价格", "折扣", "库存", "缺货", "有货", "现货", "售罄", "评价", "评分", "销量",
    "功效", "性能", "限时", "仅剩", "马上抢", "抢购", "促销",
)
BLOCKED_SLOT_STATUSES = {"blocked", "needs_reference", "needs-reference", "deferred", "rejected"}
MODEL_SLOT_TYPES = {"model-master", "model", "model-hero"}
COMPLETE_SET_SCENE_FAMILIES = {"worn_editorial", "lifestyle_scene", "editorial_scene", "brand_close"}
COMPLETE_SET_DESIGN_FAMILIES = {"designed_selling_point", "information_graphic"}


def _canonical(value: Any) -> str:
    return " ".join("".join(char if char.isalnum() else " " for char in str(value).lower()).split())


def _role_matches(reference_role: Any, required_role: Any) -> bool:
    """Match a narrow reference role without treating every image as a fit."""

    reference = _canonical(reference_role)
    required = _canonical(required_role)
    if not reference or not required:
        return False
    aliases = {
        "front": {"front", "garment front", "product front", "front view", "hero front", "top front", "bottom front"},
        "back": {"back", "garment back", "product back", "back view", "rear"},
        "top front": {"top front", "top garment front", "top front view"},
        "bottom front": {"bottom front", "bottom garment front", "bottom front view"},
        "top back": {"top back", "top rear", "top back view", "top garment back", "garment back"},
        "bottom back": {"bottom back", "bottom rear", "bottom back view", "trouser back", "bottom garment back"},
        "material": {"material", "fabric", "texture", "surface", "fabric texture"},
        "construction": {"construction", "pocket", "zipper", "hardware", "seam", "hem", "waistband", "cuff"},
    }
    if required in aliases:
        if reference in aliases[required]:
            return True
        # A named construction/material detail can satisfy its family slot,
        # while a generic back can never satisfy top_back/bottom_back.
        return required in {"material", "construction"} and any(token in reference for token in aliases[required])
    return reference == required


def _role_entries(raw: Any) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    values = raw if isinstance(raw, list) else ([] if raw in (None, "") else [raw])
    for value in values:
        if isinstance(value, dict):
            role = value.get("role", value.get("reference_role", value.get("name", "")))
            entries.append({"role": str(role).strip(), **value})
        else:
            entries.append({"role": str(value).strip()})
    return [entry for entry in entries if entry.get("role")]


def _slot_reference_roles(slot: dict[str, Any]) -> list[str]:
    roles = _role_entries(slot.get("reference_roles", slot.get("required_reference_roles", slot.get("source_roles", []))))
    result = [str(item["role"]).strip() for item in roles if item.get("role")]
    view = str(slot.get("required_view", slot.get("view", slot.get("source_view", "")))).strip()
    specific_back = _canonical(view) == "back" and any(_canonical(role) in {"top back", "bottom back"} for role in result)
    if view and not specific_back and not any(_canonical(view) == _canonical(role) for role in result):
        result.append(view)
    named = str(slot.get("named_detail", slot.get("detail_name", ""))).strip()
    if named and not any(_canonical(named) == _canonical(role) for role in result):
        result.append(named)
    return result


def _matching_product_refs(product_refs: list[dict[str, Any]], roles: list[str]) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    for role in roles:
        matches = [item for item in product_refs if _role_matches(item.get("role", ""), role)]
        for item in matches:
            if item not in matched:
                matched.append(item)
    return matched


def _garment_profile(
    job: dict[str, Any],
    facts: list[dict[str, Any]],
    *,
    sale_mode: str = "single_item",
) -> tuple[bool, bool]:
    context_parts = [str(job.get("category", "")), str(job.get("product_type", ""))]
    product = job.get("product")
    if isinstance(product, dict):
        context_parts.extend(str(product.get(key, "")) for key in ("category", "type", "name"))
    context_parts.extend(str(item.get("value", "")) for item in facts if item.get("key") in {"category", "product_type", "garment_type", "set_type"})
    context = _canonical(" ".join(context_parts))
    # Whether two garments are sold together is a business fact, never a visual,
    # filename, SKU, category-name, or language-model inference.
    is_set = sale_mode == "true_set"
    is_bottom = any(token in context for token in ("trouser", "pants", "bottom", "skirt", "裤", "半裙")) and not is_set
    return is_set, is_bottom


def _refine_slot_roles(
    slots: list[dict[str, Any]],
    *,
    job: dict[str, Any],
    facts: list[dict[str, Any]],
    sale_mode: str,
) -> None:
    """Expand generic front/back roles to top/bottom component evidence."""

    is_set, is_bottom = _garment_profile(job, facts, sale_mode=sale_mode)
    for slot in slots:
        roles = _slot_reference_roles(slot)
        refined: list[str] = []
        for role in roles:
            canonical = _canonical(role)
            replacement: list[str] | None = None
            if canonical == "front":
                replacement = ["top_front", "bottom_front"] if is_set else (["bottom_front"] if is_bottom else ["front"])
            elif canonical == "back":
                replacement = ["top_back", "bottom_back"] if is_set else (["bottom_back"] if is_bottom else ["back"])
            for candidate in replacement or [role]:
                if candidate not in refined:
                    refined.append(candidate)
        slot["reference_roles"] = refined


def _contains_volatile(value: Any) -> bool:
    text = _canonical(value)
    return any(_canonical(term) in text for term in VOLATILE_TERMS)


def _copy_rows(job: dict[str, Any]) -> list[dict[str, Any]]:
    raw = job.get("copy_ledger", job.get("copy", job.get("approved_chinese_copy", [])))
    if isinstance(raw, dict):
        raw = raw.get("rows", raw.get("items", [raw]))
    rows: list[dict[str, Any]] = []
    for index, value in enumerate(raw if isinstance(raw, list) else [raw], 1):
        if isinstance(value, dict):
            row = dict(value)
        elif value not in (None, ""):
            row = {"id": f"copy-{index}", "text": value}
        else:
            continue
        row.setdefault("id", f"copy-{index}")
        row["id"] = str(row["id"]).strip()
        row["status"] = str(row.get("status", "unknown")).strip().lower()
        row["evidence"] = row.get("evidence", row.get("source", row.get("source_path", "")))
        row["allowed_surface"] = row.get("allowed_surface", row.get("surface", ""))
        row["text"] = row.get("text", row.get("copy", row.get("value", "")))
        rows.append(row)
    return rows


def _normalize_custom_slot(value: Any, index: int) -> dict[str, Any]:
    raw = dict(value) if isinstance(value, dict) else {"id": value}
    slot_id = str(raw.get("id", raw.get("slot_id", f"slot-{index}"))).strip() or f"slot-{index}"
    slot_type = str(raw.get("type", raw.get("slot_type", "detail-slice"))).strip() or "detail-slice"
    slot = {
        **raw,
        "id": slot_id,
        "type": slot_type,
        "role": str(raw.get("role", raw.get("title", slot_type))).strip(),
        "question": str(raw.get("question", raw.get("shopper_question", raw.get("goal", "")))).strip(),
        "risk": str(raw.get("risk", raw.get("failure_risk", ""))).strip(),
        "reference_roles": [item["role"] for item in _role_entries(raw.get("reference_roles", raw.get("required_reference_roles", raw.get("source_roles", []))))],
        "copy_ids": raw.get("copy_ids", raw.get("copy_id", [])),
    }
    if not isinstance(slot["copy_ids"], list):
        slot["copy_ids"] = [slot["copy_ids"]] if slot["copy_ids"] else []
    if raw.get("required_view", raw.get("view", raw.get("source_view", ""))):
        slot["required_view"] = raw.get("required_view", raw.get("view", raw.get("source_view")))
    if raw.get("named_detail", raw.get("detail_name", "")):
        slot["named_detail"] = raw.get("named_detail", raw.get("detail_name"))
    return slot


def _view_request(value: Any, index: int) -> dict[str, Any]:
    if isinstance(value, dict):
        item = dict(value)
    else:
        item = {"id": value, "view": value}
    item.setdefault("id", f"requested-view-{index}")
    item.setdefault("view", item.get("required_view", item.get("name", item["id"])))
    item.setdefault("question", item.get("shopper_question", f"展示 {item['view']} 证据"))
    item.setdefault("risk", item.get("failure_risk", ""))
    return item


def _reference_errors(references: list[dict[str, Any]], label: str, base_dir: Path, *, required: bool = True) -> list[str]:
    errors: list[str] = []
    if required and not references:
        errors.append(f"{label} reference images are required")
    for item in references:
        path = item.get("path", "")
        if not path:
            errors.append(f"{label} reference {item.get('id', '?')} has no path")
            continue
        # A URL may be recorded but is deliberately not fetched.  Requiring a
        # local file keeps this planner deterministic and offline by default.
        if "://" in path:
            errors.append(f"{label} reference is not local (network access is disabled): {path}")
        else:
            valid, reason = validate_local_image(path, base_dir=base_dir)
            if not valid:
                errors.append(f"{label} reference is not a valid local image: {path} ({reason})")
    return errors


def _guidance_value(job: dict[str, Any], source: dict[str, Any] | None, keys: tuple[str, ...], default: str) -> str:
    """Read qualitative fit guidance without deriving numeric sizes."""

    containers: list[dict[str, Any]] = []
    if isinstance(source, dict):
        containers.append(source)
    for key in ("size_guidance", "fit_guidance", "sizing_guidance"):
        value = job.get(key)
        if isinstance(value, dict):
            containers.append(value)
    product = job.get("product")
    if isinstance(product, dict):
        for key in ("size_guidance", "fit_guidance", "sizing_guidance"):
            value = product.get(key)
            if isinstance(value, dict):
                containers.append(value)
    for container in containers:
        for key in keys:
            value = container.get(key)
            if value not in (None, ""):
                return str(value).strip()
    return default


FIT_FORBIDDEN_PATTERN = re.compile(r"(?:\b(?:XS|S|M|L|XL|XXL)\b|cm\b|厘米|kg\b|公斤|斤|身高|体重|\d)", re.IGNORECASE)


def _safe_fit_text(value: Any, default: str) -> str:
    text = str(value).strip() if value not in (None, "") else ""
    return text if text and not FIT_FORBIDDEN_PATTERN.search(text) else default


def _numeric_size_source_valid(source: dict[str, Any] | None, *, base_dir: Path) -> tuple[bool, str]:
    if not source or not source.get("available"):
        return False, "source is not an approved local file"
    raw_path = str(source.get("path", "")).strip()
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    path = path.resolve()
    if not path.is_file() or path.stat().st_size == 0:
        return False, "source file is missing or empty"
    suffix = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        text = ""
    if suffix == ".json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return False, "JSON size source is not valid JSON"
        serialized = json.dumps(parsed, ensure_ascii=False).lower()
        if not any(token in serialized for token in ("size", "尺码", "measurement", "measure", "胸围", "腰围", "衣长")):
            return False, "JSON size source has no measurement fields"
        if not any(token in serialized for token in ("unit", "cm", "厘米", "inch", "英寸")):
            return False, "JSON size source has no measurement unit"
        if not _json_has_numeric_size_row(parsed):
            return False, "JSON size source has no numeric size row"
    elif suffix in {".csv", ".tsv", ".txt"}:
        lowered = text.lower()
        if not text.strip():
            return False, "text size source is empty"
        if not any(token in lowered for token in ("size", "尺码", "measurement", "measure", "胸围", "腰围", "衣长")):
            return False, "text size source has no measurement fields"
        if not any(token in lowered for token in ("unit", "cm", "厘米", "inch", "英寸")):
            return False, "text size source has no measurement unit"
        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) < 2 or not any(char.isdigit() for char in " ".join(lines[1:])):
            return False, "text size source has no numeric data row"
    elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".pdf"}:
        reviewer = source.get("verified_by", source.get("reviewer", ""))
        approved_at = source.get("approved_at", source.get("approval_time", ""))
        if source.get("status") not in APPROVED_FACT_STATUSES or not reviewer or not approved_at:
            return False, "image/PDF size source requires reviewer and approved_at"
    return True, ""


def _json_has_numeric_size_row(value: Any) -> bool:
    if isinstance(value, list):
        return any(_json_has_numeric_size_row(item) for item in value)
    if not isinstance(value, dict):
        return False
    keys = {_canonical(key) for key in value}
    has_size = bool(keys & {"size", "尺码", "size label", "尺码标签"})
    measure_keys = {"chest", "bust", "waist", "hip", "length", "garment measurement", "measurement", "胸围", "腰围", "臀围", "衣长", "裤长"}
    has_measurement = any(_canonical(key) in measure_keys or "measure" in _canonical(key) for key in value)
    if has_size and has_measurement and any(bool(re.search(r"\d", str(item))) for item in value.values()):
        return True
    return any(_json_has_numeric_size_row(item) for item in value.values())


def _build_size_module(source: dict[str, Any] | None, *, base_dir: Path, job: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    source_valid, source_reason = _numeric_size_source_valid(source, base_dir=base_dir)
    if source and source_valid:
        return {
            "mode": "numeric",
            "type": "verified-size-chart",
            "source": relative_or_absolute(source.get("path"), base_dir=base_dir),
            "source_status": source.get("status"),
            "required_fields": ["size", "garment_measurement", "measurement_unit"],
            "verified_by": source.get("verified_by", source.get("reviewer", "")),
            "approved_at": source.get("approved_at", source.get("approval_time", "")),
            "instruction": "只使用来源中的数值，不从图片或模特反推尺码。",
        }, warnings
    if source and source_reason:
        warnings.append("size source was not accepted for numeric output: " + source_reason)
    if source and "//" in str(source.get("path", "")):
        warnings.append("size source URL was not fetched; numeric size module was replaced with qualitative guidance")
    elif source:
        warnings.append("size source is missing, unapproved, or unavailable; numeric size module was replaced")
    else:
        warnings.append("no real size source supplied; numeric size module was replaced")
    # These defaults explicitly describe what still needs confirmation.  They
    # contain no S/M/L values and never infer measurements from a photograph.
    guidance = {
        "fit": _safe_fit_text(_guidance_value(job, source, ("fit", "fit_description", "silhouette"), "版型：根据实物平铺与试穿记录描述贴身、合体或宽松程度。"), "版型：根据实物平铺与试穿记录描述贴身、合体或宽松程度。"),
        "ease": _safe_fit_text(_guidance_value(job, source, ("ease", "ease_description", "松量"), "松量：只记录可观察的活动余量，不填写未核验数值。"), "松量：只记录可观察的活动余量，不填写未核验数值。"),
        "measuring_positions": _safe_fit_text(_guidance_value(job, source, ("measuring_positions", "measurement_positions", "positions"), "测量位置：记录肩宽、胸围、腰围、臀围、衣长或裤长等实际测量点。"), "测量位置：记录肩宽、胸围、腰围、臀围、衣长或裤长等实际测量点。"),
        "styling_guidance": _safe_fit_text(_guidance_value(job, source, ("styling_guidance", "styling", "fit_styling"), "搭配说明：结合确认的版型与长度给出穿着场景建议。"), "搭配说明：结合确认的版型与长度给出穿着场景建议。"),
    }
    return {
        "mode": "fit-guidance",
        "type": "fit-guidance",
        "source": None,
        "source_status": "unknown",
        "required_fields": ["fit", "ease", "measuring_positions", "styling_guidance"],
        **guidance,
        "guidance": guidance,
        "instruction": "不得编造数字尺码；改写为版型、松量、测量位置和搭配说明。",
    }, warnings


def _slots(
    count: int,
    size_module: dict[str, Any],
    *,
    custom: list[Any] | None = None,
    requested_views: list[Any] | None = None,
) -> list[dict[str, Any]]:
    if custom:
        selected = [_normalize_custom_slot(item, index) for index, item in enumerate(custom, 1)]
    else:
        # Nine and ten-screen sets must be authored slots; never fill them with
        # generic "detail-extra" placeholders that answer no buyer question.
        selected = [dict(item) for item in SLOT_LIBRARY[: min(count, len(SLOT_LIBRARY))]]

    # Attach requested view constraints to the narrowest existing slot.  A
    # request that has no safe built-in home becomes an explicit slot and is
    # subsequently checked for question/source/copy/risk completeness.
    view_home = {
        "front": "product-hero",
        "back": "front-back-fit",
        "top back": "front-back-fit",
        "bottom back": "front-back-fit",
    }
    for index, request_value in enumerate(requested_views or [], 1):
        request = _view_request(request_value, index)
        request_id = str(request.get("id", "")).strip()
        view = str(request.get("required_view", request.get("view", ""))).strip()
        target = next((slot for slot in selected if slot.get("id") == request_id), None)
        if target is None:
            target = next((slot for slot in selected if slot.get("id") == view_home.get(_canonical(view))), None)
        if target is None:
            target = _normalize_custom_slot({
                **request,
                "id": request_id or f"requested-view-{index}",
                "type": request.get("type", "detail-slice"),
                "required_view": view,
                "reference_roles": request.get("reference_roles", [view] if view else []),
            }, len(selected) + 1)
            selected.append(target)
        target["requested_view"] = view
        if view:
            target["required_view"] = view
        request_roles = [item["role"] for item in _role_entries(request.get("reference_roles", request.get("required_reference_roles", [view] if view else [])))]
        existing_roles = [str(role) for role in target.get("reference_roles", [])]
        if _canonical(view) == "back" and any(_canonical(role) in {"top back", "bottom back"} for role in request_roles):
            existing_roles = [role for role in existing_roles if _canonical(role) not in {"front", "back"}]
        elif _canonical(view) == "back" and request_roles:
            existing_roles = [role for role in existing_roles if _canonical(role) not in {"front", "back"}]
        for role in request_roles:
            if role and role not in existing_roles:
                existing_roles.append(role)
        target["reference_roles"] = existing_roles
        if request.get("question") and not target.get("question"):
            target["question"] = str(request["question"]).strip()
        if request.get("risk") and not target.get("risk"):
            target["risk"] = str(request["risk"]).strip()

    for slot in selected:
        if slot["id"] == "size-module":
            slot["module"] = size_module["mode"]
            slot["role"] = "fit guidance (no numeric size source)" if size_module["mode"] == "fit-guidance" else slot["role"]
            slot["copy_rule"] = size_module["instruction"]
    return selected


def _validate_direction_fields(directions: list[dict[str, Any]], errors: list[str]) -> None:
    required = ("modules", "product_fit", "camera", "negative_space", "why", "composability")
    seen: set[str] = set()
    for direction in directions:
        direction_id = str(direction.get("id", "")).strip()
        if direction_id in seen:
            errors.append(f"duplicate visual direction id: {direction_id}")
        seen.add(direction_id)
        for field in required:
            value = direction.get(field)
            if value in (None, "", [], {}):
                errors.append(f"visual direction {direction_id or '[missing]'} requires {field}")


def _validate_slot_completeness(slots: list[dict[str, Any]], *, count: int, custom: bool, errors: list[str]) -> None:
    if count in (9, 10) and not custom:
        errors.append("9-10 screen sets require explicit deliverables.slots; generic extras are not allowed")
    if custom and len(slots) != count:
        errors.append(f"deliverables.slots contains {len(slots)} slots but detail_slices={count}")
    seen: set[str] = set()
    for slot in slots:
        slot_id = str(slot.get("id", "")).strip()
        if slot_id in seen:
            errors.append(f"duplicate slot id: {slot_id}")
        seen.add(slot_id)
        if custom and count in (9, 10):
            if not slot.get("question"):
                errors.append(f"custom slot {slot_id} requires shopper question")
            if not _slot_reference_roles(slot) and not slot.get("source") and not slot.get("source_refs"):
                errors.append(f"custom slot {slot_id} requires source/reference roles")
            if not slot.get("copy_ids") and not slot.get("copy") and not slot.get("copy_ledger"):
                errors.append(f"custom slot {slot_id} requires copy/copy id state")
            if not slot.get("risk"):
                errors.append(f"custom slot {slot_id} requires risk")


def _validate_facts_and_copy(
    facts: list[dict[str, Any]],
    copy_rows: list[dict[str, Any]],
    errors: list[str],
    warnings: list[str],
) -> list[dict[str, Any]]:
    valid_statuses = {
        "confirmed", "approved", "verified", "documented", "creative", "recommendation",
        "provisional", "pending", "unknown", "unconfirmed",
    }
    approved: list[dict[str, Any]] = []
    for item in facts:
        status = str(item.get("status", "")).strip().lower()
        key = str(item.get("key", "fact")).strip() or "fact"
        value = item.get("value", "")
        evidence = item.get("evidence", item.get("source", ""))
        if status not in valid_statuses:
            errors.append(f"unsupported fact status: {status or '[missing]'}")
        if status in APPROVED_FACT_STATUSES:
            if value in (None, "", [], {}):
                errors.append(f"approved fact {key} requires a non-empty value")
            if evidence in (None, "", [], {}):
                errors.append(f"approved fact {key} requires evidence")
            volatile = _contains_volatile(key) or _contains_volatile(value)
            temporary = bool(item.get("temporary_asset") or item.get("temporary_asset_id"))
            temporary_surface = _canonical(item.get("allowed_surface", "")) in {"temporary", "temporary asset", "temporary_asset", "campaign"}
            if volatile and not (temporary and temporary_surface):
                errors.append(f"volatile fact {key} cannot enter permanent product facts; use a temporary asset ledger")
            elif not volatile:
                approved.append(item)
        elif status not in {"creative", "recommendation", "provisional", "pending", "unknown", "unconfirmed"}:
            warnings.append(f"fact {key} is not approved ({status or '[missing]'})")

    for row in copy_rows:
        status = str(row.get("status", "")).strip().lower()
        row_id = str(row.get("id", "copy")).strip() or "copy"
        if _contains_volatile(row.get("text", "")):
            errors.append(
                f"copy row {row_id} contains price/discount/stock/urgency language; "
                "put it in a separately approved temporary asset"
            )
        if status not in valid_statuses:
            errors.append(f"copy row {row_id} has unsupported status: {status or '[missing]'}")
        if status in APPROVED_FACT_STATUSES:
            if row.get("text") in (None, "", [], {}):
                errors.append(f"approved copy row {row_id} requires non-empty text")
            if row.get("evidence") in (None, "", [], {}):
                errors.append(f"approved copy row {row_id} requires evidence")
            if _canonical(row.get("allowed_surface", "")) not in {"image text", "image_text"}:
                errors.append(f"approved copy row {row_id} requires allowed_surface=image_text")
    return approved


def _strict_role_matches(reference_role: Any, required_role: Any, *, is_set: bool) -> bool:
    required = _canonical(required_role)
    reference = _canonical(reference_role)
    if is_set and required in {"top front", "bottom front", "top back", "bottom back"}:
        return reference == required or reference == f"{required} view"
    for component in ("top", "bottom"):
        for family in ("material", "construction"):
            if required == f"{component} {family}":
                return reference.startswith(component + " ") and (
                    family in reference
                    or (family == "material" and any(token in reference for token in ("fabric", "texture", "surface")))
                    or (family == "construction" and any(token in reference for token in ("pocket", "zipper", "hardware", "seam", "hem", "waistband", "cuff")))
                )
    return _role_matches(reference_role, required_role)


def _bind_slot_references(
    slots: list[dict[str, Any]],
    product_refs: list[dict[str, Any]],
    model: dict[str, Any],
    model_count: int,
    *,
    errors: list[str],
    warnings: list[str],
) -> None:
    packs = model.get("packs", []) if isinstance(model.get("packs"), list) else []
    pack_by_id = {str(pack.get("id")): pack for pack in packs if pack.get("id")}
    is_set = any(
        _canonical(role) in {"top front", "bottom front", "top back", "bottom back"}
        for slot in slots
        for role in _slot_reference_roles(slot)
    )
    for slot in slots:
        slot_id = str(slot.get("id", "slot"))
        roles = _slot_reference_roles(slot)
        slot["reference_roles"] = roles
        matched: list[dict[str, Any]] = []
        for role in roles:
            for item in product_refs:
                if _strict_role_matches(item.get("role", ""), role, is_set=is_set) and item not in matched:
                    matched.append(item)
        slot["reference_paths"] = matched
        missing_roles = [role for role in roles if not any(_strict_role_matches(item.get("role", ""), role, is_set=is_set) for item in matched)]
        if missing_roles:
            slot["status"] = "NEEDS_REFERENCE"
            slot["blocked_reason"] = "missing product reference role: " + ", ".join(missing_roles)
            errors.append(f"slot {slot_id} NEEDS_REFERENCE: {slot['blocked_reason']}")

        slot_type = str(slot.get("type", "")).strip().lower()
        is_model = slot_type in MODEL_SLOT_TYPES or slot_id == "model-hero"
        if is_model:
            if model_count == 0:
                slot["status"] = "deferred"
                slot["model_group_id"] = ""
                slot["blocked_reason"] = "model imagery was not requested; model hero is deferred"
                warnings.append(f"slot {slot_id} deferred: {slot['blocked_reason']}")
                continue
            requested_group = str(slot.get("model_group_id", "")).strip()
            if not requested_group and model_count == 1 and packs:
                requested_group = str(packs[0].get("id", "")).strip()
            if not requested_group:
                slot["status"] = "deferred" if model_count == 0 else "blocked"
                slot["blocked_reason"] = "no model_group_id/model identity pack is approved"
                warnings.append(f"slot {slot_id} is {slot['status']}: {slot['blocked_reason']}")
            elif requested_group in {"primary", "model-1"} and packs:
                requested_group = str(packs[0].get("id", "")).strip()
            pack = pack_by_id.get(requested_group)
            slot["model_group_id"] = requested_group
            if pack is None:
                slot["status"] = "blocked"
                slot["blocked_reason"] = f"model group is not present in plan.models: {requested_group}"
                errors.append(f"slot {slot_id} blocked: {slot['blocked_reason']}")
            else:
                slot["model_reference_paths"] = pack.get("reference_images", [])
                if not pack.get("approved"):
                    slot["status"] = "blocked"
                    slot["blocked_reason"] = f"model group is not approved: {requested_group}"
                    warnings.append(f"slot {slot_id} blocked: {slot['blocked_reason']}")
                elif not slot.get("status"):
                    slot["status"] = "planned"
        elif not slot.get("status"):
            slot["status"] = "planned"


def _replace_omitted_size_slot(slots: list[dict[str, Any]], *, count: int, include_size: bool) -> list[dict[str, Any]]:
    if include_size:
        return slots
    replaced = [slot for slot in slots if slot.get("id") != "size-module"]
    if len(replaced) >= count:
        return replaced[:count]
    replaced.append({
        "id": "fit-evidence",
        "type": "detail-slice",
        "role": "qualitative fit evidence",
        "question": "不提供数值尺码时，如何判断版型和穿着场景？",
        "risk": "不得把模特身材或图片反推出数值尺码。",
        "aspect_ratio": "4:5",
        "template": "detail-slice.txt",
        "reference_roles": ["front"],
        "copy_ids": [],
        "status": "planned",
    })
    return replaced[:count]


def _model_extra_outputs(
    model_packs: list[dict[str, Any]],
    product_refs: list[dict[str, Any]],
    *,
    job: dict[str, Any],
    facts: list[dict[str, Any]],
    sale_mode: str,
) -> list[dict[str, Any]]:
    """Expose second-model masters as explicit, independently bound outputs."""

    is_set, is_bottom = _garment_profile(job, facts, sale_mode=sale_mode)
    if is_set:
        roles = ["top_front", "bottom_front"]
    elif is_bottom:
        roles = ["bottom_front"]
    else:
        roles = ["front"]
    outputs: list[dict[str, Any]] = []
    for pack in model_packs[1:2]:
        matched: list[dict[str, Any]] = []
        for role in roles:
            for item in product_refs:
                if _strict_role_matches(item.get("role", ""), role, is_set=is_set) and item not in matched:
                    matched.append(item)
        outputs.append({
            "id": f"model-hero-{pack.get('id', 'unknown')}",
            "type": "model-master",
            "role": "additional approved-model master",
            "question": "第二独立模特组的完整廓形如何？",
            "aspect_ratio": "4:5",
            "template": "model-master.txt",
            "reference_roles": roles,
            "reference_paths": matched,
            "model_group_id": str(pack.get("id", "")),
            "model_reference_paths": pack.get("reference_images", []),
            "status": "planned" if pack.get("approved") and matched else "NEEDS_REFERENCE",
            "billable": bool(pack.get("approved") and matched),
            "blocked_reason": "missing front reference for second model" if not matched else "",
        })
    return outputs


def _expand_requested_views(requested: list[Any], job: dict[str, Any], facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand a generic ``back`` request into garment-specific back roles."""

    context_parts = [str(job.get("category", "")), str(job.get("product_type", ""))]
    product = job.get("product")
    if isinstance(product, dict):
        context_parts.extend(str(product.get(key, "")) for key in ("category", "type", "name"))
    context_parts.extend(str(item.get("value", "")) for item in facts if item.get("key") in {"category", "product_type", "garment_type", "set_type"})
    context = _canonical(" ".join(context_parts))
    relationship = _normalize_product_relationship(job, [])
    is_set = relationship["mode"] == "true_set"
    is_bottom = any(token in context for token in ("trouser", "pants", "bottom", "skirt", "裤", "半裙")) and not is_set
    expanded: list[dict[str, Any]] = []
    for index, raw in enumerate(requested, 1):
        item = _view_request(raw, index)
        view = _canonical(item.get("required_view", item.get("view", "")))
        if view == "back":
            if relationship["mode"] == "separate_pairing":
                # Keep the base request generic; it will be materialized once
                # for the top unit and once for the bottom unit later.
                item["reference_roles"] = ["back"]
            elif is_set:
                item["reference_roles"] = ["top_back", "bottom_back"]
            elif is_bottom:
                item["reference_roles"] = ["bottom_back"]
            else:
                # A single garment may label its rear evidence simply
                # ``back``/``garment_back``; do not demand a set component.
                item["reference_roles"] = ["back"]
        expanded.append(item)
    return expanded


def _component_roles(product_refs: list[dict[str, Any]]) -> tuple[bool, bool]:
    roles = {_canonical(item.get("role", "")) for item in product_refs}
    has_top = any(role.startswith("top ") or role in {"top", "upper", "upper garment"} for role in roles)
    has_bottom = any(role.startswith("bottom ") or role in {"bottom", "pants", "trousers", "skirt"} for role in roles)
    return has_top, has_bottom


def _normalize_product_relationship(job: dict[str, Any], product_refs: list[dict[str, Any]]) -> dict[str, Any]:
    raw = job.get("product_relationship") if isinstance(job.get("product_relationship"), dict) else {}
    mode_raw = str(raw.get("mode", job.get("sale_mode", job.get("product_relationship_mode", "")))).strip().lower()
    aliases = {
        "single": "single_item", "single-item": "single_item", "单品": "single_item",
        "pairing": "separate_pairing", "fixed_pairing": "separate_pairing",
        "separate": "separate_pairing", "分开卖": "separate_pairing", "固定搭配": "separate_pairing",
        "set": "true_set", "sold_together": "true_set", "套装": "true_set", "整套卖": "true_set",
    }
    mode = aliases.get(mode_raw, mode_raw)
    has_top, has_bottom = _component_roles(product_refs)
    paired_folder = has_top and has_bottom
    explicit_confirmation = raw.get("confirmed_by_user", job.get("sale_mode_confirmed", False))
    confirmed = explicit_confirmation is True or str(explicit_confirmation).strip().lower() in {"true", "yes", "1", "confirmed"}
    if not paired_folder and not mode:
        mode = "single_item"
        confirmed = True
    question = "请确认：这些上衣和裤子是分开售卖的固定搭配，还是作为一个真套装整套售卖？"
    if mode == "separate_pairing":
        work_units = [
            {"id": "top", "order": 1, "product_scope": "top", "detail_set": "full", "companion_scope": "styling_only", "optional_full_outfit_screen": True},
            {"id": "bottom", "order": 2, "product_scope": "bottom", "detail_set": "full", "companion_scope": "styling_only", "optional_full_outfit_screen": True},
        ]
    elif mode == "true_set":
        work_units = [{"id": "set", "order": 1, "product_scope": "top_and_bottom", "detail_set": "combined", "component_detail_coverage": ["top", "bottom"]}]
    else:
        work_units = [{"id": "item", "order": 1, "product_scope": "single_item", "detail_set": "full"}]
    return {
        "mode": mode or "unconfirmed",
        "confirmed_by_user": confirmed,
        "paired_folder_detected_from_roles": paired_folder,
        "confirmation_question": question,
        "inference_policy": "never infer sale relationship from filename, SKU, category text, or images",
        "work_units": work_units,
    }


def _normalize_presentation(job: dict[str, Any]) -> dict[str, Any]:
    raw = job.get("presentation") if isinstance(job.get("presentation"), dict) else {}
    mode_raw = str(raw.get("mode", job.get("presentation_mode", "direct"))).strip().lower()
    aliases = {
        "default": "direct", "simple": "direct", "直出": "direct", "product-only": "product_only", "商品直出": "product_only",
        "ghost": "ghost_mannequin", "invisible_mannequin": "ghost_mannequin", "透明人台": "ghost_mannequin",
        "floating": "floating_product_poster", "悬浮": "floating_product_poster", "悬浮讲解": "floating_product_poster",
        "flat-lay": "flat_lay", "平铺": "flat_lay", "模特": "model",
    }
    mode = aliases.get(mode_raw, mode_raw)
    allowed = {"direct", "product_only", "ghost_mannequin", "floating_product_poster", "flat_lay", "model"}
    return {
        "mode": mode,
        "valid": mode in allowed,
        "optional": mode != "direct",
        "definition": (
            "去除人体但保留衣服被穿着时的立体空腔结构" if mode == "ghost_mannequin" else
            "商品悬浮在设计背景中并配合卖点讲解；不等同于透明人台" if mode == "floating_product_poster" else
            "商品自然平铺展示，不使用人体或隐形人台结构" if mode == "flat_lay" else
            "由已批准模特穿着展示，商品与身份引用严格分离" if mode == "model" else
            "直接依据商品图和已确认事实生成详情页"
        ),
        "extra_baseline_required": False,
        "scope": "legacy_fallback_only",
    }


def _replace_no_model_slots(slots: list[dict[str, Any]], model_count: int) -> None:
    """Keep the complete story intact when the user selects zero models.

    A no-model set still needs editorial and lifestyle functions.  Replacing
    those roles is materially different from deleting/defering them.
    """

    if model_count != 0:
        return
    for slot in slots:
        slot_id = str(slot.get("id", ""))
        slot_type = str(slot.get("type", "")).strip().lower()
        if slot_type in MODEL_SLOT_TYPES or slot_id == "model-hero":
            if slot_id == "model-hero":
                slot["id"] = "non-model-editorial"
            slot.update({
                "type": "detail-slice",
                "role": "non-model editorial product scene",
                "question": "不使用模特时，商品如何呈现品牌氛围与搭配想象？",
                "template": "detail-slice.txt",
                "reference_roles": slot.get("reference_roles") or ["front"],
                "presentation_mode": "flat_lay",
                "visual_family": "editorial_scene",
                "background_treatment": "非白底的品牌色平铺、静物空间或轻悬浮编辑场景；不得模拟隐形人体",
                "model_group_id": "",
                "status": "planned",
                "billable": True,
            })
        elif slot_id == "lifestyle-use" or slot.get("visual_family") == "lifestyle_scene":
            slot.update({
                "role": "non-model styled lifestyle scene",
                "question": "没有模特时，如何通过真实静物与空间关系说明使用场景？",
                "presentation_mode": "flat_lay",
                "visual_family": "editorial_scene",
                "background_treatment": "与整套品牌色一致的非模特平铺或空间静物场景，不使用纯白无缝棚拍",
            })


def _direction_for_slot(slot: dict[str, Any], directions: list[dict[str, Any]]) -> str:
    selected = [item for item in directions if item.get("selected")]
    if not selected:
        return ""
    family = _canonical(slot.get("visual_family", ""))
    module = _canonical(slot.get("module", ""))
    for direction in selected:
        haystack = _canonical(" ".join(str(direction.get(key, "")) for key in ("id", "name", "modules", "scene", "why")))
        if (family and any(token in haystack for token in family.split())) or (module and module in haystack):
            return str(direction.get("id", ""))
    return str(selected[0].get("id", ""))


def _enrich_screen_fields(slots: list[dict[str, Any]], approved_facts: list[dict[str, Any]], directions: list[dict[str, Any]]) -> None:
    module_by_type = {
        "product-main": "Hero", "model-master": "Hero", "lifestyle": "Multi-Scene",
        "macro-detail": "Detail Close-Up", "selling-point": "Structure", "detail-slice": "Detail Grid",
    }
    for slot in slots:
        unit_id = str(slot.get("work_unit_id", "")).strip()
        applicable_facts = [
            item for item in approved_facts
            if not unit_id
            or str(item.get("work_unit_id", item.get("sale_scope", item.get("product_scope", item.get("component", "shared"))))).strip().lower()
            in {unit_id, "shared", "both", "all"}
        ]
        fact_keys = [item.get("key") for item in applicable_facts if item.get("key")]
        slot.setdefault("module", module_by_type.get(str(slot.get("type", "")).lower(), "Detail Grid"))
        slot.setdefault("headline", str(slot.get("role", "")).strip())
        slot.setdefault("subcopy", "")
        chosen_direction = _direction_for_slot(slot, directions)
        slot.setdefault("visual_direction", [chosen_direction] if chosen_direction else [])
        slot.setdefault("palette_id", chosen_direction or "approved-brand-palette")
        slot.setdefault("presentation_mode", "direct")
        slot.setdefault("visual_family", "evidence_layout")
        slot.setdefault("background_treatment", "品牌中性色的设计化信息背景")
        slot.setdefault("render_layer", "final_module_image")
        slot.setdefault("text_rendering", "ai_embedded_one_pass")
        slot.setdefault("layout_role", "final_module_for_long_page")
        slot.setdefault("facts_used", fact_keys)
        risk = slot.get("risk_notes", slot.get("risk", ""))
        slot["risk_notes"] = risk if isinstance(risk, list) else ([risk] if risk else [])


def _validate_complete_set_visual_contract(slots: list[dict[str, Any]], errors: list[str]) -> None:
    """Prevent a product evidence pack from being labeled a complete PDP set."""

    units: dict[str, list[dict[str, Any]]] = {}
    for slot in slots:
        unit = str(slot.get("work_unit_id", "item")) or "item"
        units.setdefault(unit, []).append(slot)
    for unit, unit_slots in units.items():
        if not 6 <= len(unit_slots) <= 10:
            continue
        families = {str(slot.get("visual_family", "")).strip() for slot in unit_slots}
        missing_fields = [
            str(slot.get("id", "slot")) for slot in unit_slots
            if not all(slot.get(field) for field in ("presentation_mode", "visual_family", "background_treatment", "palette_id"))
        ]
        if missing_fields:
            errors.append(f"complete detail set {unit} has slots missing per-screen visual fields: " + ", ".join(missing_fields))
        if len(families) < 4:
            errors.append(f"complete detail set {unit} requires at least four visual families; found {len(families)}")
        truth_count = sum(1 for slot in unit_slots if slot.get("visual_family") == "product_truth_clean")
        if truth_count != 1:
            errors.append(f"complete detail set {unit} requires exactly one product_truth_clean screen; found {truth_count}")
        if not families.intersection(COMPLETE_SET_DESIGN_FAMILIES):
            errors.append(f"complete detail set {unit} requires a designed selling-point or information screen")
        if not families.intersection(COMPLETE_SET_SCENE_FAMILIES):
            errors.append(f"complete detail set {unit} requires an editorial, lifestyle, or brand-close screen")
        all_white = all(
            slot.get("presentation_mode") in {"product_only", "direct"}
            and any(token in _canonical(slot.get("background_treatment", "")) for token in ("white", "白", "seamless"))
            for slot in unit_slots
        )
        if all_white:
            errors.append(f"complete detail set {unit} cannot be an all-white product evidence pack")


def _scope_separate_pairing_slots(
    base_slots: list[dict[str, Any]],
    relationship: dict[str, Any],
) -> list[dict[str, Any]]:
    """Materialize independent top and bottom slots before reference binding."""

    scoped: list[dict[str, Any]] = []
    for unit in relationship["work_units"]:
        unit_id = str(unit["id"])
        unit_slot_ids: list[str] = []
        for base in base_slots:
            slot = copy.deepcopy(base)
            base_id = str(slot.get("id", "slot"))
            slot["base_slot_id"] = base_id
            slot["id"] = f"{unit_id}-{base_id}"
            slot["work_unit_id"] = unit_id
            slot["sale_scope"] = unit_id
            scoped_roles: list[str] = []
            for role in _slot_reference_roles(slot):
                canonical = _canonical(role)
                if canonical in {"front", "garment front", "product front", "top front", "bottom front"}:
                    replacement = f"{unit_id}_front"
                elif canonical in {"back", "garment back", "product back", "rear", "top back", "bottom back"}:
                    replacement = f"{unit_id}_back"
                elif canonical in {"material", "top material", "bottom material"}:
                    replacement = f"{unit_id}_material"
                elif canonical in {"construction", "top construction", "bottom construction"}:
                    replacement = f"{unit_id}_construction"
                else:
                    replacement = role
                if replacement not in scoped_roles:
                    scoped_roles.append(replacement)
            slot["reference_roles"] = scoped_roles
            unit_slot_ids.append(slot["id"])
            scoped.append(slot)
        unit["slot_ids"] = unit_slot_ids
    return scoped


def build_plan(job: dict[str, Any], *, base_dir: Path) -> tuple[dict[str, Any], int]:
    errors: list[str] = []
    warnings: list[str] = []
    sku = normalize_sku(job)
    if not sku["id"]:
        errors.append("sku.id is required")
    if not sku["name"]:
        warnings.append("sku.name is missing; prompts may use the SKU id only")

    product_refs = normalize_references(job, kind="product")
    errors.extend(_reference_errors(product_refs, "product", base_dir))
    relationship = _normalize_product_relationship(job, product_refs)
    if relationship["mode"] not in {"single_item", "separate_pairing", "true_set"}:
        errors.append("product relationship is unconfirmed; " + relationship["confirmation_question"])
    elif relationship["paired_folder_detected_from_roles"] and not relationship["confirmed_by_user"]:
        errors.append("paired top/bottom folder requires confirmed_by_user=true; " + relationship["confirmation_question"])
    elif relationship["paired_folder_detected_from_roles"] and relationship["mode"] == "single_item":
        errors.append("paired top/bottom folder cannot be treated as one single item; " + relationship["confirmation_question"])
    presentation = _normalize_presentation(job)
    if not presentation["valid"]:
        errors.append("presentation.mode must be direct, product_only, ghost_mannequin, floating_product_poster, flat_lay, or model")
    facts = normalize_fact_items(job)
    copy_rows = _copy_rows(job)
    approved_facts = _validate_facts_and_copy(facts, copy_rows, errors, warnings)
    if relationship["mode"] == "separate_pairing":
        for item in approved_facts:
            scope = str(item.get("work_unit_id", item.get("sale_scope", item.get("product_scope", item.get("component", ""))))).strip().lower()
            if scope not in {"top", "bottom", "shared", "both", "all"}:
                errors.append(
                    f"separate_pairing approved fact {item.get('key', 'fact')} requires "
                    "work_unit_id/sale_scope=top, bottom, or shared"
                )
    if not facts:
        warnings.append("no product fact table supplied; all unlisted details remain unknown")
    model = normalize_model(job)
    deliverables = normalize_deliverables(job)
    model_required = deliverables["model_count"] > 0
    model_packs = model.get("packs", []) if isinstance(model.get("packs"), list) else []
    model_ids = [str(pack.get("id", "")).strip() for pack in model_packs]
    seen_model_ids: set[str] = set()
    for model_id in model_ids:
        if model_id and model_id in seen_model_ids:
            errors.append(f"duplicate model pack id: {model_id}")
        seen_model_ids.add(model_id)
    if model_required and len(model_packs) < deliverables["model_count"]:
        errors.append(
            f"model_count={deliverables['model_count']} requires {deliverables['model_count']} independent model packs; "
            f"only {len(model_packs)} supplied"
        )
    for index in range(min(max(0, deliverables["model_count"]), len(model_packs))):
        pack = model_packs[index]
        label = f"model pack {index + 1}"
        errors.extend(_reference_errors(pack.get("reference_images", []), label, base_dir, required=True))
        if not pack.get("id"):
            errors.append(f"{label}.id is required when model_count is greater than zero")
        if not pack.get("approved"):
            errors.append(f"{label} must be approved before paid generation")
    if deliverables["model_count"] not in (0, 1, 2):
        errors.append("deliverables.model_count must be 0, 1, or 2")

    directions = normalize_directions(job)
    if not directions:
        errors.append("at least one visual direction is required")
    elif len(directions) > 5:
        errors.append("at most five visual directions may be proposed")
    _validate_direction_fields(directions, errors)
    if directions and not any(item["selected"] for item in directions):
        warnings.append("no visual direction is selected; the first approval gate must select one")

    count = deliverables["detail_slices"]
    if count == -1:
        errors.append("deliverables.detail_slices must be an integer")
    elif count < 6 or count > 10:
        errors.append("deliverables.detail_slices must be between 6 and 10")
    requested_count = max(0, count if count != -1 else 8)
    if deliverables["include_size"]:
        size_module, size_warnings = _build_size_module(
            size_source(job, base_dir=base_dir),
            base_dir=base_dir,
            job=job,
        )
        warnings.extend(size_warnings)
    else:
        size_module = {
            "mode": "omitted",
            "type": "omitted",
            "source": None,
            "source_status": "not_requested",
            "instruction": "不生成数值尺码模块；使用一个有证据的版型/场景问题替代。",
        }
    custom_raw = deliverables.get("slots", [])
    custom_slots = custom_raw if isinstance(custom_raw, list) else []
    expanded_views = _expand_requested_views(deliverables.get("requested_views", []), job, facts)
    slots = _slots(
        requested_count,
        size_module,
        custom=custom_slots or None,
        requested_views=expanded_views,
    )
    slots = _replace_omitted_size_slot(
        slots,
        count=requested_count,
        include_size=deliverables["include_size"],
    )
    _replace_no_model_slots(slots, deliverables["model_count"])
    _validate_slot_completeness(
        slots,
        count=requested_count,
        custom=bool(custom_slots),
        errors=errors,
    )
    if not custom_slots and len(slots) != requested_count:
        errors.append(f"requested/default slots contain {len(slots)} entries but detail_slices={requested_count}")
    if relationship["mode"] == "separate_pairing":
        slots = _scope_separate_pairing_slots(slots, relationship)
    else:
        _refine_slot_roles(slots, job=job, facts=facts, sale_mode=relationship["mode"])
    _enrich_screen_fields(slots, approved_facts, directions)
    _validate_complete_set_visual_contract(slots, errors)
    _bind_slot_references(
        slots,
        product_refs,
        model,
        deliverables["model_count"],
        errors=errors,
        warnings=warnings,
    )
    extra_outputs = _model_extra_outputs(
        model_packs if deliverables["model_count"] == 2 else [],
        product_refs,
        job=job,
        facts=facts,
        sale_mode=relationship["mode"],
    )
    for extra in extra_outputs:
        _enrich_screen_fields([extra], approved_facts, directions)
        if extra.get("status") == "NEEDS_REFERENCE":
            errors.append(f"extra output {extra['id']} NEEDS_REFERENCE: {extra['blocked_reason']}")

    additional_variants_raw = deliverables.get("additional_model_variant_calls", 0)
    try:
        additional_variants = int(additional_variants_raw or 0)
    except (TypeError, ValueError):
        additional_variants = -1
    if additional_variants < 0:
        errors.append("deliverables.additional_model_variant_calls must be a non-negative integer")
        additional_variants = 0
    billable_slots = [
        slot for slot in slots
        if slot.get("billable", True)
        and str(slot.get("status", "planned")).lower().replace("-", "_") not in {"blocked", "needs_reference", "deferred", "omitted", "rejected"}
    ]
    billable_extras = [
        output for output in extra_outputs
        if output.get("billable", True)
        and str(output.get("status", "planned")).lower().replace("-", "_") not in {"blocked", "needs_reference", "deferred", "omitted", "rejected"}
    ]
    work_unit_ids = [unit["id"] for unit in relationship["work_units"]]
    work_unit_multiplier = len(work_unit_ids)
    scoped_billable_slots = [item.get("id") for item in billable_slots]
    scoped_billable_slots.extend(
        f"{unit_id}:{item.get('id')}"
        for unit_id in work_unit_ids
        for item in billable_extras
    )
    planned_base_outputs = len(billable_slots) + len(billable_extras) * work_unit_multiplier + additional_variants
    text_correction_allowance = 1
    planned_max_with_allowance = planned_base_outputs + text_correction_allowance
    estimate = {
        # The eight (or six-to-ten) slots already contain both default heroes;
        # only an additional model identity master is extra for model_count=2.
        "planned_base_outputs": planned_base_outputs,
        "model_masters": deliverables["model_count"] * work_unit_multiplier,
        "product_hero": sum(1 for slot in slots if slot.get("base_slot_id", slot.get("id")) == "product-hero"),
        "detail_slices": len(slots),
        "detail_slices_per_work_unit": requested_count,
        "billable_slots": scoped_billable_slots,
        "work_unit_multiplier": work_unit_multiplier,
        "additional_model_variant_calls": additional_variants,
        "text_correction_allowance": text_correction_allowance,
        "planned_max_with_allowance": planned_max_with_allowance,
        # Backwards-compatible alias; this is a maximum estimate, not a
        # promise that the text correction allowance will be spent.
        "planned_total": planned_max_with_allowance,
        "sample_package": 3,
        "sample_package_is_subset": True,
        "sample_package_roles": ["selected truth/master", "designed selling-point or information", "editorial/lifestyle or no-model scene"],
        "note": "estimate only; sample_package=3 is a representative subset of planned_base_outputs; no provider/API call was made; failed or indeterminate calls are never silently retried",
    }

    gates = [
        {
            "id": "facts-blueprint",
            "name": "事实与蓝图审批闸门",
            "status": "pending",
            "requires": ["product truth", "reference-role map", "selected visual direction", "detail slices", "copy", "estimated paid calls"],
            "blocks": "all paid image calls",
        },
        {
            "id": "sample-package",
            "name": "样片包审批闸门",
            "status": "pending",
            "requires": ["approved selected main-visual module", "one construction/macro final module", "one editorial/lifestyle or no-model final module", "assembly-only sample-page render", "QA verdicts", "actual call count", "all remaining modules and independent model-group masters"],
            "blocks": "remaining paid image calls",
        },
    ]
    plan = {
        "schema_version": "1.2",
        "workflow": "generate-clothing-detail-set",
        "mode": "plan-only",
        "sku": sku,
        "product_reference_images": product_refs,
        "model": {**model, "reference_images": model["reference_images"]},
        "models": model_packs,
        "extra_outputs": extra_outputs,
        "product_relationship": relationship,
        "presentation": presentation,
        "facts": {
            "items": facts,
            "approved_items": approved_facts,
            "unknown_items": [item for item in facts if item not in approved_facts],
            "visible_facts": [item for item in facts if item.get("origin") == "visible"],
            "user_provided_facts": [item for item in facts if item.get("origin") == "user_provided"],
            "unconfirmed_facts": [item for item in facts if item.get("origin") == "unconfirmed"],
        },
        "copy_ledger": copy_rows,
        "visual_directions": directions,
        "selected_direction_ids": [item["id"] for item in directions if item["selected"]],
        "visual_contract": {
            "per_screen_presentation": True,
            "product_truth_clean_per_work_unit": 1,
            "minimum_visual_families": 4,
            "requires_designed_information_or_selling_point": True,
            "requires_editorial_lifestyle_or_brand_close": True,
            "all_white_product_only_classification": "product_evidence_pack_not_complete_detail_set",
        },
        "page_delivery_contract": {
            "target": "mobile_ecommerce_long_page",
            "logical_width": 750,
            "requires_page_blueprint": True,
            "requires_long_page_assembly": True,
            "ai_renders_module_text_and_annotations": True,
            "local_compositor_adds_text": False,
            "individual_slot_png_is_final_page": False,
            "scripts": {
                "blueprint": "scripts/build_page_blueprint.py",
                "compositor": "scripts/compose_detail_page.py",
            },
        },
        "deliverables": {
            **deliverables,
            "detail_slices": requested_count,
            "total_slots": len(slots),
            "slots": slots,
        },
        "size_module": size_module,
        "paid_calls_estimate": estimate,
        "approval_gates": gates,
        "validation": {"ok": not errors, "errors": errors, "warnings": warnings},
        "status": "ready_for_approval" if not errors else "blocked",
    }
    return plan, 0 if not errors else 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", nargs="?", help="job JSON path")
    parser.add_argument("--job", dest="job_flag", help="job JSON path (alias)")
    parser.add_argument("--out", "-o", help="write plan JSON to this path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source = args.job_flag or args.job
    if not source:
        print("build_plan.py requires a job JSON path", file=sys.stderr)
        return 2
    try:
        source_path = Path(source).expanduser().resolve()
        raw = load_json(source_path)
        if not isinstance(raw, dict):
            raise ValidationError("job JSON must be an object")
        plan, code = build_plan(raw, base_dir=source_path.parent)
        dump_json(plan, args.out)
        return code
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
