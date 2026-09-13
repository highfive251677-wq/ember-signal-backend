"""Validate report-only worker envelopes and enforce release gates.

Usage:
  python supervisor.py report.json

The supervisor never modifies code, data, or production. It only validates a
JSON report and returns a non-zero exit code when the report is not releasable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = {"task_id", "provider", "model", "mode", "status", "claims", "findings", "risks", "next_actions", "confidence"}
VALID = {"PASS", "FAIL", "INCOMPLETE", "BLOCKED"}


def validate(item: dict) -> list[str]:
    errors = []
    missing = REQUIRED - item.keys()
    if missing:
        errors.append(f"missing required fields: {sorted(missing)}")
    if item.get("mode") != "report-only":
        errors.append("mode must be report-only")
    if item.get("status") not in VALID:
        errors.append("status must be PASS, FAIL, INCOMPLETE, or BLOCKED")
    if not isinstance(item.get("claims"), list):
        errors.append("claims must be a list")
    else:
        for i, claim in enumerate(item["claims"]):
            if not isinstance(claim, dict) or not claim.get("claim") or not claim.get("evidence"):
                errors.append(f"claim {i} lacks claim text or evidence")
    confidence = item.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append("confidence must be between 0 and 1")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python supervisor.py report.json", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"BLOCKED: cannot read report: {exc}")
        return 1
    items = data if isinstance(data, list) else [data]
    all_errors = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            all_errors.append(f"item {i} is not an object")
            continue
        all_errors.extend(f"item {i}: {e}" for e in validate(item))
    if all_errors:
        print("FAIL: KPI envelope validation failed")
        for error in all_errors:
            print(f"- {error}")
        return 1
    statuses = {item["status"] for item in items}
    if "BLOCKED" in statuses or "FAIL" in statuses or "INCOMPLETE" in statuses:
        print(f"BLOCKED: worker statuses require review: {sorted(statuses)}")
        return 1
    if len({item["provider"] for item in items}) < 2:
        print("BLOCKED: release decisions require independent cross-review")
        return 1
    print("PASS: report envelope and independent-provider KPI checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
