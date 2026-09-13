"""Demonstrate task routing across DeepSeek, Gemini, and OpenAI.

This is report-only: it reads project handoff context, sends three small
independent analysis requests, and writes responses to a local output file.
It never edits code, data, or production.
"""
from __future__ import annotations

import json
import os
import argparse
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
CONTEXT = "\n\n".join((BASE / "handoff" / n).read_text(encoding="utf-8") for n in [
    "PROJECT_CONTEXT.md", "CURRENT_STATUS.md", "TASK_QUEUE.md"
])
BUDGET = json.loads((BASE / "model_budget.json").read_text(encoding="utf-8"))


def post_json(url: str, headers: dict[str, str], payload: dict) -> dict:
    req = Request(url, data=json.dumps(payload).encode(), headers={**headers, "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=90) as response:
            return json.loads(response.read().decode())
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"network error: {exc.reason}") from exc


def compact_context() -> str:
    """Send only the stable status summary, not the full repository."""
    return "Project: Myanmar college public-source intelligence. Baseline: 357 institutions, 69 sources, 41 evidence, 28 duplicate groups, 41 unreviewed evidence. Release is blocked until quality review passes."


def limit(task: str) -> int:
    return BUDGET["tasks"][task]["max_output_tokens"]


def deepseek() -> str:
    prompt = """Act as the technical auditor. Inspect the supplied project handoff context and return a report-only plan for investigating the 28 duplicate institution groups. Do not modify code or data. Include queries/files to inspect, safety risks, and acceptance criteria."""
    result = post_json("https://api.deepseek.com/v1/chat/completions", {
        "Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}"
    }, {"model": "deepseek-chat", "temperature": 0.1, "max_tokens": limit("technical_audit"), "messages": [
        {"role": "system", "content": "You are a report-only technical auditor."},
        {"role": "user", "content": f"{compact_context()}\n\n{prompt}"},
    ]})
    return result["choices"][0]["message"]["content"]


def gemini() -> str:
    prompt = """Act as the data-classification specialist. From the supplied context, define a compact JSON schema for reviewing evidence records, with allowed review_status values and rules for approved, rejected, and source_review_required. Return JSON only. Do not modify anything."""
    result = post_json("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent", {
        "x-goog-api-key": os.environ["GEMINI_API_KEY"]
    }, {"contents": [{"parts": [{"text": f"{compact_context()}\n\n{prompt}"}]}], "generationConfig": {"temperature": 0.1, "maxOutputTokens": limit("evidence_schema"), "responseMimeType": "application/json"}})
    return result["candidates"][0]["content"]["parts"][0]["text"]


def openai() -> str:
    prompt = """Act as the independent release reviewer. Based only on the supplied context, return PASS, FAIL, or BLOCKED for adding a new source batch. Give three evidence-based reasons and the exact conditions needed to change the verdict. Do not modify or deploy anything."""
    result = post_json("https://api.openai.com/v1/responses", {
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
    }, {"model": "gpt-4o-mini", "input": f"{compact_context()}\n\n{prompt}", "temperature": 0.1, "max_output_tokens": limit("release_review")})
    return result.get("output_text", json.dumps(result))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run exactly one bounded model task.")
    parser.add_argument("--task", choices=["technical_audit", "evidence_schema", "release_review"], required=True)
    args = parser.parse_args()
    jobs = {
        "technical_audit": ("DeepSeek — technical audit", deepseek),
        "evidence_schema": ("Gemini — evidence schema", gemini),
        "release_review": ("OpenAI — release gate", openai),
    }
    label, fn = jobs[args.task]
    try:
        output = [{"task": args.task, "worker": label, "status": "ok", "report": fn(), "pause_after_task": True}]
    except Exception as exc:
        output = [{"task": args.task, "worker": label, "status": "error", "error": str(exc), "pause_after_task": True}]
    path = Path("/tmp/ember-signal-multi-model-demo.json")
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in output:
        print(f"\n=== {item['worker']} [{item['status']}] ===")
        print(item.get("report", item.get("error", ""))[:4000])
    print(f"\nSaved full report to {path}")
    print("BUDGET_PAUSED: one task completed; no next task was started")


if __name__ == "__main__":
    main()
