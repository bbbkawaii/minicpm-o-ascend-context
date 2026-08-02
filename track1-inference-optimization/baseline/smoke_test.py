#!/usr/bin/env python3
"""Run a deterministic text-only correctness smoke test against vLLM-Omni."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request


def request_json(url: str, payload: dict | None = None, timeout: float = 30) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def wait_until_ready(base_url: str, wait_seconds: int) -> None:
    deadline = time.monotonic() + wait_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            request_json(f"{base_url}/models", timeout=5)
            return
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(2)
    raise RuntimeError(f"server did not become ready within {wait_seconds}s: {last_error}")


def extract_message_text(response: dict) -> str:
    choices = response.get("choices") or []
    if not choices:
        raise ValueError("response has no choices")
    content = choices[0].get("message", {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    raise ValueError(f"unexpected message content: {type(content).__name__}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8099/v1")
    parser.add_argument("--model", default="openbmb/MiniCPM-o-4_5")
    parser.add_argument("--prompt", default="Reply with exactly: ASCEND_SMOKE_OK")
    parser.add_argument("--wait-seconds", type=int, default=300)
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()

    wait_until_ready(args.base_url.rstrip("/"), args.wait_seconds)
    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": [{"type": "text", "text": "Answer briefly."}]},
            {"role": "user", "content": [{"type": "text", "text": args.prompt}]},
        ],
        "modalities": ["text"],
        "chat_template_kwargs": {
            "enable_thinking": False,
            "use_tts_template": False,
        },
        "temperature": 0,
        "max_tokens": 64,
        "stream": False,
    }

    started = time.perf_counter()
    response = request_json(
        f"{args.base_url.rstrip('/')}/chat/completions",
        payload,
        timeout=args.timeout,
    )
    elapsed = time.perf_counter() - started
    text = extract_message_text(response).strip()
    if not text:
        raise RuntimeError("model returned an empty text response")

    print(
        json.dumps(
            {
                "status": "ok",
                "model": args.model,
                "e2e_seconds": round(elapsed, 6),
                "response": text,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
