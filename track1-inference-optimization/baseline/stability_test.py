#!/usr/bin/env python3
"""Run repeated text-only requests and save machine-readable stability data."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from baseline.smoke_test import extract_message_text, request_json


def run_once(base_url: str, model: str, prompt: str, timeout: float) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        "modalities": ["text"],
        "chat_template_kwargs": {"enable_thinking": False, "use_tts_template": False},
        "temperature": 0,
        "max_tokens": 64,
        "stream": False,
    }
    started = time.perf_counter()
    response = request_json(
        f"{base_url.rstrip('/')}/chat/completions", payload, timeout=timeout
    )
    elapsed = time.perf_counter() - started
    text = extract_message_text(response).strip()
    if not text:
        raise ValueError("empty response")
    return {"ok": True, "e2e_seconds": round(elapsed, 6), "response_chars": len(text)}


def run_stability(
    base_url: str, model: str, prompt: str, requests: int, timeout: float
) -> dict:
    results = []
    for request_id in range(requests):
        try:
            result = run_once(base_url, model, prompt, timeout)
        except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as exc:
            result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        result["request_id"] = request_id
        results.append(result)
    successful = [result for result in results if result["ok"]]
    return {
        "requests": requests,
        "successes": len(successful),
        "failures": requests - len(successful),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8099/v1")
    parser.add_argument("--model", default="openbmb/MiniCPM-o-4_5")
    parser.add_argument("--prompt", default="Reply with exactly: ASCEND_STABILITY_OK")
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.requests < 1:
        parser.error("--requests must be positive")
    summary = run_stability(
        args.base_url, args.model, args.prompt, args.requests, args.timeout
    )
    rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if summary["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
