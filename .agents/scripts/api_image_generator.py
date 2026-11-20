#!/usr/bin/env python3
"""OpenAI-compatible image generation client for the model-photo workflow.

The legacy positional CLI remains supported:
    python3 api_image_generator.py PROMPT OUTPUT [N] [REFERENCE_IMAGE ...]

Configuration is read from process environment variables first, then (when
present) the project-root ``.env`` file. An alternate dotenv file can be
selected with ``--env-file``. Values are parsed in memory and never printed or
written back:
    IMAGE_API_BASE_URL  default: https://fushengyunsuan.com/v1
    IMAGE_API_KEY       required (NEW_API_KEY is accepted as a compatibility alias)
    IMAGE_MODEL         default: gpt-image-2
    IMAGE_API_MODE      default: images
"""

from __future__ import annotations

import argparse
import base64
import binascii
import http.client
import json
import mimetypes
import os
import queue
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


DEFAULT_BASE_URL = "https://fushengyunsuan.com/v1"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_API_MODE = "images"
RETRYABLE_HTTP_CODES = {408, 409, 425, 429, 500, 502, 503, 504}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"
PROVIDER_ENV_KEYS = frozenset(
    {
        "IMAGE_API_BASE_URL",
        "IMAGE_API_KEY",
        "IMAGE_MODEL",
        "IMAGE_API_MODE",
        "NEW_API_KEY",
    }
)
_ENV_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ImageGenerationError(RuntimeError):
    """Raised when the provider request or result is invalid."""


def _env_file_error(path: Path, line_number: Optional[int], message: str) -> ImageGenerationError:
    location = f"{path}"
    if line_number is not None:
        location += f":{line_number}"
    return ImageGenerationError(f"Invalid environment file {location}: {message}")


def _strip_env_inline_comment(value: str) -> str:
    """Strip shell-style comments without touching # inside quoted values."""
    quote: Optional[str] = None
    escaped = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote == '"':
            escaped = True
            continue
        if character in {'"', "'"}:
            if quote is None:
                quote = character
            elif quote == character:
                quote = None
            continue
        if character == "#" and quote is None and (
            index == 0 or value[index - 1].isspace()
        ):
            return value[:index].rstrip()
    return value.strip()


def _unescape_double_quoted(value: str) -> str:
    """Decode common dotenv double-quote escapes while preserving unknown ones."""
    escaped = False
    output: List[str] = []
    escapes = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v"}
    for character in value:
        if escaped:
            if character in escapes:
                output.append(escapes[character])
            elif character in {'"', "\\", "$"}:
                output.append(character)
            else:
                output.extend(("\\", character))
            escaped = False
        elif character == "\\":
            escaped = True
        else:
            output.append(character)
    if escaped:
        output.append("\\")
    return "".join(output)


def _parse_env_value(raw_value: str, *, path: Path, line_number: int) -> str:
    value = _strip_env_inline_comment(raw_value.strip())
    if not value:
        return ""
    if value[0] not in {'"', "'"}:
        if value[-1] in {'"', "'"}:
            raise _env_file_error(path, line_number, "unmatched quote")
        return value

    quote = value[0]
    if len(value) < 2 or value[-1] != quote:
        raise _env_file_error(path, line_number, "unmatched quote")
    inner = value[1:-1]
    if quote == "'":
        return inner
    return _unescape_double_quoted(inner)


def _parse_env_file(path: Path) -> Dict[str, str]:
    """Parse a dotenv-style file without executing it or exposing its values."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise ImageGenerationError(f"Environment file not found: {path}") from exc
    except IsADirectoryError as exc:
        raise ImageGenerationError(f"Environment file is a directory: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ImageGenerationError(
            f"Environment file is not valid UTF-8: {path}"
        ) from exc
    except OSError as exc:
        raise ImageGenerationError(f"Cannot read environment file: {path}") from exc

    values: Dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "export" or (
            line.startswith("export")
            and len(line) > len("export")
            and line[len("export")].isspace()
        ):
            export_tail = line[6:]
            if not export_tail or not export_tail[0].isspace():
                raise _env_file_error(path, line_number, "expected KEY=VALUE")
            line = export_tail.lstrip()
        if "=" not in line:
            raise _env_file_error(path, line_number, "expected KEY=VALUE")
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not _ENV_KEY_PATTERN.fullmatch(key):
            raise _env_file_error(path, line_number, "invalid variable name")
        values[key] = _parse_env_value(
            raw_value,
            path=path,
            line_number=line_number,
        )
    return values


def load_env_file(env_file: Optional[str] = None) -> Mapping[str, str]:
    """Load provider settings in memory; never mutate the process or write a file.

    With no explicit path, a project-root ``.env`` is optional. An explicit path
    must exist and be readable. Only provider settings are returned to avoid
    importing unrelated secrets from a larger project environment file.
    """
    if env_file is None:
        path = DEFAULT_ENV_FILE
        if not path.is_file():
            return {}
    else:
        path = Path(env_file).expanduser()
        if not path.is_file():
            raise ImageGenerationError(f"Environment file not found: {path}")
    parsed = _parse_env_file(path)
    return {key: value for key, value in parsed.items() if key in PROVIDER_ENV_KEYS}


def _configured_value(
    explicit: Optional[str],
    names: Sequence[str],
    file_values: Mapping[str, str],
) -> str:
    if explicit is not None:
        return explicit
    process_value_seen = False
    for name in names:
        if name not in os.environ:
            continue
        process_value_seen = True
        value = os.environ[name]
        if value:
            return value
    if process_value_seen:
        return ""
    for name in names:
        value = file_values.get(name)
        if value:
            return value
    return ""


@dataclass(frozen=True)
class ProviderConfig:
    base_url: str
    api_key: str
    model: str
    api_mode: str
    timeout: int
    max_retries: int

    @classmethod
    def from_env(
        cls,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_mode: Optional[str] = None,
        timeout: int = 300,
        max_retries: int = 0,
        require_key: bool = True,
        env_file: Optional[str] = None,
        file_values: Optional[Mapping[str, str]] = None,
    ) -> "ProviderConfig":
        env_values = (
            file_values if file_values is not None else load_env_file(env_file)
        )
        resolved_key = _configured_value(
            api_key,
            ("IMAGE_API_KEY", "NEW_API_KEY"),
            env_values,
        )
        if require_key and not resolved_key:
            raise ImageGenerationError(
                "Missing API key: set IMAGE_API_KEY (or NEW_API_KEY) in the "
                "process environment or the selected environment file."
            )
        resolved_base = (
            _configured_value(base_url, ("IMAGE_API_BASE_URL",), env_values)
            or DEFAULT_BASE_URL
        ).rstrip("/")
        resolved_mode = (
            _configured_value(api_mode, ("IMAGE_API_MODE",), env_values)
            or DEFAULT_API_MODE
        ).strip()
        if resolved_mode not in {"chat_completions", "images"}:
            raise ImageGenerationError(
                "IMAGE_API_MODE must be 'chat_completions' or 'images'."
            )
        return cls(
            base_url=resolved_base,
            api_key=resolved_key,
            model=_configured_value(model, ("IMAGE_MODEL",), env_values) or DEFAULT_MODEL,
            api_mode=resolved_mode,
            timeout=timeout,
            max_retries=max_retries,
        )


def _json_error_body(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        return "empty response body"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text[:1000]
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error)
        return str(payload.get("message") or payload)
    return str(payload)


def _request_with_retries(
    request: urllib.request.Request,
    *,
    timeout: int,
    max_retries: int,
) -> Tuple[bytes, str]:
    last_error: Optional[BaseException] = None
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                try:
                    return response.read(), content_type
                except http.client.IncompleteRead as exc:
                    partial = exc.partial or b""
                    if partial and (
                        "text/event-stream" in content_type.lower()
                        or partial.lstrip().startswith((b"event:", b"data:"))
                    ):
                        return partial, content_type
                    raise ImageGenerationError(
                        "Provider closed an incomplete non-streaming response."
                    ) from exc
        except urllib.error.HTTPError as exc:
            body = exc.read()
            message = _json_error_body(body)
            if exc.code not in RETRYABLE_HTTP_CODES or attempt >= max_retries:
                raise ImageGenerationError(
                    f"Provider returned HTTP {exc.code}: {message}"
                ) from exc
            last_error = exc
        except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError) as exc:
            if attempt >= max_retries:
                raise ImageGenerationError(
                    f"Provider connection failed after {attempt + 1} attempt(s): {exc}"
                ) from exc
            last_error = exc
        time.sleep(2**attempt)
    raise ImageGenerationError(f"Provider request failed: {last_error}")


def _request_sse_stream(
    request: urllib.request.Request,
    *,
    timeout: int,
    max_retries: int,
    heartbeat_seconds: int = 5,
) -> Tuple[bytes, str]:
    """Read an SSE response incrementally while keeping the invoking terminal alive.

    Some execution hosts terminate a process which produces no terminal output for
    a short period.  ``response.read()`` defeats SSE in that environment because
    partial image events remain buffered until the provider closes the stream.
    This reader emits progress as each event arrives and a low-frequency heartbeat
    while the provider is still rendering.  It deliberately returns the original
    SSE bytes so the normal completed-event validation remains the sole authority
    for saving a final asset.
    """

    updates: "queue.Queue[Tuple[str, Any]]" = queue.Queue()

    def _read_once() -> Tuple[bytes, str]:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            updates.put(("opened", content_type))
            chunks: List[bytes] = []
            try:
                for raw_line in response:
                    chunks.append(raw_line)
                    line = raw_line.strip()
                    if not line.startswith(b"data:"):
                        continue
                    try:
                        event = json.loads(line[5:].strip().decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                    if isinstance(event, dict):
                        event_type = str(event.get("type") or "event")
                        updates.put(("event", event_type))
                return b"".join(chunks), content_type
            except http.client.IncompleteRead as exc:
                partial = exc.partial or b""
                if partial and (
                    "text/event-stream" in content_type.lower()
                    or partial.lstrip().startswith((b"event:", b"data:"))
                ):
                    return b"".join(chunks) + partial, content_type
                raise ImageGenerationError(
                    "Provider closed an incomplete non-streaming response."
                ) from exc

    def _worker() -> None:
        last_error: Optional[BaseException] = None
        for attempt in range(max_retries + 1):
            try:
                updates.put(("submitted", attempt + 1))
                payload, content_type = _read_once()
                updates.put(("done", (payload, content_type)))
                return
            except urllib.error.HTTPError as exc:
                message = _json_error_body(exc.read())
                error = ImageGenerationError(
                    f"Provider returned HTTP {exc.code}: {message}"
                )
            except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError) as exc:
                error = ImageGenerationError(
                    f"Provider connection failed after {attempt + 1} attempt(s): {exc}"
                )
            except ImageGenerationError as exc:
                updates.put(("error", exc))
                return
            except Exception as exc:  # Preserve unexpected reader errors.
                updates.put(("error", exc))
                return
            if attempt >= max_retries:
                updates.put(("error", error))
                return
            last_error = error
            time.sleep(2**attempt)
        updates.put(("error", ImageGenerationError(f"Provider request failed: {last_error}")))

    worker = threading.Thread(target=_worker, name="image-sse-reader", daemon=True)
    worker.start()
    print("SSE request submitted; waiting for provider events…", file=sys.stderr, flush=True)
    while True:
        try:
            kind, value = updates.get(timeout=heartbeat_seconds)
        except queue.Empty:
            print("SSE still waiting for provider event…", file=sys.stderr, flush=True)
            continue
        if kind == "opened":
            print("SSE connection opened.", file=sys.stderr, flush=True)
        elif kind == "event":
            print(f"SSE event: {value}", file=sys.stderr, flush=True)
        elif kind == "done":
            worker.join()
            return value
        elif kind == "error":
            worker.join()
            if isinstance(value, ImageGenerationError):
                raise value
            raise ImageGenerationError(f"Provider request failed: {value}") from value


def _multipart_body(
    fields: Sequence[Tuple[str, str]],
    files: Sequence[Tuple[str, Path]],
) -> Tuple[bytes, str]:
    boundary = f"codex-{uuid.uuid4().hex}"
    chunks: List[bytes] = []

    for name, value in fields:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    for field_name, path in files:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{field_name}"; '
                    f'filename="{path.name}"\r\n'
                ).encode(),
                f"Content-Type: {content_type}\r\n\r\n".encode(),
                path.read_bytes(),
                b"\r\n",
            ]
        )

    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), boundary


def _validate_references(reference_images: Iterable[str]) -> List[Path]:
    paths = [Path(item).expanduser().resolve() for item in reference_images]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise ImageGenerationError(
            "Reference image(s) not found; generation was not started:\n- "
            + "\n- ".join(missing)
        )
    return paths


def _reference_data_url(path: Path) -> str:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def _build_request(
    config: ProviderConfig,
    *,
    prompt: str,
    n: int,
    size: str,
    quality: str,
    style: Optional[str],
    response_format: str,
    reference_images: Sequence[Path],
    stream: bool = False,
    partial_images: int = 0,
) -> Tuple[urllib.request.Request, str]:
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "User-Agent": "AI-Model-Photo-Workflow/2.0",
        "Accept": "application/json",
    }

    if config.api_mode == "chat_completions":
        url = f"{config.base_url}/chat/completions"
        if reference_images:
            user_content: Any = [{"type": "text", "text": prompt}]
            user_content.extend(
                {
                    "type": "image_url",
                    "image_url": {"url": _reference_data_url(path)},
                }
                for path in reference_images
            )
        else:
            user_content = prompt

        payload: Dict[str, Any] = {
            "model": config.model,
            "messages": [{"role": "user", "content": user_content}],
            "size": size,
            "quality": quality,
            "n": n,
        }
        if style:
            payload["style"] = style
        if stream:
            payload["stream"] = True
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
        return urllib.request.Request(url, data=body, headers=headers, method="POST"), url

    endpoint = "images/edits" if reference_images else "images/generations"
    url = f"{config.base_url}/{endpoint}"
    if reference_images:
        common_fields: List[Tuple[str, str]] = [
            ("model", config.model),
            ("prompt", prompt),
            ("n", str(n)),
            ("size", size),
            ("quality", quality),
            ("response_format", response_format),
        ]
        if style:
            common_fields.append(("style", style))
        if stream:
            common_fields.extend(
                [
                    ("stream", "true"),
                    ("partial_images", str(partial_images)),
                ]
            )
        body, boundary = _multipart_body(
            common_fields,
            [("image[]", path) for path in reference_images],
        )
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    else:
        payload: Dict[str, Any] = {
            "model": config.model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality,
            "response_format": response_format,
        }
        if style:
            payload["style"] = style
        if stream:
            payload["stream"] = True
            payload["partial_images"] = partial_images
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if stream:
        headers["Accept"] = "text/event-stream"

    return urllib.request.Request(url, data=body, headers=headers, method="POST"), url


def _items_from_chat_content(value: Any) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if isinstance(value, list):
        for entry in value:
            items.extend(_items_from_chat_content(entry))
        return items
    if isinstance(value, dict):
        if isinstance(value.get("b64_json"), str):
            return [{"b64_json": value["b64_json"]}]
        if isinstance(value.get("base64"), str):
            return [{"base64": value["base64"]}]
        if isinstance(value.get("url"), str):
            return [{"url": value["url"]}]
        image_url = value.get("image_url")
        if isinstance(image_url, str):
            return [{"url": image_url}]
        if isinstance(image_url, dict) and isinstance(image_url.get("url"), str):
            return [{"url": image_url["url"]}]
        for key in ("content", "data", "images", "result", "output"):
            if key in value:
                items.extend(_items_from_chat_content(value[key]))
        return items
    if not isinstance(value, str) or not value.strip():
        return items

    text = value.strip()
    if text.startswith(("{", "[")):
        try:
            return _items_from_chat_content(json.loads(text))
        except json.JSONDecodeError:
            pass

    data_urls = re.findall(
        r"data:image/[^;,\s]+;base64,([A-Za-z0-9+/=\r\n]+)",
        text,
    )
    items.extend(
        {"b64_json": encoded.replace("\n", "").replace("\r", "")}
        for encoded in data_urls
    )

    markdown_urls = re.findall(r"!\[[^\]]*\]\((https?://[^)\s]+)\)", text)
    items.extend({"url": url} for url in markdown_urls)

    if not markdown_urls:
        plain_urls = re.findall(r"https?://[^\s<>()\"']+", text)
        items.extend({"url": url.rstrip(".,;]}")} for url in plain_urls)
    return items


def _decode_stream_response(
    payload: bytes,
    *,
    require_completed: bool = False,
) -> List[Dict[str, Any]]:
    completed: List[Dict[str, Any]] = []
    partials: List[Dict[str, Any]] = []
    for raw_line in payload.decode("utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            continue
        try:
            event = json.loads(data)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type") or "")
        if event_type.endswith(".completed") and (
            event.get("b64_json") or event.get("url")
        ):
            completed.append(event)
        elif event_type.endswith(".partial_image") and (
            event.get("b64_json") or event.get("url")
        ):
            partials.append(event)
    if completed:
        return completed
    if partials:
        if require_completed:
            raise ImageGenerationError(
                "Provider stream ended without a completed image event."
            )
        fallback = dict(partials[-1])
        fallback["_partial_fallback"] = True
        return [fallback]
    raise ImageGenerationError("Provider stream contained no completed image event.")


def _decode_response(
    payload: bytes,
    content_type: str = "",
    *,
    require_completed: bool = False,
) -> List[Dict[str, Any]]:
    if "text/event-stream" in content_type.lower() or payload.lstrip().startswith(
        (b"event:", b"data:")
    ):
        return _decode_stream_response(
            payload,
            require_completed=require_completed,
        )
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImageGenerationError("Provider returned invalid JSON.") from exc

    if not isinstance(parsed, dict):
        raise ImageGenerationError("Provider response must be a JSON object.")
    if parsed.get("error"):
        raise ImageGenerationError(f"Provider error: {parsed['error']}")

    candidates = parsed.get("data")
    if not isinstance(candidates, list):
        candidates = parsed.get("images")
    normalized: List[Dict[str, Any]] = []
    if isinstance(candidates, list):
        for item in candidates:
            if isinstance(item, str):
                normalized.append({"url": item})
            elif isinstance(item, dict):
                normalized.append(item)

    choices = parsed.get("choices")
    if not normalized and isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            message = choice.get("message")
            if isinstance(message, dict):
                normalized.extend(_items_from_chat_content(message.get("content")))
                normalized.extend(_items_from_chat_content(message.get("images")))

    if not normalized:
        raise ImageGenerationError(
            "Provider response contains no usable image URL or base64 data."
        )
    return normalized


def _download_url(url: str, *, timeout: int, max_retries: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AI-Model-Photo-Workflow/2.0"},
        method="GET",
    )
    payload, _ = _request_with_retries(
        request,
        timeout=timeout,
        max_retries=max_retries,
    )
    return payload


def _image_bytes(item: Dict[str, Any], config: ProviderConfig) -> bytes:
    encoded = item.get("b64_json") or item.get("base64")
    if isinstance(encoded, str) and encoded:
        if encoded.startswith("data:") and "," in encoded:
            encoded = encoded.split(",", 1)[1]
        try:
            return base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ImageGenerationError("Provider returned invalid base64 image data.") from exc

    url = item.get("url")
    if isinstance(url, str) and url:
        return _download_url(
            url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )
    raise ImageGenerationError("Image result contains neither url nor b64_json.")


def _detect_image_format(data: bytes) -> Optional[str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    return None


def _output_paths(output_path: Path, count: int) -> List[Path]:
    if count == 1:
        return [output_path]
    return [
        output_path.with_name(f"{output_path.stem}_{index}{output_path.suffix}")
        for index in range(1, count + 1)
    ]


def generate_images(
    *,
    prompt: str,
    output_path: str,
    number_of_images: int = 1,
    image_paths: Optional[Sequence[str]] = None,
    size: str = "1024x1024",
    quality: str = "standard",
    style: Optional[str] = None,
    response_format: str = "url",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    api_mode: Optional[str] = None,
    env_file: Optional[str] = None,
    timeout: int = 300,
    max_retries: int = 0,
    stream: bool = False,
    partial_images: int = 0,
    require_completed: bool = True,
    dry_run: bool = False,
) -> List[Path]:
    if not prompt.strip():
        raise ImageGenerationError("Prompt must not be empty.")
    if not 1 <= number_of_images <= 10:
        raise ImageGenerationError("number_of_images must be between 1 and 10.")
    if not 0 <= partial_images <= 3:
        raise ImageGenerationError("partial_images must be between 0 and 3.")
    if partial_images and not stream:
        raise ImageGenerationError("partial_images requires stream=True.")

    references = _validate_references(image_paths or [])
    env_values = load_env_file(env_file)
    config = ProviderConfig.from_env(
        base_url=base_url,
        api_key=api_key,
        model=model,
        api_mode=api_mode,
        timeout=timeout,
        max_retries=max_retries,
        require_key=not dry_run,
        file_values=env_values,
    )
    request, url = _build_request(
        config,
        prompt=prompt,
        n=number_of_images,
        size=size,
        quality=quality,
        style=style,
        response_format=response_format,
        reference_images=references,
        stream=stream,
        partial_images=partial_images,
    )

    if dry_run:
        print(
            json.dumps(
                {
                    "endpoint": url,
                    "model": config.model,
                    "api_mode": config.api_mode,
                    "reference_count": len(references),
                    "n": number_of_images,
                    "size": size,
                    "quality": quality,
                    "style": style,
                    "response_format": response_format,
                    "stream": stream,
                    "partial_images": partial_images,
                    "require_completed": require_completed,
                    "output_path": str(Path(output_path).expanduser().resolve()),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return []

    if stream:
        response, content_type = _request_sse_stream(
            request,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )
    else:
        response, content_type = _request_with_retries(
            request,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )
    items = _decode_response(
        response,
        content_type,
        require_completed=require_completed,
    )
    if len(items) < number_of_images:
        raise ImageGenerationError(
            f"Provider returned {len(items)} image(s), expected {number_of_images}."
        )

    target = Path(output_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    outputs = _output_paths(target, number_of_images)
    for item, path in zip(items, outputs):
        if item.get("_partial_fallback"):
            print(
                "Warning: provider omitted the completed SSE event; "
                "saving the last fully received partial image.",
                file=sys.stderr,
            )
        data = _image_bytes(item, config)
        detected_format = _detect_image_format(data)
        if not detected_format:
            raise ImageGenerationError(
                f"Provider result is not a recognized PNG, JPEG, GIF, or WebP image: {path}"
            )
        path.write_bytes(data)
        print(f"Saved: {path} ({detected_format})")
    return outputs


def generate_image_with_provider(
    prompt: str,
    output_path: str,
    number_of_images: int = 1,
    image_paths: Optional[Sequence[str]] = None,
    env_file: Optional[str] = None,
) -> List[Path]:
    """Compatibility wrapper for older project imports."""
    return generate_images(
        prompt=prompt,
        output_path=output_path,
        number_of_images=number_of_images,
        image_paths=image_paths,
        env_file=env_file,
    )


generate_image_with_google = generate_image_with_provider


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate images through an OpenAI-compatible provider API."
    )
    parser.add_argument("prompt")
    parser.add_argument("output_path")
    parser.add_argument("number_of_images", nargs="?", type=int, default=1)
    parser.add_argument("reference_images", nargs="*")
    parser.add_argument("--base-url")
    parser.add_argument(
        "--env-file",
        help=(
            "Optional dotenv file. Defaults to the project-root .env when present; "
            "process environment values take precedence."
        ),
    )
    parser.add_argument("--model")
    parser.add_argument(
        "--api-mode",
        choices=["chat_completions", "images"],
        default=None,
        help="Provider route. Defaults to IMAGE_API_MODE or images.",
    )
    parser.add_argument("--size", default="1024x1024")
    parser.add_argument("--quality", default="standard")
    parser.add_argument(
        "--style",
        default=None,
        help="Optional provider style preset; omitted by default for gpt-image-2 edits.",
    )
    parser.add_argument(
        "--response-format",
        choices=["url", "b64_json"],
        default="url",
    )
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument(
        "--max-retries",
        type=int,
        default=0,
        help="Paid POST retry count. Keep at 0 unless duplicate billing is acceptable.",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Use SSE image streaming to avoid idle connection timeouts.",
    )
    parser.add_argument(
        "--partial-images",
        type=int,
        default=0,
        help="Number of streamed partial images (0-3); requires --stream.",
    )
    completion_group = parser.add_mutually_exclusive_group()
    completion_group.add_argument(
        "--require-completed",
        dest="require_completed",
        action="store_true",
        help="Reject streams without an explicit completed image event (default).",
    )
    completion_group.add_argument(
        "--allow-partial-fallback",
        dest="require_completed",
        action="store_false",
        help="Diagnostic only: allow saving the last partial event.",
    )
    parser.set_defaults(require_completed=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    if args.max_retries != 0:
        print("Error: legacy paid retries are disabled; Right.codes submissions are always single-shot.", file=sys.stderr)
        return 1
    if args.api_mode == "chat_completions":
        print("Error: project image generation is pinned to the Right.codes async Images route.", file=sys.stderr)
        return 1

    # Preserve the historical command path used by older prompts while routing
    # every CLI generation through the verified Right.codes async client.
    from right_codes_image_generator import main as right_codes_main

    translated: List[str] = [
        args.prompt,
        args.output_path,
        str(args.number_of_images),
        *args.reference_images,
        "--credential-name",
        "RIGHT_CODES_API_KEY",
        "--model",
        args.model or "gpt-image-2",
        "--size",
        args.size,
        "--image-size",
        "1K",
        "--timeout",
        str(max(args.timeout, 600)),
    ]
    if args.env_file:
        translated.extend(["--env-file", args.env_file])
    if args.dry_run:
        translated.append("--dry-run")
    return right_codes_main(translated)


if __name__ == "__main__":
    sys.exit(main())
