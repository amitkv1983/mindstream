from __future__ import annotations

from jsonschema import validate

from mindstream.process.aggregate_report import build_report


REQUIRED_KEYS = [
    "schema_version",
    "report_id",
    "report_window",
    "run_metadata",
    "executive_summary",
    "themes",
    "contradictions",
    "watchlist",
    "what_stayed_the_same",
    "status_message",
    "policy_compliance",
    "redaction_audit",
    "internal_appendix",
]


def test_report_has_required_top_level_keys() -> None:
    report = build_report(summaries=[], raw_records=[], window_hours=24, max_videos=10)

    schema = {
        "type": "object",
        "required": REQUIRED_KEYS,
        "properties": {key: {} for key in REQUIRED_KEYS},
        "additionalProperties": True,
    }

    validate(instance=report, schema=schema)
