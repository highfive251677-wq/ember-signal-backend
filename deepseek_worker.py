"""Ask DeepSeek to review one handoff task.

This worker is intentionally report-only by default. It reads the handoff files,
sends them to a DeepSeek OpenAI-compatible endpoint, and prints the response.
It does not edit the repository, database, or production service.

Required environment variables:
  DEEPSEEK_API_KEY
Optional:
  DEEPSEEK_MODEL (default: deepseek-chat)
  DEEPSEEK_API_BASE (default: https://api.deepseek.com/v1)

Usage:
  python deepseek_worker.py --task "Inspect duplicate institution groups"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
HANDOFF_DIR = BASE_DIR / "handoff"


def read_handoff() -> str:
    names = [
        "PROJECT_CONTEXT.md",
        "CURRENT_STATUS.md",
        "TASK_QUEUE.md",
        "RELEASE_CHECKLIST.md",
    ]
    parts = []
    for name in names:
        path = HANDOFF_DIR / name
        parts.append(f"\n--- {name} ---\n{path.read_text(encoding='utf-8')}")
    return "".join(parts)


def call_deepseek(task: str) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set; no request was sent")

    base = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1").rstrip("/")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    system = (
        "You are a report-only project assistant. Read the supplied handoff context. "
        "Do not claim to have changed code, database, or production. Do not access "
        "private or login-gated sources. Return findings, proposed steps, risks, "
        "and exact files/tests to inspect."
    )
    user = f"{read_handoff()}\n\n--- REQUESTED TASK ---\n{task}"
    payload = json.dumps({
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }).encode("utf-8")
    request = Request(
        f"{base}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek HTTP {exc.code}: {detail[:1000]}") from exc
    except URLError as exc:
        raise RuntimeError(f"DeepSeek network error: {exc.reason}") from exc

    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected DeepSeek response: {json.dumps(result)[:2000]}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, help="One report-only task to ask DeepSeek to analyze")
    args = parser.parse_args()
    try:
        print(call_deepseek(args.task))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
