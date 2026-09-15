"""Bounded Mistral API demo for Ember Signal.

One mode runs per invocation so the script does not fan out or waste tokens.
It never edits the database, repository data, or production.

Examples:
  python mistral_api_demo.py models
  python mistral_api_demo.py chat --text "Explain public-source evidence in one sentence"
  python mistral_api_demo.py extract --text "A 2026 intake opens for a data course" \
      --model mistral-small-latest
  python mistral_api_demo.py translate --text "သင်တန်းသစ် စတင်မည်"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://api.mistral.ai/v1"
DEFAULT_MODEL = "mistral-small-latest"


def request_json(method: str, path: str, payload: dict | None = None) -> dict:
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        raise RuntimeError("MISTRAL_API_KEY is not configured")
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        BASE_URL + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Mistral HTTP {exc.code}: {detail[:800]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Mistral network error: {exc.reason}") from exc


def text_from_chat(result: dict) -> str:
    content = result["choices"][0]["message"]["content"]
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content)
    return str(content)


def models() -> None:
    result = request_json("GET", "/models")
    rows = result.get("data", result if isinstance(result, list) else [])
    print(json.dumps([
        {"id": row.get("id"), "chat": row.get("capabilities", {}).get("completion_chat"),
         "json": row.get("capabilities", {}).get("structured_output"),
         "context": row.get("max_context_length")}
        for row in rows[:20]
    ], ensure_ascii=False, indent=2))


def chat(text: str, model: str) -> None:
    result = request_json("POST", "/chat/completions", {
        "model": model,
        "temperature": 0.1,
        "max_tokens": 120,
        "messages": [{"role": "user", "content": text}],
    })
    print(json.dumps({"model": result.get("model"), "answer": text_from_chat(result), "usage": result.get("usage")}, ensure_ascii=False, indent=2))


def extract(text: str, model: str) -> None:
    schema = {
        "type": "object",
        "properties": {
            "signal_type": {"type": "string", "enum": ["admissions", "course", "event", "campaign", "partnership", "other"]},
            "summary": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["signal_type", "summary", "confidence"],
        "additionalProperties": False,
    }
    result = request_json("POST", "/chat/completions", {
        "model": model,
        "temperature": 0,
        "max_tokens": 180,
        "messages": [{"role": "system", "content": "Return only valid JSON matching the schema."}, {"role": "user", "content": text}],
        "response_format": {"type": "json_schema", "json_schema": {"name": "ember_signal", "schema": schema}},
    })
    raw = text_from_chat(result)
    print(json.dumps({"model": result.get("model"), "extracted": json.loads(raw), "usage": result.get("usage")}, ensure_ascii=False, indent=2))


def translate(text: str, model: str) -> None:
    result = request_json("POST", "/chat/completions", {
        "model": model,
        "temperature": 0.1,
        "max_tokens": 160,
        "messages": [{"role": "system", "content": "Translate the supplied text into clear English. Return only the translation."}, {"role": "user", "content": text}],
    })
    print(json.dumps({"model": result.get("model"), "translation": text_from_chat(result), "usage": result.get("usage")}, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["models", "chat", "extract", "translate"])
    parser.add_argument("--text", default="", help="Text for chat, extraction, or translation")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    if args.mode != "models" and not args.text:
        parser.error("--text is required for this mode")
    try:
        {"models": models, "chat": lambda: chat(args.text, args.model), "extract": lambda: extract(args.text, args.model), "translate": lambda: translate(args.text, args.model)}[args.mode]()
    except (RuntimeError, json.JSONDecodeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
