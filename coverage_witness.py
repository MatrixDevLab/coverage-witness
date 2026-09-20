#!/usr/bin/env python3
"""Deterministically reconcile a requested-file manifest with read events.

This tool witnesses task-local coverage only.  It does not infer that a read
was genuine, that the contents were understood, or that a review found no
defects.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import sys
from typing import Any


QUALIFYING_EVENT_KIND = "file_read"


def _normalise_path(value: Any) -> tuple[str | None, str | None]:
    if not isinstance(value, str):
        return None, "path_not_string"
    if not value:
        return None, "path_empty"
    if "\x00" in value:
        return None, "path_contains_nul"
    # Backslash is rejected rather than guessed at, so a Windows path cannot
    # silently alias a POSIX path on another machine.
    if "\\" in value:
        return None, "path_contains_backslash"
    if value.startswith("/"):
        return None, "path_absolute"
    path = posixpath.normpath(value)
    if path in ("", ".") or path == ".." or path.startswith("../"):
        return None, "path_escapes_root"
    return path, None


def _issue(code: str, location: str, path: str | None = None) -> dict[str, str]:
    result = {"code": code, "location": location}
    if path is not None:
        result["path"] = path
    return result


def _manifest_entries(raw: Any) -> tuple[list[str], list[dict[str, str]]]:
    if not isinstance(raw, list):
        return [], [_issue("manifest_not_list", "manifest")]
    paths: list[str] = []
    issues: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, entry in enumerate(raw):
        location = f"manifest[{index}]"
        value = entry.get("path") if isinstance(entry, dict) else entry
        path, error = _normalise_path(value)
        if error:
            issues.append(_issue(error, location))
            continue
        assert path is not None
        if path in seen:
            issues.append(_issue("duplicate_manifest_path", location, path))
            continue
        seen.add(path)
        paths.append(path)
    return paths, issues


def _claim_info(raw: Any, manifest: set[str]) -> tuple[str | None, list[dict[str, str]]]:
    if not isinstance(raw, dict):
        return None, [_issue("claim_not_object", "claim")]
    status = raw.get("status")
    if status not in {"complete", "partial", "unknown"}:
        return None, [_issue("claim_status_unknown", "claim.status")]
    issues: list[dict[str, str]] = []
    if "paths" in raw:
        if not isinstance(raw["paths"], list):
            issues.append(_issue("claim_paths_not_list", "claim.paths"))
        else:
            for index, value in enumerate(raw["paths"]):
                path, error = _normalise_path(value)
                if error:
                    issues.append(_issue(error, f"claim.paths[{index}]"))
                elif path not in manifest:
                    issues.append(_issue("claim_exceeds_manifest", f"claim.paths[{index}]", path))
    return status, issues


def reconcile(document: Any) -> dict[str, Any]:
    """Return a stable, JSON-serialisable reconciliation result."""

    if not isinstance(document, dict):
        return {
            "schema": 1,
            "verdict": "unknown",
            "claim_status": None,
            "coverage": [],
            "unknown": [_issue("input_not_object", "input")],
            "event_counts": {"qualifying": 0, "non_qualifying": 0},
        }

    paths, manifest_issues = _manifest_entries(document.get("manifest"))
    manifest_set = set(paths)
    claim_status, claim_issues = _claim_info(document.get("claim"), manifest_set)
    issues: list[dict[str, str]] = [*manifest_issues, *claim_issues]
    events = document.get("events")
    if not isinstance(events, list):
        issues.append(_issue("events_not_list", "events"))
        events = []

    observed: dict[str, list[int]] = {path: [] for path in paths}
    event_unknown: dict[str, list[str]] = {path: [] for path in paths}
    counts = {"qualifying": 0, "non_qualifying": 0}
    for index, event in enumerate(events):
        location = f"events[{index}]"
        if not isinstance(event, dict):
            issues.append(_issue("event_not_object", location))
            continue
        kind = event.get("kind")
        if not isinstance(kind, str):
            issues.append(_issue("event_kind_unknown", f"{location}.kind"))
            continue
        path, error = _normalise_path(event.get("path"))
        if error:
            if kind == QUALIFYING_EVENT_KIND:
                issues.append(_issue(error, f"{location}.path"))
            else:
                counts["non_qualifying"] += 1
            continue
        assert path is not None
        if kind != QUALIFYING_EVENT_KIND:
            counts["non_qualifying"] += 1
            continue
        counts["qualifying"] += 1
        if path in observed:
            observed[path].append(index)
        elif path in manifest_set:
            event_unknown[path].append("unreachable_manifest_path")

    coverage: list[dict[str, Any]] = []
    for path in paths:
        if event_unknown[path]:
            status = "unknown"
        elif observed[path]:
            status = "covered"
        else:
            status = "missing"
        coverage.append(
            {
                "path": path,
                "status": status,
                "observed_event_indexes": observed[path],
                "unknown_reasons": event_unknown[path],
            }
        )

    if issues or any(item["status"] == "unknown" for item in coverage):
        verdict = "unknown"
    elif any(item["status"] == "missing" for item in coverage):
        verdict = "missing"
    elif not paths:
        verdict = "unknown"
    elif claim_status != "complete":
        verdict = "unknown"
    else:
        verdict = "covered"

    return {
        "schema": 1,
        "verdict": verdict,
        "claim_status": claim_status,
        "coverage": coverage,
        "unknown": issues,
        "event_counts": counts,
    }


def _render_text(result: dict[str, Any]) -> str:
    lines = [
        f"verdict: {result['verdict']}",
        f"claim: {result['claim_status'] or 'unknown'} (claim is not coverage evidence)",
    ]
    for item in result["coverage"]:
        indexes = ",".join(str(index) for index in item["observed_event_indexes"]) or "-"
        lines.append(f"{item['status']}: {item['path']} (event indexes: {indexes})")
    for issue in result["unknown"]:
        suffix = f" [{issue['path']}]" if "path" in issue else ""
        lines.append(f"unknown: {issue['code']} at {issue['location']}{suffix}")
    return "\n".join(lines)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--input", help="JSON input file; stdin is used when omitted")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    try:
        if args.input:
            with open(args.input, encoding="utf-8") as handle:
                document = json.load(handle)
        else:
            document = json.load(sys.stdin)
    except (OSError, json.JSONDecodeError) as error:
        result = {
            "schema": 1,
            "verdict": "unknown",
            "claim_status": None,
            "coverage": [],
            "unknown": [_issue("input_json_invalid", "input")],
            "event_counts": {"qualifying": 0, "non_qualifying": 0},
        }
        if args.format == "text":
            print(_render_text(result))
        else:
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        print(f"coverage-witness: {error}", file=sys.stderr)
        return 2

    result = reconcile(document)
    if args.format == "text":
        print(_render_text(result))
    else:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return {"covered": 0, "missing": 1, "unknown": 2}[result["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
