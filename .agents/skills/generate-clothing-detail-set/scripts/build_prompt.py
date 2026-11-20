#!/usr/bin/env python3
"""Render a GPT Image 2 clothing prompt from an approved local plan.

The command creates text only.  It does not call GPT Image 2, upload a
reference, inspect a URL, or read an API key.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from common import (
    APPROVED_FACT_STATUSES,
    ValidationError,
    clean_text,
    dump_json,
    first,
    load_json,
    normalize_fact_items,
    normalize_sku,
    validate_local_image,
)


TYPE_TEMPLATE = {
    "product-main": "product-main.txt",
    "product_hero": "product-main.txt",
    "product-main-image": "product-main.txt",
    "model-master": "model-master.txt",
    "model": "model-master.txt",
    "lifestyle": "lifestyle.txt",
    "macro-detail": "macro-detail.txt",
    "macro": "macro-detail.txt",
    "selling-point": "selling-point.txt",
    "detail-slice": "detail-slice.txt",
    "detail": "detail-slice.txt",
}
VOLATILE_TERMS = (
    "price", "discount", "stock", "availability", "review", "rating", "performance",
    "价格", "折扣", "库存", "缺货", "有货", "现货", "售罄", "评价", "评分", "销量",
    "功效", "性能", "限时", "仅剩", "马上抢", "抢购", "促销",
)
BLOCKED_SLOT_STATUSES = {"blocked", "needs_reference", "needs-reference", "deferred", "rejected"}
MODEL_SLOT_TYPES = {"model-master", "model", "model-hero"}


def _template_path(raw: str | None, slot_type: str, script_dir: Path) -> Path:
    if raw:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = script_dir / candidate
    else:
        name = TYPE_TEMPLATE.get(slot_type.lower(), "detail-slice.txt")
        candidate = script_dir / "templates" / name
    if not candidate.is_file():
        raise ValidationError(f"template file not found: {candidate}")
    return candidate


def _as_lines(values: Iterable[Any]) -> list[str]:
    lines: list[str] = []
    for value in values:
        if isinstance(value, dict):
            key = clean_text(first(value, "key", "name", "label", default=""))
            item_value = first(value, "value", "text", "description", default="")
            lines.append(f"- {key}: {item_value}" if key else f"- {item_value}")
        else:
            text = clean_text(value)
            if text:
                lines.append(f"- {text}")
    return lines


def _canonical(value: Any) -> str:
    return " ".join("".join(char if char.isalnum() else " " for char in str(value).lower()).split())


def _role_matches(reference_role: Any, required_role: Any) -> bool:
    reference = _canonical(reference_role)
    required = _canonical(required_role)
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
    for component in ("top", "bottom"):
        for family in ("material", "construction"):
            if required == f"{component} {family}":
                return reference.startswith(component + " ") and (
                    family in reference
                    or (family == "material" and any(token in reference for token in ("fabric", "texture", "surface")))
                    or (family == "construction" and any(token in reference for token in ("pocket", "zipper", "hardware", "seam", "hem", "waistband", "cuff")))
                )
    if required in aliases:
        if reference in aliases[required]:
            return True
        return required in {"material", "construction"} and any(token in reference for token in aliases[required])
    return reference == required


def _slot_product_references(plan: dict[str, Any], slot: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve semantic slot roles to actual local product-reference paths."""

    product_refs = [item for item in plan.get("product_reference_images", []) if isinstance(item, dict)]
    existing = [item for item in slot.get("reference_paths", []) if isinstance(item, dict)]
    candidates = existing or product_refs
    roles = slot.get("reference_roles", [])
    if not isinstance(roles, list):
        roles = [roles] if roles else []
    matched: list[dict[str, Any]] = []
    for role in roles:
        role_matches = [item for item in candidates if _role_matches(first(item, "role", "reference_role", default=""), role)]
        for item in role_matches:
            if item not in matched:
                matched.append(item)
        if not role_matches:
            raise ValidationError(f"slot {first(slot, 'id', 'slot_id', default='slot')} has no local reference for role {role}")
    if not roles and existing:
        matched = existing
    return matched


def _model_references(plan: dict[str, Any], slot: dict[str, Any]) -> list[dict[str, Any]]:
    group_id = clean_text(first(slot, "model_group_id", default=""))
    models = plan.get("models") if isinstance(plan.get("models"), list) else []
    pack = next((item for item in models if isinstance(item, dict) and clean_text(item.get("id")) == group_id), None)
    if pack is None:
        raise ValidationError(f"model slot requires an exact model_group_id present in plan.models: {group_id or '[missing]'}")
    refs = pack.get("reference_images", [])
    if not isinstance(refs, list) or not refs:
        raise ValidationError(f"model group {group_id} has no identity references")
    return [item for item in refs if isinstance(item, dict)]


def _reference_lines(plan: dict[str, Any], slot: dict[str, Any], *, base_dir: Path) -> list[str]:
    references: list[tuple[str, dict[str, Any]]] = []
    for item in _slot_product_references(plan, slot):
        references.append(("product", item))
    slot_type = clean_text(first(slot, "type", "slot_type", default="")).lower()
    if slot_type in MODEL_SLOT_TYPES or first(slot, "id", "slot_id", default="") == "model-hero":
        for item in _model_references(plan, slot):
            references.append(("model identity", item))
    lines: list[str] = []
    for source_label, item in references:
        role = clean_text(first(item, "role", "reference_role", default="reference image"))
        path = clean_text(first(item, "path", "file", "image", "src", default=""))
        if not path or "://" in path:
            raise ValidationError(f"{source_label} reference role {role} has no local path")
        valid, reason = validate_local_image(path, base_dir=base_dir)
        if not valid:
            raise ValidationError(f"{source_label} reference role {role} is not a valid local image: {path} ({reason})")
        lines.append(f"- {source_label} / {role}: {path}")
    return lines or ["- No product image role is required for this slot; do not invent one."]


def _approved_fact_lines(plan: dict[str, Any], slot: dict[str, Any] | None = None) -> list[str]:
    items = _approved_fact_items(plan, slot)
    lines = []
    lines.extend(_as_lines(items))
    return lines


def _sku_lines(plan: dict[str, Any]) -> list[str]:
    """Return identity context separately from the required fact ledger."""

    sku = plan.get("sku") if isinstance(plan.get("sku"), dict) else {}
    lines = []
    if clean_text(sku.get("id")):
        lines.append(f"- SKU: {sku['id']}")
    if clean_text(sku.get("name")):
        lines.append(f"- 商品名称: {sku['name']}")
    if clean_text(sku.get("variant")):
        lines.append(f"- 已确认变体: {sku['variant']}")
    return lines


def _approved_fact_items(plan: dict[str, Any], slot: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    facts = plan.get("facts") if isinstance(plan.get("facts"), dict) else {}
    raw = facts.get("items", facts.get("approved_items", [])) if isinstance(facts, dict) else (facts if isinstance(facts, list) else [])
    unit_id = clean_text(first(slot or {}, "work_unit_id", "sale_unit", default="")).lower()
    return [
        item for item in raw
        if isinstance(item, dict)
        and clean_text(item.get("status", "")).lower() in APPROVED_FACT_STATUSES
        and item.get("value", item.get("fact", item.get("text", ""))) not in (None, "", [], {})
        and item.get("evidence", item.get("source", "")) not in (None, "", [], {})
        and (
            not unit_id
            or clean_text(first(item, "work_unit_id", "sale_scope", "product_scope", "component", default="shared")).lower()
            in {unit_id, "shared", "both", "all"}
        )
        and not (_canonical(item.get("key", "")) in {_canonical(term) for term in VOLATILE_TERMS} or any(_canonical(term) in _canonical(item.get("key", "")) for term in VOLATILE_TERMS) or any(_canonical(term) in _canonical(item.get("value", item.get("fact", item.get("text", "")))) for term in VOLATILE_TERMS))
    ]


def _copy_lines(slot: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    inline = first(slot, "approved_chinese_copy", "chinese_copy", "copy", "copy_lines", default=None)
    ledger = plan.get("copy_ledger", plan.get("copy", []))
    if isinstance(ledger, dict):
        ledger = ledger.get("rows", ledger.get("items", [ledger]))
    rows = [row for row in (ledger if isinstance(ledger, list) else []) if isinstance(row, dict)]
    ids = first(slot, "copy_ids", "copy_id", default=[])
    if not isinstance(ids, list):
        ids = [ids] if ids else []
    if inline not in (None, "", [], {}):
        raise ValidationError("inline copy is not allowed; reference an approved copy ledger row")
    selected = [row for row in rows if (not ids and clean_text(row.get("slot_id", "")) == clean_text(first(slot, "id", "slot_id", default=""))) or clean_text(row.get("id", "")) in {clean_text(value) for value in ids}]
    if ids and len(selected) != len(ids):
        missing = [str(value) for value in ids if not any(clean_text(row.get("id")) == clean_text(value) for row in rows)]
        raise ValidationError("copy ledger rows not found: " + ", ".join(missing))
    output: list[str] = []
    for row in selected:
        status = clean_text(row.get("status", "")).lower()
        if status not in APPROVED_FACT_STATUSES or not row.get("evidence") or _canonical(row.get("allowed_surface", "")) not in {"image text", "image_text"}:
            raise ValidationError(f"copy row {row.get('id', '[missing]')} is not approved for image_text")
        text = clean_text(row.get("text", row.get("copy", row.get("value", ""))))
        if not text or any(_canonical(term) in _canonical(text) for term in VOLATILE_TERMS):
            raise ValidationError(f"copy row {row.get('id', '[missing]')} is empty or contains volatile claims")
        output.append(f"- 逐字保留：{text}")
    return output


def _creative_lines(slot: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    values: list[Any] = []
    raw = first(slot, "creative_variables", "creative", default=None)
    if isinstance(raw, dict):
        values.extend(f"{key}: {value}" for key, value in raw.items() if value not in (None, ""))
    elif raw:
        values.extend(raw if isinstance(raw, list) else [raw])
    for direction in plan.get("visual_directions", []):
        if isinstance(direction, dict) and direction.get("selected"):
            for key in ("name", "scene", "lighting", "palette"):
                if direction.get(key):
                    values.append(f"{key}: {direction[key]}")
    for key in ("scene", "lighting", "palette", "composition", "pose", "background", "mood"):
        if slot.get(key):
            values.append(f"{key}: {slot[key]}")
    for key in ("visual_family", "background_treatment", "palette_id"):
        if slot.get(key):
            values.append(f"{key}: {slot[key]}")
    return _as_lines(values) or ["- 仅使用模板默认的克制摄影变量；不得改动固定商品事实。"]


def _text_layer_lines(slot: dict[str, Any], plan: dict[str, Any]) -> tuple[str, list[str]]:
    copy_lines = _copy_lines(slot, plan)
    lines = [
        "- 在本次同一次生图中完成商品画面、中文标题与正文、标签、引线、放大框和必要的信息排版。",
        "- 所有文字必须逐字使用下方批准文案，不得改写、补写或虚构营销承诺。",
    ]
    lines.extend(copy_lines or ["- 本模块没有批准的中文文案；保持无文字，不要自行添加文字。"])
    return "ai_embedded_one_pass", lines


def _size_table_lines(plan: dict[str, Any], slot: dict[str, Any], *, base_dir: Path) -> list[str]:
    slot_id = clean_text(first(slot, "base_slot_id", "id", "slot_id", default=""))
    if slot_id != "size-module":
        return []
    size = plan.get("size_module") if isinstance(plan.get("size_module"), dict) else {}
    if size.get("mode") != "numeric":
        return ["- 当前没有已核验尺码数字；不得生成尺码表或任何尺码数值。"]
    raw_source = clean_text(size.get("source", ""))
    source = Path(raw_source).expanduser()
    if not source.is_absolute():
        source = base_dir / source
    if source.suffix.lower() != ".json" or not source.is_file():
        raise ValidationError("numeric size module requires a readable JSON source before prompting")
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"numeric size source is invalid JSON: {source}") from exc
    rows = raw.get("rows", raw) if isinstance(raw, dict) else raw
    if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
        raise ValidationError("numeric size JSON must contain a non-empty list of row objects")
    serialized = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return [
        f"- 已核验尺码数据（逐字逐数渲染）：{serialized}",
        "- 可以美化表格版式，但列名、行名、单位和每个数字都不得改变、补全或猜测。",
    ]


def _presentation_constraint_lines(mode: str) -> list[str]:
    if mode == "ghost_mannequin":
        return [
            "- 透明人台：去除真人脸、皮肤、手脚和人体轮廓，但保留衣服自然立体空腔；不出现衣架、挂杆或虚构内里。",
            "- 默认是实体背景商品展示，不得擅自当作透明通道抠图。",
        ]
    if mode == "floating_product_poster":
        return [
            "- 悬浮讲解海报：商品可悬浮在已批准设计背景中；它不是透明人台，不得制造隐形人体空腔。",
            "- 只可使用批准文案与可核验标注，不得增加价格、库存、折扣或未经确认的卖点。",
        ]
    if mode == "flat_lay":
        return ["- 平铺展示：保持自然重力、真实边缘与结构，不使用真人、隐形人台或悬浮人体轮廓。"]
    if mode == "model":
        return ["- 模特展示：只使用已批准身份包；模特参考不提供服装事实，商品参考不提供人物身份。"]
    return ["- 直接商品展示：保持商品优先、结构清楚，不自动增加透明人台、悬浮海报或模特。"]


def _render(template: str, values: dict[str, str]) -> str:
    """Replace ``{{NAME}}`` tokens while preserving all other template text."""

    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip().upper()
        return values.get(key, match.group(0))

    return re.sub(r"\{\{\s*([A-Za-z0-9_ -]+)\s*\}\}", replace, template).strip() + "\n"


def build_prompt(
    plan: dict[str, Any],
    slot: dict[str, Any],
    template_text: str,
    *,
    base_dir: Path,
    allow_empty_facts: bool = False,
) -> str:
    slot_status = clean_text(first(slot, "status", "state", default="planned")).lower().replace("-", "_")
    if slot_status in BLOCKED_SLOT_STATUSES:
        raise ValidationError(f"slot {first(slot, 'id', 'slot_id', default='slot')} is {slot_status}; no prompt may be generated")
    validation = plan.get("validation") if isinstance(plan.get("validation"), dict) else {}
    if plan.get("status") == "blocked" or validation.get("ok") is False:
        raise ValidationError("plan is blocked; resolve reference/fact/approval errors before prompting")
    relationship = plan.get("product_relationship") if isinstance(plan.get("product_relationship"), dict) else {}
    sale_mode = clean_text(relationship.get("mode", "single_item")) or "single_item"
    if sale_mode == "unconfirmed" or relationship.get("confirmed_by_user") is False:
        raise ValidationError("sale relationship is unconfirmed; ask whether the top and bottom are separate_pairing or true_set")
    work_unit_id = clean_text(first(slot, "work_unit_id", "sale_unit", default=""))
    if sale_mode == "separate_pairing" and work_unit_id not in {"top", "bottom"}:
        raise ValidationError("separate_pairing prompt requires slot.work_unit_id=top or bottom; never mix two sellable units")
    presentation = plan.get("presentation") if isinstance(plan.get("presentation"), dict) else {}
    presentation_mode = clean_text(first(slot, "presentation_mode", "presentation", default=""))
    if not presentation_mode:
        presentation_mode = clean_text(presentation.get("mode", "direct")) or "direct"
    approved_items = _approved_fact_items(plan, slot)
    if not approved_items and not allow_empty_facts:
        raise ValidationError("no approved product facts available; do not generate a paid prompt")
    approved = _approved_fact_lines(plan, slot)
    fixed_lines = _sku_lines(plan) + approved
    slot_type = clean_text(first(slot, "type", "slot_type", default="detail-slice")) or "detail-slice"
    text_mode, copy_lines = _text_layer_lines(slot, plan)
    size_lines = _size_table_lines(plan, slot, base_dir=base_dir)
    values = {
        "SLOT_ID": clean_text(first(slot, "id", "slot_id", default="slot")),
        "SLOT_TYPE": slot_type,
        "SLOT_ROLE": clean_text(first(slot, "role", "title", "name", default=slot_type)),
        "SLOT_GOAL": clean_text(first(slot, "goal", "question", "purpose", default="回答一个具体购买问题。")),
        "ASPECT_RATIO": clean_text(first(slot, "aspect_ratio", "aspect", default="4:5")),
        "REFERENCE_ROLES": "\n".join(_reference_lines(plan, slot, base_dir=base_dir)),
        "FIXED_FACTS": "\n".join(fixed_lines or ["- 没有已批准事实；所有未列出的内容必须保持未知。"]),
        "CREATIVE_VARIABLES": "\n".join(_creative_lines(slot, plan)),
        "APPROVED_CHINESE_COPY": "\n".join(copy_lines + size_lines),
        "NEGATIVE_CONSTRAINTS": "\n".join([
            "- 禁止重设计、改色、改面料、改廓形、改长度、改层次、改口袋/拉链/五金/缝线/下摆或比例。",
            "- 禁止生成额外商品、配件、变体、logo、标签、条码、尺码数值、认证、评价、价格、折扣、库存或功效宣称。",
            "- 禁止把模特参考当作服装参考；模特图只提供身份，商品图只提供对应可见商品事实。",
            "- 若参考证据不足，保留空白或停止该视角，不要脑补。",
            "- 中文信息属于最终画面的一部分；完成可读、自然、接近淘宝服装详情页的信息层级，不要输出空白占位框。",
            *_presentation_constraint_lines(presentation_mode),
        ]),
    }
    rendered = _render(template_text, values)
    header = "\n".join([
        "GPT Image 2 clothing detail prompt (prompt only; no API call)",
        f"Slot: {values['SLOT_ID']} / {values['SLOT_TYPE']} / aspect {values['ASPECT_RATIO']}",
        f"Sale mode: {sale_mode}",
        f"Sale unit: {work_unit_id or clean_text((plan.get('sku') or {}).get('id', 'single_item'))}",
        f"Presentation: {presentation_mode}",
        f"Text rendering: {text_mode}",
        "Output role: final ecommerce detail module with embedded Chinese, ready for long-page assembly",
        "",
    ])
    return header + rendered


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", nargs="?", help="approved plan JSON path")
    parser.add_argument("slot", nargs="?", help="slot JSON path")
    parser.add_argument("--plan", dest="plan_flag")
    parser.add_argument("--facts", dest="facts_flag", help="alias for plan/facts JSON")
    parser.add_argument("--slot", dest="slot_flag")
    parser.add_argument("--template")
    parser.add_argument("--out", "-o")
    parser.add_argument("--json", action="store_true", help="emit {slot,prompt} JSON")
    parser.add_argument("--allow-empty-facts", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    plan_path = args.plan_flag or args.facts_flag or args.plan
    slot_path = args.slot_flag or args.slot
    if not plan_path or not slot_path:
        print("build_prompt.py requires a plan/facts JSON path and a slot JSON path", file=sys.stderr)
        return 2
    try:
        plan_raw = load_json(Path(plan_path).expanduser())
        slot_raw = load_json(Path(slot_path).expanduser())
        if not isinstance(plan_raw, dict) or not isinstance(slot_raw, dict):
            raise ValidationError("plan and slot JSON must both be objects")
        if "facts" not in plan_raw:
            plan_raw = {**plan_raw, "facts": {"items": normalize_fact_items(plan_raw)}, "sku": normalize_sku(plan_raw)}
        template = _template_path(args.template, clean_text(first(slot_raw, "type", "slot_type", default="detail-slice")), Path(__file__).resolve().parent)
        prompt = build_prompt(
            plan_raw,
            slot_raw,
            template.read_text(encoding="utf-8"),
            base_dir=Path(plan_path).expanduser().resolve().parent,
            allow_empty_facts=args.allow_empty_facts,
        )
        result: Any = {"slot": first(slot_raw, "id", "slot_id", default="slot"), "prompt": prompt}
        if args.json:
            dump_json(result, args.out)
        elif args.out:
            out = Path(args.out).expanduser()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(prompt, encoding="utf-8")
        else:
            sys.stdout.write(prompt)
        return 0
    except (ValidationError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
