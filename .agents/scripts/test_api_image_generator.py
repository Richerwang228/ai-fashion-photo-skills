#!/usr/bin/env python3
"""Offline contract tests for api_image_generator.py."""

import base64
import contextlib
import http.client
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("api_image_generator.py")
SPEC = importlib.util.spec_from_file_location("api_image_generator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FakeResponse:
    def __init__(self, payload, content_type="application/json"):
        self.payload = payload
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.payload


class IncompleteStreamResponse(FakeResponse):
    def read(self):
        raise http.client.IncompleteRead(self.payload)


class ImageGeneratorContractTests(unittest.TestCase):
    def test_legacy_cli_dry_run_forwards_to_right_codes(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = MODULE.main(
                ["portrait prompt", "/tmp/result.png", "1", "--dry-run"]
            )
        self.assertEqual(result, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(
            payload["submit_endpoint"],
            "https://www.rightapi.ai/draw/v1/images/generations",
        )
        self.assertEqual(payload["provider"], "right.codes")
        self.assertEqual(payload["model"], "gpt-image-2")
        self.assertEqual(payload["reference_count"], 0)
        self.assertEqual(payload["paid_post_retries"], 0)

    def test_env_file_is_parsed_in_memory_and_process_env_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / "provider.env"
            env_file.write_text(
                'export IMAGE_API_KEY="file-secret"\n'
                'IMAGE_API_BASE_URL=https://file.example/v1 # comment\n'
                'UNRELATED_SECRET=must-not-load\n',
                encoding="utf-8",
            )
            before = dict(MODULE.os.environ)
            loaded = MODULE.load_env_file(str(env_file))
            self.assertEqual(loaded["IMAGE_API_KEY"], "file-secret")
            self.assertNotIn("UNRELATED_SECRET", loaded)
            self.assertEqual(dict(MODULE.os.environ), before)
            with mock.patch.dict(MODULE.os.environ, {"IMAGE_API_KEY": "process-secret"}, clear=True):
                config = MODULE.ProviderConfig.from_env(file_values=loaded)
            self.assertEqual(config.api_key, "process-secret")
            self.assertEqual(config.base_url, "https://file.example/v1")

    def test_env_errors_never_echo_secret_values(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / "bad.env"
            env_file.write_text("IMAGE_API_KEY=do-not-print-me\nnot valid\n", encoding="utf-8")
            with self.assertRaises(MODULE.ImageGenerationError) as raised:
                MODULE.load_env_file(str(env_file))
        self.assertNotIn("do-not-print-me", str(raised.exception))

    def test_legacy_reference_dry_run_uses_right_codes_single_endpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "reference.png"
            reference.write_bytes(b"fake-image")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = MODULE.main(
                    [
                        "edit prompt",
                        str(Path(directory) / "result.png"),
                        "1",
                        str(reference),
                        "--dry-run",
                    ]
                )
        self.assertEqual(result, 0)
        payload = json.loads(output.getvalue())
        self.assertTrue(payload["submit_endpoint"].endswith("/images/generations"))
        self.assertEqual(payload["reference_count"], 1)

    def test_multiple_references_use_image_array_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            references = []
            for name in ("model.png", "top.png", "bottom.png"):
                path = Path(directory) / name
                path.write_bytes(b"fake-image")
                references.append(path)
            config = MODULE.ProviderConfig.from_env(
                api_key="test-key",
                require_key=True,
            )
            request, _ = MODULE._build_request(
                config,
                prompt="test",
                n=1,
                size="1024x1024",
                quality="standard",
                style="vivid",
                response_format="url",
                reference_images=references,
            )
        self.assertEqual(request.data.count(b'name="image[]"'), 3)

    def test_text_generation_uses_typed_json_stream_parameters(self):
        config = MODULE.ProviderConfig.from_env(
            api_key="test-key",
            require_key=True,
        )
        request, _ = MODULE._build_request(
            config,
            prompt="test",
            n=2,
            size="1024x1024",
            quality="standard",
            style=None,
            response_format="url",
            reference_images=[],
            stream=True,
            partial_images=3,
        )
        payload = json.loads(request.data)
        self.assertEqual(payload["n"], 2)
        self.assertIsInstance(payload["n"], int)
        self.assertIs(payload["stream"], True)
        self.assertEqual(payload["partial_images"], 3)
        self.assertIsInstance(payload["partial_images"], int)
        self.assertEqual(request.get_header("Accept"), "text/event-stream")

    def test_chat_completions_mode_remains_available(self):
        config = MODULE.ProviderConfig.from_env(
            api_key="test-key",
            api_mode="chat_completions",
            require_key=True,
        )
        _, url = MODULE._build_request(
            config,
            prompt="test",
            n=1,
            size="1024x1024",
            quality="standard",
            style=None,
            response_format="url",
            reference_images=[],
        )
        self.assertTrue(url.endswith("/chat/completions"))

    def test_missing_reference_aborts_before_request(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            result = MODULE.main(
                [
                    "edit prompt",
                    "/tmp/result.png",
                    "1",
                    "/definitely/missing/reference.png",
                    "--dry-run",
                ]
            )
        self.assertEqual(result, 1)
        self.assertIn("generation was not started", error.getvalue())

    def test_base64_result_is_saved(self):
        image = b"\x89PNG\r\n\x1a\ncontract-test"
        response = json.dumps(
            {"data": [{"b64_json": base64.b64encode(image).decode()}]}
        ).encode()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "result.png"
            with mock.patch.object(
                MODULE.urllib.request,
                "urlopen",
                return_value=FakeResponse(response),
            ):
                outputs = MODULE.generate_images(
                    prompt="test",
                    output_path=str(target),
                    api_key="test-key",
                )
            self.assertEqual(outputs, [target.resolve()])
            self.assertEqual(target.read_bytes(), image)

    def test_unsupported_response_fails(self):
        with self.assertRaises(MODULE.ImageGenerationError):
            MODULE._decode_response(b'{"choices": []}')

    def test_chat_markdown_image_url_is_decoded(self):
        response = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": "Generated: ![result](https://example.com/image.png)"
                        }
                    }
                ]
            }
        ).encode()
        self.assertEqual(
            MODULE._decode_response(response),
            [{"url": "https://example.com/image.png"}],
        )

    def test_streaming_edit_request_and_completed_event(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "reference.png"
            reference.write_bytes(b"fake-image")
            config = MODULE.ProviderConfig.from_env(
                api_key="test-key",
                require_key=True,
            )
            request, _ = MODULE._build_request(
                config,
                prompt="test",
                n=1,
                size="1536x1024",
                quality="standard",
                style=None,
                response_format="url",
                reference_images=[reference],
                stream=True,
                partial_images=1,
            )
        self.assertIn(b'name="stream"', request.data)
        self.assertIn(b"\r\ntrue\r\n", request.data)
        self.assertIn(b'name="partial_images"', request.data)

        image = base64.b64encode(b"\x89PNG\r\n\x1a\nstream-test").decode()
        event = (
            'event: image_edit.completed\n'
            f'data: {{"type":"image_edit.completed","b64_json":"{image}"}}\n\n'
        ).encode()
        self.assertEqual(
            MODULE._decode_response(event, "text/event-stream"),
            [{"type": "image_edit.completed", "b64_json": image}],
        )

        request = MODULE.urllib.request.Request("https://example.com")
        with mock.patch.object(
            MODULE.urllib.request,
            "urlopen",
            return_value=IncompleteStreamResponse(event, "text/event-stream"),
        ):
            recovered, content_type = MODULE._request_with_retries(
                request,
                timeout=10,
                max_retries=0,
            )
        self.assertEqual(recovered, event)
        self.assertEqual(content_type, "text/event-stream")

        partial_event = (
            'event: image_edit.partial_image\n'
            f'data: {{"type":"image_edit.partial_image","b64_json":"{image}",'
            '"partial_image_index":0}\n\n'
        ).encode()
        self.assertEqual(
            MODULE._decode_response(partial_event, "text/event-stream"),
            [
                {
                    "type": "image_edit.partial_image",
                    "b64_json": image,
                    "partial_image_index": 0,
                    "_partial_fallback": True,
                }
            ],
        )
        with self.assertRaises(MODULE.ImageGenerationError):
            MODULE._decode_response(
                partial_event,
                "text/event-stream",
                require_completed=True,
            )


if __name__ == "__main__":
    unittest.main()
