#!/usr/bin/env python3
"""Offline contract tests for the Right.codes asynchronous image client."""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("right_codes_image_generator.py")
SPEC = importlib.util.spec_from_file_location("right_codes_image_generator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RightCodesClientTests(unittest.TestCase):
    def test_dry_run_uses_async_draw_and_site_level_task_endpoint(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = MODULE.main(["test", "/tmp/right-codes.png", "1", "--dry-run"])
        self.assertEqual(result, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["provider"], "right.codes")
        self.assertEqual(payload["submit_endpoint"], "https://www.rightapi.ai/draw/v1/images/generations")
        self.assertEqual(payload["task_endpoint_template"], "https://www.rightapi.ai/v1/tasks/{task_id}")
        self.assertEqual(payload["model"], "gpt-image-2")
        self.assertTrue(payload["async"])
        self.assertEqual(payload["paid_post_retries"], 0)

    def test_reference_payload_uses_data_url_array(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "reference.png"
            reference.write_bytes(b"image")
            payload = MODULE._build_payload(
                model="gpt-image-2",
                prompt="edit",
                n=1,
                size="4:5",
                image_size="1K",
                references=[reference],
            )
        self.assertTrue(payload["async"])
        self.assertEqual(payload["size"], "4:5")
        self.assertTrue(payload["image"][0].startswith("data:image/png;base64,"))

    def test_one_submit_then_poll_and_save(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("RIGHT_CODES_API_KEY=test-key\n", encoding="utf-8")
            target = Path(directory) / "result.png"
            responses = [
                {"task_id": "task_test", "status": "processing"},
                {"task_id": "task_test", "status": "in_progress", "progress": 50},
                {"status": "completed", "data": [{"url": "https://cdn.example/result.png"}]},
            ]
            with mock.patch.object(MODULE, "_json_request", side_effect=responses) as request_json, mock.patch.object(
                MODULE, "_image_bytes", return_value=b"\x89PNG\r\n\x1a\nimage"
            ), mock.patch.object(MODULE.time, "sleep"):
                result = MODULE.main([
                    "test", str(target), "1", "--env-file", str(env_file), "--poll-interval", "0"
                ])
        self.assertEqual(result, 0)
        self.assertEqual(request_json.call_count, 3)
        submit_request = request_json.call_args_list[0].args[0]
        self.assertEqual(submit_request.get_method(), "POST")
        self.assertEqual(request_json.call_args_list[0].kwargs["max_retries"], 0)
        self.assertEqual(request_json.call_args_list[1].args[0].get_method(), "GET")

    def test_submit_transport_error_is_indeterminate_and_not_retried(self):
        config = MODULE.RightCodesConfig(
            base_url=MODULE.DEFAULT_BASE_URL,
            api_key="test-key",
            model="gpt-image-2",
            timeout=10,
            poll_interval=0,
        )
        with mock.patch.object(
            MODULE,
            "_json_request",
            side_effect=MODULE.ImageGenerationError("connection closed"),
        ) as request_json:
            with self.assertRaises(MODULE.ImageGenerationError) as raised:
                MODULE.submit_task(config, {"async": True})
        self.assertEqual(request_json.call_count, 1)
        self.assertIn("indeterminate", str(raised.exception))

    def test_resume_task_does_not_submit_another_paid_request(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("RIGHT_CODES_API_KEY=test-key\n", encoding="utf-8")
            target = Path(directory) / "resume.png"
            with mock.patch.object(MODULE, "submit_task") as submit, mock.patch.object(
                MODULE, "poll_task", return_value={"data": [{"b64_json": "ignored"}]}
            ), mock.patch.object(MODULE, "_image_bytes", return_value=b"\x89PNG\r\n\x1a\nimage"):
                result = MODULE.main([
                    "", str(target), "1", "--resume-task", "task_existing", "--env-file", str(env_file)
                ])
        self.assertEqual(result, 0)
        submit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
