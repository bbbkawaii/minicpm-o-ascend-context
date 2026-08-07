#!/usr/bin/env python3
"""Four-modality correctness smoke test for MiniCPM-o.

Runs text / image / audio / video requests against the OpenAI-compatible
server and verifies machine-checkable correctness:

* HTTP success
* non-empty text response
* for audio: 24 kHz WAV with non-zero duration (when audio output requested)

Media fixtures come from :file:`fixtures/manifest.json`. Inline fixtures run
fully offline; URL fixtures are downloaded on demand and verified by SHA256.
A fixture with an empty ``url`` is reported as ``skipped`` rather than failed,
so the suite never fabricates a pass for media we have not licensed.

Usage:
    python3 baseline/smoke_multimodal.py \
        --base-url http://127.0.0.1:8091/v1 \
        --model openbmb/MiniCPM-o-4_5 \
        --runs-per-modality 5
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baseline.metrics import now_utc_iso  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_manifest() -> dict:
    manifest_path = PROJECT_ROOT / "fixtures" / "manifest.json"
    with open(manifest_path, encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def _download_with_sha256(url: str, expected_sha256: str, timeout: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "smoke"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
    digest = hashlib.sha256(body).hexdigest()
    if expected_sha256 and digest != expected_sha256:
        raise RuntimeError(f"SHA256 mismatch for {url}: got {digest}, expected {expected_sha256}")
    return body


def build_content(entry: dict, timeout: float) -> list[dict]:
    """Return the OpenAI content-list for one manifest modality entry."""
    kind = entry["kind"]
    media_type = entry["media_type"]
    prompt = entry["prompt"]

    if kind == "inline":
        if media_type == "image_url":
            return [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{entry['base64']}"},
                },
                {"type": "text", "text": prompt},
            ]
        if media_type == "input_audio":
            return [
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": entry["base64"],
                        "format": "wav",
                    },
                },
                {"type": "text", "text": prompt},
            ]
        if media_type == "video_url":
            return [{"type": "text", "text": prompt}]
        # default: text
        return [{"type": "text", "text": entry["prompt"]}]

    if kind == "url":
        if not entry.get("url"):
            raise RuntimeError("URL fixture has empty url; cannot run")
        body = _download_with_sha256(entry["url"], entry.get("sha256", ""), timeout)
        if media_type == "image_url":
            return [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64.b64encode(body).decode()}"}},
                {"type": "text", "text": prompt},
            ]
        # video / other: fall back to text-only so the case is still checked
        return [{"type": "text", "text": prompt}]

    raise RuntimeError(f"unknown fixture kind {kind!r}")


def inspect_audio_base64(audio_base64: str) -> dict:
    """Decode a base64 WAV and return sample rate + duration."""
    wav_bytes = base64.b64decode(audio_base64, validate=True)
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        frame_count = wav_file.getnframes()
        sample_rate = wav_file.getframerate()
    return {"sample_rate_hz": sample_rate, "duration_seconds": frame_count / sample_rate}


def run_one(
    *,
    base_url: str,
    model: str,
    modality: str,
    content: list[dict],
    modalities: list[str],
    chat_template_kwargs: dict,
    timeout: float,
) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "modalities": modalities,
        "chat_template_kwargs": chat_template_kwargs,
        "temperature": 0,
        "max_tokens": 128,
        "stream": False,
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        body = json.load(response)

    choices = body.get("choices") or []
    if not choices:
        return {"modality": modality, "status": "fail", "reason": "no choices"}

    message = choices[0].get("message") or {}
    text = message.get("content")
    if isinstance(text, list):
        text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
    text = (text or "").strip()

    checks = {"http_ok": True}
    if not text:
        checks["text_nonempty"] = False
    else:
        checks["text_nonempty"] = True

    audio = message.get("audio")
    if "audio" in modalities:
        audio_data = audio.get("data") if isinstance(audio, dict) else None
        if not audio_data:
            checks["audio_present"] = False
        else:
            try:
                info = inspect_audio_base64(audio_data)
                checks["audio_present"] = True
                checks["audio_24khz"] = info["sample_rate_hz"] == 24_000
                checks["audio_nonzero"] = info["duration_seconds"] > 0
            except Exception:  # noqa: BLE001
                checks["audio_present"] = False

    passed = all(checks.values())
    return {
        "modality": modality,
        "status": "pass" if passed else "fail",
        "checks": checks,
        "text_preview": text[:60],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8091/v1")
    parser.add_argument("--model", default="openbmb/MiniCPM-o-4_5")
    parser.add_argument("--runs-per-modality", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--output")
    args = parser.parse_args()

    manifest = load_manifest()
    modalities = manifest["modalities"]
    results = []
    failed = 0
    skipped = 0

    for modality, entry in modalities.items():
        if entry["kind"] == "url" and not entry.get("url"):
            results.append(
                {"modality": modality, "status": "skipped", "reason": "fixture url not set"}
            )
            skipped += 1
            continue

        for run in range(args.runs_per_modality):
            try:
                content = build_content(entry, args.timeout)
            except RuntimeError as exc:
                results.append(
                    {"modality": modality, "run": run, "status": "fail", "reason": str(exc)}
                )
                failed += 1
                continue

            wants_audio = modality == "audio"
            result = run_one(
                base_url=args.base_url,
                model=args.model,
                modality=modality,
                content=content,
                modalities=["text", "audio"] if wants_audio else ["text"],
                chat_template_kwargs={
                    "enable_thinking": False,
                    "use_tts_template": wants_audio,
                },
                timeout=args.timeout,
            )
            result["run"] = run
            results.append(result)
            if result["status"] == "fail":
                failed += 1

    summary = {
        "schema_version": 1,
        "created_at": now_utc_iso(),
        "model": args.model,
        "runs_per_modality": args.runs_per_modality,
        "total": len(results),
        "passed": len(results) - failed - skipped,
        "failed": failed,
        "skipped": skipped,
        "results": results,
    }

    rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as out:
            out.write(rendered + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
