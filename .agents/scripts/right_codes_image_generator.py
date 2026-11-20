#!/usr/bin/env python3
"""Generate images through the Right.codes asynchronous drawing API.

The paid POST is submitted exactly once. After a task_id is returned, only
non-billable GET polling is performed. A saved task id can be resumed with
``--resume-task`` without submitting a second generation.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from api_image_generator import (
    ImageGenerationError,
    _detect_image_format,
    _parse_env_file,
    _request_with_retries,
    _validate_references,
)


DEFAULT_BASE_URL = "https://www.rightapi.ai/draw"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_IMAGE_SIZE = "1K"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"
KEY_NAMES = ("RIGHT_CODES_API_KEY", "RIGHT_API_KEY", "GEMINI_API_KEY", "IMAGE_API_KEY")


@dataclass(frozen=True)
class RightCodesConfig:
    base_url: str
    api_key: str
    model: str
    timeout: int
    poll_interval: float

    @property
    def submit_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/v1/images/generations"

    def task_url(self, task_id: str) -> str:
        parsed = urllib.parse.urlsplit(self.base_url)
        origin = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
        return f"{origin}/v1/tasks/{urllib.parse.quote(task_id, safe='')}"


def _load_env(path: str | None) -> Mapping[str, str]:
    candidate = Path(path).expanduser() if path else DEFAULT_ENV_FILE
    if not candidate.is_file():
        if path:
            raise ImageGenerationError(f"Environment file not found: {candidate}")
        return {}
    return _parse_env_file(candidate)


def _configured_value(explicit: str | None, names: Sequence[str], values: Mapping[str, str]) -> str:
    if explicit is not None:
        return explicit
    for name in names:
        if name in os.environ:
            return os.environ[name]
    for name in names:
        if values.get(name):
            return values[name]
    return ""


def _config(args: argparse.Namespace, *, require_key: bool) -> RightCodesConfig:
    values = _load_env(args.env_file)
    key_names = (args.credential_name,) if args.credential_name else KEY_NAMES
    key = _configured_value(args.api_key, key_names, values)
    if require_key and not key:
        raise ImageGenerationError(
            "Missing Right.codes API key: set RIGHT_CODES_API_KEY, RIGHT_API_KEY, "
            "GEMINI_API_KEY, or IMAGE_API_KEY in the process environment or .env."
        )
    base_url = _configured_value(
        args.base_url,
        ("RIGHT_CODES_BASE_URL",),
        values,
    ) or DEFAULT_BASE_URL
    model = _configured_value(
        args.model,
        ("RIGHT_CODES_MODEL",),
        values,
    ) or DEFAULT_MODEL
    return RightCodesConfig(
        base_url=base_url.rstrip("/"),
        api_key=key,
        model=model,
        timeout=args.timeout,
        poll_interval=args.poll_interval,
    )


def _headers(config: RightCodesConfig) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "AI-Model-Photo-Workflow/RightCodes-1.0",
    }


def _json_request(
    request: urllib.request.Request,
    *,
    timeout: int,
    max_retries: int = 0,
) -> dict[str, Any]:
    payload, _ = _request_with_retries(request, timeout=timeout, max_retries=max_retries)
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImageGenerationError("Right.codes returned invalid JSON.") from exc
    if not isinstance(decoded, dict):
        raise ImageGenerationError("Right.codes response must be a JSON object.")
    return decoded


def _data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _build_payload(
    *,
    model: str,
    prompt: str,
    n: int,
    size: str,
    image_size: str,
    references: Sequence[Path],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size,
        "imageSize": image_size,
        "async": True,
    }
    if references:
        payload["image"] = [_data_url(path) for path in references]
    return payload


def submit_task(config: RightCodesConfig, payload: Mapping[str, Any]) -> str:
    request = urllib.request.Request(
        config.submit_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=_headers(config),
        method="POST",
    )
    print("Submitting exactly one paid Right.codes image task…", file=sys.stderr, flush=True)
    try:
        response = _json_request(request, timeout=config.timeout, max_retries=0)
    except ImageGenerationError as exc:
        raise ImageGenerationError(
            "Paid submission result is indeterminate; do not resubmit until provider usage is checked. "
            f"Cause: {exc}"
        ) from exc
    task_id = response.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise ImageGenerationError(
            "Paid submission returned no task_id; billing state is indeterminate. Do not resubmit."
        )
    print(f"Task accepted: {task_id}", file=sys.stderr, flush=True)
    return task_id


def poll_task(config: RightCodesConfig, task_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + config.timeout
    last_progress: Any = None
    while True:
        request = urllib.request.Request(
            config.task_url(task_id),
            headers=_headers(config),
            method="GET",
        )
        # GET polling cannot create another paid image; tolerate one transient GET failure.
        response = _json_request(request, timeout=min(config.timeout, 60), max_retries=1)
        status = str(response.get("status") or "").lower()
        progress = response.get("progress")
        if progress != last_progress:
            print(f"Task {task_id}: {status or 'result'} {progress if progress is not None else ''}".rstrip(), file=sys.stderr, flush=True)
            last_progress = progress
        if isinstance(response.get("data"), list) or isinstance(response.get("candidates"), list):
            return response
        if status in {"completed", "succeeded", "success"}:
            return response
        if status in {"failed", "cancelled", "canceled", "error"}:
            error = response.get("error")
            message = error.get("message") if isinstance(error, dict) else error
            raise ImageGenerationError(f"Right.codes task failed: {message or response.get('message') or status}")
        if time.monotonic() >= deadline:
            raise ImageGenerationError(
                f"Task {task_id} is still pending after {config.timeout}s. Resume it with --resume-task; do not submit again."
            )
        time.sleep(config.poll_interval)


def _result_items(response: Mapping[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    data = response.get("data")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                items.append({"url": item})
            elif isinstance(item, dict):
                items.append(dict(item))
    candidates = response.get("candidates")
    if not items and isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content")
            parts = content.get("parts") if isinstance(content, dict) else None
            if isinstance(parts, list):
                for part in parts:
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        text = part["text"].strip()
                        if text.startswith("http://") or text.startswith("https://"):
                            items.append({"url": text})
    if not items:
        raise ImageGenerationError("Completed Right.codes task contains no usable image result.")
    return items


def _image_bytes(item: Mapping[str, Any], config: RightCodesConfig) -> bytes:
    encoded = item.get("b64_json") or item.get("base64")
    if isinstance(encoded, str) and encoded:
        if encoded.startswith("data:") and "," in encoded:
            encoded = encoded.split(",", 1)[1]
        try:
            return base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ImageGenerationError("Right.codes returned invalid base64 image data.") from exc
    url = item.get("url")
    if isinstance(url, str) and url:
        request = urllib.request.Request(url, headers={"User-Agent": _headers(config)["User-Agent"]}, method="GET")
        payload, _ = _request_with_retries(request, timeout=config.timeout, max_retries=1)
        return payload
    raise ImageGenerationError("Right.codes result contains neither url nor base64 data.")


def _output_paths(output: Path, count: int) -> list[Path]:
    if count == 1:
        return [output]
    return [output.with_name(f"{output.stem}_{index}{output.suffix}") for index in range(1, count + 1)]


def check_auth(config: RightCodesConfig) -> None:
    """Perform a non-billable authenticated lookup for a nonexistent task."""

    request = urllib.request.Request(
        config.task_url("task_codex_auth_preflight_nonexistent"),
        headers=_headers(config),
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=min(config.timeout, 30)) as response:
            response.read()
            print("Right.codes task endpoint accepted the configured credential.")
    except urllib.error.HTTPError as exc:
        exc.read()
        if exc.code in {401, 403}:
            raise ImageGenerationError(f"Right.codes authentication failed with HTTP {exc.code}.") from exc
        if exc.code == 404:
            print("Right.codes authentication preflight passed (nonexistent task returned HTTP 404).")
            return
        raise ImageGenerationError(f"Right.codes auth preflight returned HTTP {exc.code}.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ImageGenerationError(f"Right.codes auth preflight connection failed: {exc}") from exc


def run(args: argparse.Namespace) -> list[Path]:
    if args.check_auth:
        check_auth(_config(args, require_key=True))
        return []
    if not args.resume_task and not (args.prompt and args.output):
        raise ImageGenerationError("PROMPT and OUTPUT are required unless --resume-task is used.")
    if args.resume_task and not args.output:
        raise ImageGenerationError("OUTPUT is required with --resume-task.")
    if args.n < 1 or args.n > 10:
        raise ImageGenerationError("N must be between 1 and 10.")
    references = _validate_references(args.references or [])
    config = _config(args, require_key=not args.dry_run)
    payload = _build_payload(
        model=config.model,
        prompt=args.prompt or "",
        n=args.n,
        size=args.size,
        image_size=args.image_size,
        references=references,
    )
    if args.dry_run:
        print(json.dumps({
            "provider": "right.codes",
            "submit_endpoint": config.submit_url,
            "task_endpoint_template": config.task_url("TASK_ID").replace("TASK_ID", "{task_id}"),
            "model": config.model,
            "n": args.n,
            "size": args.size,
            "imageSize": args.image_size,
            "async": True,
            "reference_count": len(references),
            "output_path": str(Path(args.output).expanduser().resolve()),
            "paid_post_retries": 0,
        }, ensure_ascii=False, indent=2))
        return []
    task_id = args.resume_task or submit_task(config, payload)
    result = poll_task(config, task_id)
    items = _result_items(result)
    if len(items) < args.n:
        raise ImageGenerationError(f"Right.codes returned {len(items)} image(s), expected {args.n}.")
    target = Path(args.output).expanduser().resolve()
    outputs = _output_paths(target, args.n)
    for path in outputs:
        if path.exists():
            raise ImageGenerationError(f"Refusing to overwrite existing output: {path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    for item, path in zip(items, outputs):
        image = _image_bytes(item, config)
        image_format = _detect_image_format(image)
        if image_format is None:
            raise ImageGenerationError("Downloaded Right.codes result is not a recognized image.")
        path.write_bytes(image)
        print(f"Saved: {path} ({image_format}); task_id={task_id}")
    return outputs


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("output", nargs="?")
    parser.add_argument("n", nargs="?", type=int, default=1)
    parser.add_argument("references", nargs="*")
    parser.add_argument("--resume-task")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key")
    parser.add_argument("--credential-name", choices=KEY_NAMES, help="select one configured key name for diagnostics")
    parser.add_argument("--model")
    parser.add_argument("--env-file")
    parser.add_argument("--size", default="1:1")
    parser.add_argument("--image-size", choices=("1K", "2K", "4K"), default=DEFAULT_IMAGE_SIZE)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--poll-interval", type=float, default=3.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check-auth", action="store_true", help="non-billable credential preflight")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        run(parse_args(argv))
        return 0
    except (ImageGenerationError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
