from __future__ import annotations

import json
import base64
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]


class ClothingDetailScriptsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="clothing-detail-scripts-")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_json(self, name: str, value: object) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def touch(self, name: str, content: str = "reference") -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def image(self, name: str, color: tuple[int, int, int] = (200, 200, 200)) -> Path:
        from PIL import Image

        path = self.root / name
        Image.new("RGB", (12, 12), color).save(path)
        return path

    def run_script(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_DIR / script), *args],
            cwd=SCRIPT_DIR,
            text=True,
            capture_output=True,
            check=False,
        )

    def base_job(self) -> dict[str, object]:
        for name in ("garment-front.png", "garment-back.png", "model-front.png", "material.png", "pocket.png"):
            self.image(name)
        self.write_json("size.json", {"rows": [{"size": "M", "chest": 100, "unit": "cm"}]})
        return {
            "sku": {"id": "SKU-001", "name": "轻盈外套", "variant": "深灰"},
            "product_reference_images": [
                {"path": "garment-front.png", "role": "garment front"},
                {"path": "garment-back.png", "role": "garment back"},
                {"path": "material.png", "role": "material"},
                {"path": "pocket.png", "role": "pocket"},
            ],
            "model": {
                "id": "model-001",
                "approved": True,
                "reference_images": [{"path": "model-front.png", "role": "model identity"}],
            },
            "facts": [
                {"key": "category", "value": "短外套", "status": "confirmed", "evidence": "garment-front.png"},
                {"key": "color", "value": "深灰", "status": "approved", "evidence": "garment-front.png"},
            ],
            "visual_directions": [{
                "id": "studio",
                "name": "产品真值棚拍",
                "selected": True,
                "scene": "neutral studio",
                "lighting": "soft frontal",
                "modules": ["product hero", "model master"],
                "product_fit": "clothing-first neutral fit",
                "camera": "50mm straight-on",
                "negative_space": "top and side safe crop",
                "why": "keeps the garment readable",
                "composability": "shares the neutral master with detail slices",
            }],
            "deliverables": {"detail_slices": 8, "model_count": 1},
            "size_source": {"path": "size.json", "status": "confirmed"},
            "copy_ledger": [{
                "id": "copy-1",
                "slot_id": "construction-selling-point",
                "text": "轻盈有型，日常好搭",
                "status": "approved",
                "evidence": "copy-review.md",
                "allowed_surface": "image_text",
            }],
        }

    def valid_manifest(self) -> tuple[dict[str, object], Path, dict[str, object]]:
        job_path = self.write_json("manifest-job.json", self.base_job())
        plan_path = self.root / "manifest-plan.json"
        plan_result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(plan_result.returncode, 0, plan_result.stderr)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        output_paths = [self.image(f"manifest-{slot['id']}.png").name for slot in plan["deliverables"]["slots"]]
        preview = self.image("manifest-preview.png")
        blueprint_path = self.root / "manifest-page-blueprint.json"
        blueprint_result = self.run_script(
            "build_page_blueprint.py", str(plan_path), "--out", str(blueprint_path)
        )
        self.assertEqual(blueprint_result.returncode, 0, blueprint_result.stderr)
        blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
        asset_map_path = self.write_json(
            "manifest-page-assets.json",
            {module["id"]: [output_paths[index]] for index, module in enumerate(blueprint["modules"])},
        )
        composed_page = self.root / "manifest-complete-page.png"
        page_render_manifest = self.root / "manifest-page-render.json"
        compose_result = self.run_script(
            "compose_detail_page.py", str(blueprint_path), "--assets", str(asset_map_path),
            "--out", str(composed_page), "--manifest-out", str(page_render_manifest),
        )
        self.assertEqual(compose_result.returncode, 0, compose_result.stderr)
        master_slot = next(slot for slot in plan["deliverables"]["slots"] if slot["id"] == "product-hero")
        designed_slot = next(slot for slot in plan["deliverables"]["slots"] if slot["id"] == "construction-selling-point")
        editorial_slot = next(slot for slot in plan["deliverables"]["slots"] if slot["id"] == "lifestyle-use")
        slot_output = {slot["id"]: output for slot, output in zip(plan["deliverables"]["slots"], output_paths)}
        manifest: dict[str, object] = {
            "sku": plan["sku"],
            "product_reference_images": plan["product_reference_images"],
            "models": [{"id": "model-001", "approved": True, "reference_images": plan["model"]["reference_images"]}],
            "deliverables": {"model_count": 1},
            "slots": [{**slot, "output": output} for slot, output in zip(plan["deliverables"]["slots"], output_paths)],
            "facts": plan["facts"]["items"],
            "copy_ledger": plan["copy_ledger"],
            "moments": [{"id": f"M{i}", "text": "今天分享一件认真挑选的日常穿搭。"} for i in range(1, 7)],
            "size_module": plan["size_module"],
            "approval_gates": [{"id": "facts-blueprint", "status": "approved"}, {"id": "sample-package", "status": "approved"}],
            "paid_calls_estimate": plan["paid_calls_estimate"],
            "paid_calls": {"actual": 3},
            "gate1_paid_calls": 3,
            "delivery_classification": "complete_mobile_detail_page",
            "page_blueprint": blueprint_path.name,
            "composed_page": composed_page.name,
            "page_render_manifest": page_render_manifest.name,
            "sample_outputs": [
                {"kind": "master", "path": slot_output[master_slot["id"]], "visual_family": master_slot["visual_family"]},
                {"kind": "final-detail", "path": slot_output[designed_slot["id"]], "visual_family": designed_slot["visual_family"]},
                {"kind": "final-detail", "path": slot_output[editorial_slot["id"]], "visual_family": editorial_slot["visual_family"]},
            ],
            "two_slice_preview": {"path": preview.name, "inputs": [slot_output[designed_slot["id"]], slot_output[editorial_slot["id"]]]},
        }
        manifest_path = self.write_json("valid-manifest.json", manifest)
        return manifest, manifest_path, plan

    def test_normal_plan_prompt_and_manifest(self) -> None:
        job = self.write_json("job.json", self.base_job())
        plan_path = self.root / "plan.json"
        result = self.run_script("build_plan.py", "--job", str(job), "--out", str(plan_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["deliverables"]["detail_slices"], 8)
        self.assertEqual(plan["size_module"]["mode"], "numeric")
        estimate = plan["paid_calls_estimate"]
        self.assertEqual(estimate["planned_base_outputs"], 8)
        self.assertEqual(estimate["planned_max_with_allowance"], 9)
        self.assertEqual(estimate["sample_package"], 3)
        self.assertTrue(estimate["sample_package_is_subset"])
        self.assertEqual(plan["approval_gates"][1]["requires"][0], "approved selected main-visual module")

        slot = dict(next(item for item in plan["deliverables"]["slots"] if item["id"] == "construction-selling-point"))
        slot["copy_ids"] = ["copy-1"]
        slot_path = self.write_json("slot.json", slot)
        prompt_path = self.root / "prompt.txt"
        prompt_result = self.run_script(
            "build_prompt.py", "--plan", str(plan_path), "--slot", str(slot_path), "--out", str(prompt_path)
        )
        self.assertEqual(prompt_result.returncode, 0, prompt_result.stderr)
        prompt = prompt_path.read_text(encoding="utf-8")
        self.assertIn("轻盈有型，日常好搭", prompt)
        self.assertIn("禁止重设计", prompt)
        self.assertIn("pocket.png", prompt)
        self.assertIn("Text rendering: ai_embedded_one_pass", prompt)
        self.assertIn("同一次生图中完成商品画面、中文标题与正文", prompt)
        self.assertNotIn("禁止在图中生成文字", prompt)
        self.assertIn("final ecommerce detail module with embedded Chinese", prompt)
        product_slot_path = self.write_json("product-slot.json", plan["deliverables"]["slots"][0])
        product_prompt = self.run_script("build_prompt.py", str(plan_path), str(product_slot_path))
        self.assertEqual(product_prompt.returncode, 0, product_prompt.stderr)
        self.assertIn("garment-front.png", product_prompt.stdout)
        self.assertNotIn("garment-back.png", product_prompt.stdout)
        self.assertIn("APPROVED_CHINESE_COPY", (SCRIPT_DIR / "templates" / "product-main.txt").read_text(encoding="utf-8"))
        self.assertIn("APPROVED_CHINESE_COPY", (SCRIPT_DIR / "templates" / "model-master.txt").read_text(encoding="utf-8"))

        output_paths: list[str] = []
        for planned_slot in plan["deliverables"]["slots"]:
            output = self.image(f"{planned_slot['id']}.png")
            output_paths.append(output.name)
        preview = self.image("two-slice-preview.png", (230, 230, 230))
        manifest = {
            "sku": plan["sku"],
            "product_reference_images": plan["product_reference_images"],
            "models": [{
                "id": "model-001",
                "approved": True,
                "reference_images": plan["model"]["reference_images"],
            }],
            "deliverables": {"model_count": 1},
            "slots": [
                {**item, "output": path}
                for item, path in zip(plan["deliverables"]["slots"], output_paths)
            ],
            "facts": plan["facts"]["items"],
            "copy_ledger": plan["copy_ledger"],
            "moments": [{"id": f"M{i}", "text": "今天分享一件认真挑选的日常穿搭。"} for i in range(1, 7)],
            "size_module": plan["size_module"],
            "approval_gates": [
                {"id": "facts-blueprint", "status": "approved"},
                {"id": "sample-package", "status": "approved"},
            ],
            "paid_calls_estimate": plan["paid_calls_estimate"],
            "paid_calls": {"actual": 3},
            "gate1_paid_calls": 3,
            "sample_outputs": [
                {"kind": "master", "path": output_paths[0]},
                {"kind": "final-detail", "path": output_paths[4]},
                {"kind": "final-detail", "path": output_paths[5]},
            ],
            "two_slice_preview": {"path": preview.name, "inputs": [output_paths[4], output_paths[5]]},
        }
        manifest_path = self.write_json("manifest.json", manifest)
        manifest_result = self.run_script("validate_manifest.py", str(manifest_path))
        self.assertEqual(manifest_result.returncode, 0, manifest_result.stderr)

    def test_failure_is_fail_closed(self) -> None:
        job = {
            "sku": {"id": "SKU-MISSING"},
            "deliverables": {"detail_slices": 5, "model_count": 1},
            "model": {"id": "model-1", "approved": True},
        }
        job_path = self.write_json("bad-job.json", job)
        plan_path = self.root / "bad-plan.json"
        result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(result.returncode, 2)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertFalse(plan["validation"]["ok"])
        self.assertTrue(any("reference" in error for error in plan["validation"]["errors"]))

        empty_plan = self.write_json("empty-plan.json", {
            "status": "ready_for_approval",
            "validation": {"ok": True},
            "sku": {"id": "SKU-MISSING"},
            "facts": {"items": []},
            "product_reference_images": [],
        })
        slot_path = self.write_json("slot.json", {"id": "product-hero", "type": "product-main", "status": "planned"})
        prompt_result = self.run_script("build_prompt.py", str(empty_plan), str(slot_path))
        self.assertEqual(prompt_result.returncode, 2)
        self.assertIn("no approved product facts", prompt_result.stderr)

    def test_missing_size_source_replaces_numeric_module(self) -> None:
        job_data = self.base_job()
        job_data.pop("size_source")
        job_path = self.write_json("no-size-job.json", job_data)
        plan_path = self.root / "no-size-plan.json"
        result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        size = plan["size_module"]
        self.assertEqual(size["mode"], "fit-guidance")
        for field in ("fit", "ease", "measuring_positions", "styling_guidance"):
            self.assertTrue(size[field])
            self.assertNotRegex(size[field], r"(?:\b(?:XS|S|M|L|XL)\b|cm|kg|斤|身高|体重|\d)")
        self.assertIn("no real size source", " ".join(plan["validation"]["warnings"]))

        url_job = self.base_job()
        url_job["size_source"] = {"path": "https://example.invalid/size.json", "status": "approved"}
        url_path = self.write_json("url-size-job.json", url_job)
        url_plan_path = self.root / "url-size-plan.json"
        url_result = self.run_script("build_plan.py", str(url_path), "--out", str(url_plan_path))
        self.assertEqual(url_result.returncode, 0, url_result.stderr)
        url_plan = json.loads(url_plan_path.read_text(encoding="utf-8"))
        self.assertEqual(url_plan["size_module"]["mode"], "fit-guidance")
        self.assertTrue(any("URL" in warning for warning in url_plan["validation"]["warnings"]))

        empty_job = self.base_job()
        self.write_json("size.json", {})
        empty_path = self.write_json("empty-size-job.json", empty_job)
        empty_plan_path = self.root / "empty-size-plan.json"
        empty_result = self.run_script("build_plan.py", str(empty_path), "--out", str(empty_plan_path))
        self.assertEqual(empty_result.returncode, 0, empty_result.stderr)
        self.assertEqual(json.loads(empty_plan_path.read_text(encoding="utf-8"))["size_module"]["mode"], "fit-guidance")

    def test_requested_set_back_needs_top_and_bottom_back(self) -> None:
        job_data = self.base_job()
        job_data["category"] = "套装"
        job_data["product_relationship"] = {"mode": "true_set", "confirmed_by_user": True}
        job_data["product_reference_images"] = [
            {"path": "garment-front.png", "role": "TOP_FRONT"},
            {"path": "material.png", "role": "material"},
            {"path": "pocket.png", "role": "pocket"},
            {"path": "garment-back.png", "role": "BOTTOM_BACK"},
        ]
        job_data["requested_views"] = [{"id": "rear", "view": "back"}]
        job_path = self.write_json("set-back-job.json", job_data)
        plan_path = self.root / "set-back-plan.json"
        result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(result.returncode, 2)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        rear = next(item for item in plan["deliverables"]["slots"] if item["id"] == "front-back-fit")
        self.assertEqual(rear["status"], "NEEDS_REFERENCE")
        self.assertIn("top_back", rear["blocked_reason"])
        self.assertNotIn("front", rear["reference_roles"])

    def test_true_set_builds_one_combined_component_covered_package(self) -> None:
        job_data = self.base_job()
        top_front = self.image("set-top-front.png")
        top_back = self.image("set-top-back.png")
        bottom_front = self.image("set-bottom-front.png")
        bottom_back = self.image("set-bottom-back.png")
        job_data["product_reference_images"] = [
            {"path": top_front.name, "role": "top_front"},
            {"path": top_back.name, "role": "top_back"},
            {"path": bottom_front.name, "role": "bottom_front"},
            {"path": bottom_back.name, "role": "bottom_back"},
            {"path": "material.png", "role": "material"},
            {"path": "pocket.png", "role": "construction"},
        ]
        job_data["product_relationship"] = {"mode": "true_set", "confirmed_by_user": True}
        job_path = self.write_json("true-set-job.json", job_data)
        plan_path = self.root / "true-set-plan.json"
        result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual([unit["id"] for unit in plan["product_relationship"]["work_units"]], ["set"])
        self.assertEqual(plan["product_relationship"]["work_units"][0]["component_detail_coverage"], ["top", "bottom"])
        hero = next(slot for slot in plan["deliverables"]["slots"] if slot["id"] == "product-hero")
        prompt = self.run_script("build_prompt.py", str(plan_path), str(self.write_json("true-set-hero.json", hero)))
        self.assertEqual(prompt.returncode, 0, prompt.stderr)
        self.assertIn("set-top-front.png", prompt.stdout)
        self.assertIn("set-bottom-front.png", prompt.stdout)

    def test_paired_folder_requires_owner_confirmation_and_never_guesses(self) -> None:
        job_data = self.base_job()
        bottom_front = self.image("bottom-front.png")
        job_data["product_reference_images"][0]["role"] = "top_front"
        job_data["product_reference_images"].append({"path": bottom_front.name, "role": "bottom_front"})
        job_path = self.write_json("paired-unconfirmed-job.json", job_data)
        plan_path = self.root / "paired-unconfirmed-plan.json"
        result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(result.returncode, 2)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        relationship = plan["product_relationship"]
        self.assertEqual(relationship["mode"], "unconfirmed")
        self.assertIn("分开售卖", relationship["confirmation_question"])
        self.assertTrue(any("product relationship is unconfirmed" in error for error in plan["validation"]["errors"]))

    def test_separate_pairing_orders_two_full_detail_sets(self) -> None:
        job_data = self.base_job()
        component_refs = []
        for component in ("top", "bottom"):
            for role in ("front", "back", "material", "construction"):
                path = self.image(f"{component}-{role}.png")
                component_refs.append({"path": path.name, "role": f"{component}_{role}"})
        job_data["product_reference_images"] = component_refs
        job_data["product_relationship"] = {"mode": "separate_pairing", "confirmed_by_user": True}
        job_data["requested_views"] = [{"id": "rear", "view": "back"}]
        job_data["facts"] = [
            {"key": "top_category", "value": "外套", "status": "confirmed", "evidence": "top-front.png", "sale_scope": "top"},
            {"key": "bottom_category", "value": "长裤", "status": "confirmed", "evidence": "bottom-front.png", "sale_scope": "bottom"},
        ]
        job_path = self.write_json("separate-pairing-job.json", job_data)
        plan_path = self.root / "separate-pairing-plan.json"
        result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        units = plan["product_relationship"]["work_units"]
        self.assertEqual([unit["id"] for unit in units], ["top", "bottom"])
        self.assertTrue(all(unit["detail_set"] == "full" for unit in units))
        self.assertTrue(all(unit["companion_scope"] == "styling_only" for unit in units))
        self.assertEqual(plan["deliverables"]["total_slots"], 16)
        top_slot = next(slot for slot in plan["deliverables"]["slots"] if slot["id"] == "top-product-hero")
        bottom_slot = next(slot for slot in plan["deliverables"]["slots"] if slot["id"] == "bottom-product-hero")
        top_rear = next(slot for slot in plan["deliverables"]["slots"] if slot["id"] == "top-front-back-fit")
        bottom_rear = next(slot for slot in plan["deliverables"]["slots"] if slot["id"] == "bottom-front-back-fit")
        self.assertEqual(top_rear["reference_roles"], ["top_back"])
        self.assertEqual(bottom_rear["reference_roles"], ["bottom_back"])
        top_prompt = self.run_script("build_prompt.py", str(plan_path), str(self.write_json("top-slot.json", top_slot)))
        bottom_prompt = self.run_script("build_prompt.py", str(plan_path), str(self.write_json("bottom-slot.json", bottom_slot)))
        self.assertEqual(top_prompt.returncode, 0, top_prompt.stderr)
        self.assertEqual(bottom_prompt.returncode, 0, bottom_prompt.stderr)
        self.assertIn("top-front.png", top_prompt.stdout)
        self.assertNotIn("bottom-front.png", top_prompt.stdout)
        self.assertIn("top_category", top_prompt.stdout)
        self.assertNotIn("bottom_category", top_prompt.stdout)
        self.assertIn("bottom-front.png", bottom_prompt.stdout)
        self.assertNotIn("top-front.png", bottom_prompt.stdout)
        self.assertIn("bottom_category", bottom_prompt.stdout)
        self.assertNotIn("top_category", bottom_prompt.stdout)

    def test_light_presentation_facts_buckets_and_five_screen_fields(self) -> None:
        job_data = self.base_job()
        job_data["presentation"] = {"mode": "floating_product_poster"}
        job_data["facts"].append({
            "key": "lining", "value": "待确认", "status": "unconfirmed", "origin": "unconfirmed"
        })
        job_path = self.write_json("light-presentation-job.json", job_data)
        plan_path = self.root / "light-presentation-plan.json"
        result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["presentation"]["mode"], "floating_product_poster")
        self.assertFalse(plan["presentation"]["extra_baseline_required"])
        self.assertTrue(plan["facts"]["visible_facts"])
        self.assertTrue(plan["facts"]["unconfirmed_facts"])
        for slot in plan["deliverables"]["slots"]:
            for field in (
                "headline", "subcopy", "visual_direction", "facts_used", "risk_notes",
                "presentation_mode", "visual_family", "background_treatment", "palette_id",
            ):
                self.assertIn(field, slot)
        hero = next(slot for slot in plan["deliverables"]["slots"] if slot["id"] == "product-hero")
        prompt = self.run_script("build_prompt.py", str(plan_path), str(self.write_json("floating-hero.json", hero)))
        self.assertEqual(prompt.returncode, 0, prompt.stderr)
        self.assertIn("Presentation: product_only", prompt.stdout)
        self.assertNotIn("悬浮讲解海报", prompt.stdout)
        designed = next(slot for slot in plan["deliverables"]["slots"] if slot["id"] == "construction-selling-point")
        designed_prompt = self.run_script(
            "build_prompt.py", str(plan_path), str(self.write_json("designed-slot.json", designed))
        )
        self.assertEqual(designed_prompt.returncode, 0, designed_prompt.stderr)
        self.assertIn("Presentation: floating_product_poster", designed_prompt.stdout)
        self.assertIn("悬浮讲解海报", designed_prompt.stdout)

        flat_job = self.base_job()
        flat_job["presentation"] = {"mode": "flat_lay"}
        flat_path = self.write_json("flat-lay-job.json", flat_job)
        flat_plan = self.root / "flat-lay-plan.json"
        flat_result = self.run_script("build_plan.py", str(flat_path), "--out", str(flat_plan))
        self.assertEqual(flat_result.returncode, 0, flat_result.stderr)

    def test_no_model_replaces_model_roles_with_billable_editorial_scenes(self) -> None:
        job_data = self.base_job()
        job_data.pop("model")
        job_data["deliverables"] = {"detail_slices": 8, "model_count": 0}
        job_path = self.write_json("no-model-job.json", job_data)
        plan_path = self.root / "no-model-plan.json"
        result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        slot_ids = [item["id"] for item in plan["deliverables"]["slots"]]
        self.assertNotIn("model-hero", slot_ids)
        hero = next(item for item in plan["deliverables"]["slots"] if item["id"] == "non-model-editorial")
        self.assertEqual(hero["status"], "planned")
        self.assertEqual(hero["visual_family"], "editorial_scene")
        self.assertEqual(hero["presentation_mode"], "flat_lay")
        self.assertEqual(plan["paid_calls_estimate"]["planned_base_outputs"], 8)
        self.assertIn("non-model-editorial", plan["paid_calls_estimate"]["billable_slots"])
        self.assertGreaterEqual(len({item["visual_family"] for item in plan["deliverables"]["slots"]}), 4)
        slot_path = self.write_json("non-model-editorial-slot.json", hero)
        prompt_result = self.run_script("build_prompt.py", str(plan_path), str(slot_path))
        self.assertEqual(prompt_result.returncode, 0, prompt_result.stderr)
        self.assertIn("Presentation: flat_lay", prompt_result.stdout)
        self.assertIn("非白底", prompt_result.stdout)

    def test_all_white_product_only_pack_cannot_pass_as_complete_detail_set(self) -> None:
        job_data = self.base_job()
        job_data["deliverables"] = {
            "detail_slices": 8,
            "model_count": 1,
            "slots": [
                {
                    "id": f"white-{index}",
                    "type": "product-main",
                    "role": f"white product view {index}",
                    "question": "商品是什么样？",
                    "reference_roles": ["front"],
                    "presentation_mode": "product_only",
                    "visual_family": "product_truth_clean",
                    "background_treatment": "纯白无缝棚拍",
                    "palette_id": "white-only",
                }
                for index in range(1, 9)
            ],
        }
        job_path = self.write_json("all-white-job.json", job_data)
        plan_path = self.root / "all-white-plan.json"
        result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(result.returncode, 2)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        errors = "\n".join(plan["validation"]["errors"])
        self.assertIn("at least four visual families", errors)
        self.assertIn("exactly one product_truth_clean", errors)
        self.assertIn("cannot be an all-white product evidence pack", errors)

    def test_build_page_blueprint_and_assembly_only_long_page(self) -> None:
        job_path = self.write_json("page-job.json", self.base_job())
        plan_path = self.root / "page-plan.json"
        result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        blueprint_path = self.root / "page-blueprint.json"
        blueprint_result = self.run_script(
            "build_page_blueprint.py", str(plan_path), "--out", str(blueprint_path)
        )
        self.assertEqual(blueprint_result.returncode, 0, blueprint_result.stderr)
        blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
        self.assertEqual(blueprint["page"]["logical_width"], 750)
        self.assertEqual(blueprint["page"]["text_rendering"], "ai_embedded_per_module")
        self.assertEqual(blueprint["page"]["image_generation_scope"], "final_module_images")
        self.assertEqual(len(blueprint["modules"]), 8)
        feature = next(item for item in blueprint["modules"] if item["template"] == "feature-callout")
        self.assertTrue(feature["annotations"])
        fit_guide = next(item for item in blueprint["modules"] if item["template"] == "fit-guide")
        self.assertEqual(fit_guide["table"]["columns"], ["size", "chest", "unit"])
        self.assertEqual(fit_guide["table"]["rows"][0], ["M", "100", "cm"])

        asset_map = {module["id"]: ["garment-front.png"] for module in blueprint["modules"]}
        assets_path = self.write_json("page-assets.json", asset_map)
        page_path = self.root / "complete-page.png"
        render_manifest_path = self.root / "page-render.json"
        slices_dir = self.root / "page-slices"
        compose_result = self.run_script(
            "compose_detail_page.py",
            str(blueprint_path),
            "--assets", str(assets_path),
            "--out", str(page_path),
            "--slices-dir", str(slices_dir),
            "--manifest-out", str(render_manifest_path),
        )
        self.assertEqual(compose_result.returncode, 0, compose_result.stderr)
        from PIL import Image
        with Image.open(page_path) as page:
            self.assertEqual(page.width, 750)
            self.assertGreater(page.height, 5000)
        render_manifest = json.loads(render_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(render_manifest["layout_engine"], "deterministic_pillow_vertical_assembly")
        self.assertTrue(render_manifest["assembly_only"])
        self.assertFalse(render_manifest["local_text_overlays"])
        self.assertTrue(all(item["local_text_overlay_count"] == 0 for item in render_manifest["modules"]))
        self.assertEqual(render_manifest["module_count"], 8)
        self.assertEqual(len(list(slices_dir.glob("*.png"))), 8)

        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        size_slot = next(item for item in plan["deliverables"]["slots"] if item["id"] == "size-module")
        size_slot_path = self.write_json("size-slot.json", size_slot)
        size_prompt = self.run_script("build_prompt.py", str(plan_path), str(size_slot_path))
        self.assertEqual(size_prompt.returncode, 0, size_prompt.stderr)
        self.assertIn('已核验尺码数据（逐字逐数渲染）：[{"size":"M","chest":100,"unit":"cm"}]', size_prompt.stdout)

    def test_separate_pairing_page_blueprint_requires_one_work_unit(self) -> None:
        job_data = self.base_job()
        self.image("top-front.png")
        self.image("top-back.png")
        self.image("bottom-front.png")
        self.image("bottom-back.png")
        job_data["product_reference_images"] = [
            {"path": "top-front.png", "role": "top_front"},
            {"path": "top-back.png", "role": "top_back"},
            {"path": "bottom-front.png", "role": "bottom_front"},
            {"path": "bottom-back.png", "role": "bottom_back"},
            {"path": "material.png", "role": "top_material"},
            {"path": "material.png", "role": "bottom_material"},
            {"path": "pocket.png", "role": "top_construction"},
            {"path": "pocket.png", "role": "bottom_construction"},
        ]
        job_data["product_relationship"] = {"mode": "separate_pairing", "confirmed_by_user": True}
        job_data["facts"] = [
            {"key": "top_category", "value": "外套", "status": "confirmed", "evidence": "top-front.png", "sale_scope": "top"},
            {"key": "bottom_category", "value": "长裤", "status": "confirmed", "evidence": "bottom-front.png", "sale_scope": "bottom"},
        ]
        plan_path = self.root / "pair-page-plan.json"
        job_path = self.write_json("pair-page-job.json", job_data)
        self.assertEqual(self.run_script("build_plan.py", str(job_path), "--out", str(plan_path)).returncode, 0)
        missing_unit = self.run_script("build_page_blueprint.py", str(plan_path))
        self.assertEqual(missing_unit.returncode, 2)
        self.assertIn("--work-unit", missing_unit.stderr)
        top_blueprint = self.root / "top-page-blueprint.json"
        top_result = self.run_script(
            "build_page_blueprint.py", str(plan_path), "--work-unit", "top", "--out", str(top_blueprint)
        )
        self.assertEqual(top_result.returncode, 0, top_result.stderr)
        top = json.loads(top_blueprint.read_text(encoding="utf-8"))
        self.assertEqual(top["work_unit_id"], "top")
        self.assertTrue(all(module["id"].startswith("top-") for module in top["modules"]))

    def test_include_size_false_replaces_slot_without_numeric_text(self) -> None:
        job_data = self.base_job()
        job_data["deliverables"] = {"detail_slices": 8, "model_count": 1, "include_size": False}
        job_path = self.write_json("omit-size-job.json", job_data)
        plan_path = self.root / "omit-size-plan.json"
        result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["size_module"]["mode"], "omitted")
        slot_ids = [slot["id"] for slot in plan["deliverables"]["slots"]]
        self.assertNotIn("size-module", slot_ids)
        self.assertIn("fit-evidence", slot_ids)

    def test_direction_duplicates_and_nine_screen_require_explicit_slots(self) -> None:
        duplicate_job = self.base_job()
        duplicate_job["visual_directions"] = duplicate_job["visual_directions"] * 2
        duplicate_path = self.write_json("duplicate-directions-job.json", duplicate_job)
        duplicate_plan_path = self.root / "duplicate-directions-plan.json"
        duplicate_result = self.run_script("build_plan.py", str(duplicate_path), "--out", str(duplicate_plan_path))
        self.assertEqual(duplicate_result.returncode, 2)
        duplicate_plan = json.loads(duplicate_plan_path.read_text(encoding="utf-8"))
        self.assertTrue(any("duplicate visual direction id" in error for error in duplicate_plan["validation"]["errors"]))

        nine_job = self.base_job()
        nine_job["deliverables"] = {"detail_slices": 9, "model_count": 1}
        nine_path = self.write_json("nine-generic-job.json", nine_job)
        nine_plan_path = self.root / "nine-generic-plan.json"
        nine_result = self.run_script("build_plan.py", str(nine_path), "--out", str(nine_plan_path))
        self.assertEqual(nine_result.returncode, 2)
        nine_plan = json.loads(nine_plan_path.read_text(encoding="utf-8"))
        self.assertTrue(any("explicit deliverables.slots" in error for error in nine_plan["validation"]["errors"]))

    def test_manifest_sample_gate_and_permanent_claim_guards(self) -> None:
        import copy

        manifest, manifest_path, _ = self.valid_manifest()
        valid_result = self.run_script("validate_manifest.py", str(manifest_path))
        self.assertEqual(valid_result.returncode, 0, valid_result.stdout)

        def check_bad(name: str, mutate) -> str:
            bad = copy.deepcopy(manifest)
            mutate(bad)
            path = self.write_json(name, bad)
            result = self.run_script("validate_manifest.py", str(path))
            self.assertEqual(result.returncode, 2)
            return result.stdout

        gate1_report = check_bad("bad-gate1.json", lambda value: value.update({"gate1_paid_calls": 2}))
        self.assertIn("gate1_paid_calls", gate1_report)
        sample_report = check_bad("bad-sample-count.json", lambda value: value["sample_outputs"].append(dict(value["sample_outputs"][0])))
        self.assertIn("sample_outputs", sample_report)
        page_claim_report = check_bad("bad-complete-page-claim.json", lambda value: value.pop("page_blueprint"))
        self.assertIn("requires page_blueprint", page_claim_report)
        pending_report = check_bad(
            "bad-gate2-order.json",
            lambda value: (value["paid_calls"].update({"actual": 4}), value["approval_gates"].__setitem__(1, {"id": "sample-package", "status": "pending"})),
        )
        self.assertIn("Gate2", pending_report)
        approved = copy.deepcopy(manifest)
        approved["paid_calls"] = {"actual": 4}
        approved_path = self.write_json("approved-gate2.json", approved)
        approved_result = self.run_script("validate_manifest.py", str(approved_path))
        self.assertEqual(approved_result.returncode, 0, approved_result.stdout)

        copy_report = check_bad(
            "bad-permanent-copy.json",
            lambda value: value["copy_ledger"][0].update({"text": "限时折扣价格"}),
        )
        self.assertIn("volatile copy", copy_report)
        moments_report = check_bad(
            "bad-moments.json",
            lambda value: value["moments"][0].update({"text": "限时折扣，库存有限"}),
        )
        self.assertIn("Moments", moments_report)
        duplicate_report = check_bad(
            "bad-output-duplicate.json",
            lambda value: value["slots"][1].update({"output": value["slots"][0]["output"]}),
        )
        self.assertIn("same output path", duplicate_report)

    def test_strict_approval_bool_volatile_fact_and_real_image_checks(self) -> None:
        fake_reference = self.touch("fake-reference.png", "not an image")
        fake_reference_job = self.base_job()
        fake_reference_job["product_reference_images"] = [
            {"path": fake_reference.name, "role": "garment front"},
            *fake_reference_job["product_reference_images"][1:],
        ]
        fake_reference_path = self.write_json("fake-reference-job.json", fake_reference_job)
        fake_reference_plan_path = self.root / "fake-reference-plan.json"
        fake_reference_result = self.run_script(
            "build_plan.py", str(fake_reference_path), "--out", str(fake_reference_plan_path)
        )
        self.assertEqual(fake_reference_result.returncode, 2)
        fake_reference_plan = json.loads(fake_reference_plan_path.read_text(encoding="utf-8"))
        self.assertTrue(any("valid local image" in error for error in fake_reference_plan["validation"]["errors"]))

        bypass_plan = self.write_json("fake-reference-bypass-plan.json", {
            "status": "ready_for_approval",
            "validation": {"ok": True},
            "sku": {"id": "SKU-FAKE"},
            "facts": {"items": [{
                "key": "category", "value": "外套", "status": "confirmed", "evidence": "owner approved"
            }]},
            "product_reference_images": [{"path": fake_reference.name, "role": "garment front"}],
            "models": [],
        })
        bypass_slot = self.write_json("fake-reference-slot.json", {
            "id": "product-hero", "type": "product-main", "status": "planned", "reference_roles": ["front"]
        })
        bypass_result = self.run_script("build_prompt.py", str(bypass_plan), str(bypass_slot))
        self.assertEqual(bypass_result.returncode, 2)
        self.assertIn("valid local image", bypass_result.stderr)

        unknown_approval = self.base_job()
        unknown_approval["model"] = dict(unknown_approval["model"])
        unknown_approval["model"]["approved"] = "not-reviewed"
        unknown_path = self.write_json("unknown-approval-job.json", unknown_approval)
        unknown_plan_path = self.root / "unknown-approval-plan.json"
        unknown_result = self.run_script("build_plan.py", str(unknown_path), "--out", str(unknown_plan_path))
        self.assertEqual(unknown_result.returncode, 2)
        unknown_plan = json.loads(unknown_plan_path.read_text(encoding="utf-8"))
        self.assertTrue(any("must be approved" in error for error in unknown_plan["validation"]["errors"]))

        volatile = self.base_job()
        volatile["facts"] = list(volatile["facts"]) + [{"key": "price", "value": "99", "status": "confirmed", "evidence": "price-sheet"}]
        volatile_path = self.write_json("volatile-fact-job.json", volatile)
        volatile_plan_path = self.root / "volatile-fact-plan.json"
        volatile_result = self.run_script("build_plan.py", str(volatile_path), "--out", str(volatile_plan_path))
        self.assertEqual(volatile_result.returncode, 2)
        volatile_plan = json.loads(volatile_plan_path.read_text(encoding="utf-8"))
        self.assertTrue(any("volatile fact" in error for error in volatile_plan["validation"]["errors"]))

        volatile_copy = self.base_job()
        volatile_copy["copy_ledger"] = [{
            "id": "bad-copy",
            "slot_id": "construction-selling-point",
            "text": "限时折扣",
            "status": "confirmed",
            "evidence": "owner input",
            "allowed_surface": "image_text",
        }]
        volatile_copy_path = self.write_json("volatile-copy-job.json", volatile_copy)
        volatile_copy_plan_path = self.root / "volatile-copy-plan.json"
        volatile_copy_result = self.run_script(
            "build_plan.py", str(volatile_copy_path), "--out", str(volatile_copy_plan_path)
        )
        self.assertEqual(volatile_copy_result.returncode, 2)
        volatile_copy_plan = json.loads(volatile_copy_plan_path.read_text(encoding="utf-8"))
        self.assertTrue(any("temporary asset" in error for error in volatile_copy_plan["validation"]["errors"]))

        manifest, manifest_path, _ = self.valid_manifest()
        fake = dict(manifest)
        fake["slots"] = [dict(item) for item in manifest["slots"]]
        fake["slots"][0]["output"] = "fake-output.png"
        self.touch("fake-output.png", "not an image")
        fake_path = self.write_json("fake-image-manifest.json", fake)
        fake_result = self.run_script("validate_manifest.py", str(fake_path))
        self.assertEqual(fake_result.returncode, 2)
        self.assertIn("valid readable image", fake_result.stdout)

        numericless = self.base_job()
        self.write_json("size.json", {"size": "M", "unit": "cm"})
        numericless_path = self.write_json("numericless-size-job.json", numericless)
        numericless_plan_path = self.root / "numericless-size-plan.json"
        numericless_result = self.run_script("build_plan.py", str(numericless_path), "--out", str(numericless_plan_path))
        self.assertEqual(numericless_result.returncode, 0, numericless_result.stderr)
        self.assertEqual(json.loads(numericless_plan_path.read_text(encoding="utf-8"))["size_module"]["mode"], "fit-guidance")

        fit_manifest = dict(manifest)
        fit_manifest["size_module"] = {"mode": "fit-guidance", "fit": "M码", "ease": "100cm", "measuring_positions": "胸围", "styling_guidance": "体重"}
        fit_manifest["deliverables"] = {"model_count": 1, "include_size": True}
        fit_path = self.write_json("numeric-fit-manifest.json", fit_manifest)
        fit_result = self.run_script("validate_manifest.py", str(fit_path))
        self.assertEqual(fit_result.returncode, 2)
        self.assertIn("fit-guidance", fit_result.stdout)

    def test_two_model_packs_are_independent(self) -> None:
        job_data = self.base_job()
        model_two = self.image("model-two.png", (180, 180, 220))
        job_data.pop("model")
        job_data["models"] = [
            {"id": "model-001", "approved": True, "reference_images": [{"path": "model-front.png"}]},
            {"id": "model-002", "approved": True, "reference_images": [{"path": model_two.name}]},
        ]
        job_data["deliverables"] = {"detail_slices": 8, "model_count": 2}
        job_path = self.write_json("two-model-job.json", job_data)
        plan_path = self.root / "two-model-plan.json"
        result = self.run_script("build_plan.py", str(job_path), "--out", str(plan_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(len(plan["models"]), 2)
        self.assertEqual(plan["paid_calls_estimate"]["planned_base_outputs"], 9)
        self.assertEqual(plan["extra_outputs"][0]["model_group_id"], "model-002")

        first_slot = next(item for item in plan["deliverables"]["slots"] if item["id"] == "model-hero")
        second_slot = plan["extra_outputs"][0]
        first_slot_path = self.write_json("model-one-slot.json", first_slot)
        second_slot_path = self.write_json("model-two-slot.json", second_slot)
        first_prompt = self.run_script("build_prompt.py", str(plan_path), str(first_slot_path))
        second_prompt = self.run_script("build_prompt.py", str(plan_path), str(second_slot_path))
        self.assertEqual(first_prompt.returncode, 0, first_prompt.stderr)
        self.assertEqual(second_prompt.returncode, 0, second_prompt.stderr)
        self.assertIn("model-front.png", first_prompt.stdout)
        self.assertNotIn("model-two.png", first_prompt.stdout)
        self.assertIn("model-two.png", second_prompt.stdout)
        self.assertNotIn("model-front.png", second_prompt.stdout)

        job_data["models"] = job_data["models"][:1]
        bad_path = self.write_json("one-of-two-job.json", job_data)
        bad_plan_path = self.root / "one-of-two-plan.json"
        bad_result = self.run_script("build_plan.py", str(bad_path), "--out", str(bad_plan_path))
        self.assertEqual(bad_result.returncode, 2)
        bad_plan = json.loads(bad_plan_path.read_text(encoding="utf-8"))
        self.assertTrue(any("independent model packs" in error for error in bad_plan["validation"]["errors"]))

        duplicate_data = self.base_job()
        duplicate_data.pop("model")
        duplicate_data["models"] = [
            {"id": "same", "approved": True, "reference_images": [{"path": "model-front.png"}]},
            {"id": "same", "approved": True, "reference_images": [{"path": "model-two.png"}]},
        ]
        duplicate_data["deliverables"] = {"detail_slices": 8, "model_count": 2}
        duplicate_path = self.write_json("duplicate-model-job.json", duplicate_data)
        duplicate_plan_path = self.root / "duplicate-model-plan.json"
        duplicate_result = self.run_script("build_plan.py", str(duplicate_path), "--out", str(duplicate_plan_path))
        self.assertEqual(duplicate_result.returncode, 2)
        duplicate_plan = json.loads(duplicate_plan_path.read_text(encoding="utf-8"))
        self.assertTrue(any("duplicate model pack id" in error for error in duplicate_plan["validation"]["errors"]))

    def test_assemble_preview_is_non_destructive(self) -> None:
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is optional")
        first = self.root / "first.png"
        second = self.root / "second.png"
        Image.new("RGBA", (10, 20), (255, 0, 0, 255)).save(first)
        Image.new("RGBA", (20, 10), (0, 0, 255, 255)).save(second)
        output = self.root / "preview.png"
        result = self.run_script("assemble_preview.py", str(first), str(second), "--out", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(output) as preview:
            self.assertEqual(preview.size, (20, 30))
        again = self.run_script("assemble_preview.py", str(first), str(second), "--out", str(output))
        self.assertEqual(again.returncode, 2)
        self.assertIn("overwrite", again.stderr)


if __name__ == "__main__":
    unittest.main()
