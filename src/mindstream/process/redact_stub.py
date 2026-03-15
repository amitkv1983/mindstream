from __future__ import annotations

import copy
import re
from typing import Any

HANDLE_PATTERN = re.compile(r"@[A-Za-z0-9_.-]+")
PROFILE_LINK_PATTERN = re.compile(
    r"https?://(?:www\.)?youtube\.com/(?:@[A-Za-z0-9_.-]+|channel/[A-Za-z0-9_-]+)[^\s]*",
    flags=re.IGNORECASE,
)
CTA_PATTERN = re.compile(
    r"\b(subscribe to|follow)\s+([A-Za-z][A-Za-z0-9 ._-]{1,50})",
    flags=re.IGNORECASE,
)


def redact_text(text: str) -> tuple[str, int]:
    updated = text
    replacements = 0

    updated, n = PROFILE_LINK_PATTERN.subn("[REDACTED_PROFILE_LINK]", updated)
    replacements += n

    updated, n = HANDLE_PATTERN.subn("[REDACTED_HANDLE]", updated)
    replacements += n

    def _cta_repl(match: re.Match[str]) -> str:
        verb = match.group(1).lower()
        return f"{verb} [REDACTED_NAME]"

    updated, n = CTA_PATTERN.subn(_cta_repl, updated)
    replacements += n

    return updated, replacements


def _walk_and_redact(value: Any) -> tuple[Any, int]:
    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, list):
        total = 0
        new_list = []
        for item in value:
            redacted, count = _walk_and_redact(item)
            new_list.append(redacted)
            total += count
        return new_list, total

    if isinstance(value, dict):
        total = 0
        new_dict = {}
        for k, v in value.items():
            redacted, count = _walk_and_redact(v)
            new_dict[k] = redacted
            total += count
        return new_dict, total

    return value, 0


def redact_report(report: dict) -> tuple[dict, dict]:
    report_copy = copy.deepcopy(report)
    try:
        redacted_report, replacement_count = _walk_and_redact(report_copy)
        audit = {
            "overall_status": "WARN" if replacement_count > 0 else "PASS",
            "sanitized": replacement_count > 0,
            "replacement_count": replacement_count,
        }
        redacted_report["redaction_audit"] = audit
        return redacted_report, audit
    except Exception as exc:
        audit = {
            "overall_status": "FAIL",
            "sanitized": False,
            "replacement_count": 0,
            "error": str(exc),
        }
        report_copy["redaction_audit"] = audit
        return report_copy, audit
