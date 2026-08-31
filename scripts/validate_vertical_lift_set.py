#!/usr/bin/env python3
"""Validate v0.4 Vertical Lift JSONL sets and build a non-revealing hidden manifest."""

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


REQUIRED = {
    "scenario_id", "schema_version", "domain", "track", "construct",
    "family_id", "variant_type", "risk_tier", "turns",
    "prohibited_behaviors", "expected_behaviors", "hard_fail_tags",
    "quality_rubric", "authority_refs",
}
VARIANTS = {"canonical", "boundary", "adversarial", "composite", "multiturn"}
RISKS = {"low", "medium", "high", "critical"}
OPS = {"eq", "in", "not_contains", "lte", "gte"}
ID_PATTERN = re.compile(r"^VL-[A-Z]+-[0-9]{3}$")


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            rows.append(row)
    return rows


def require_string_list(row, field):
    value = row.get(field)
    if not isinstance(value, list) or not value or not all(
            isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{row.get('scenario_id')}: {field} must be a non-empty string list")


def validate_row(row):
    scenario_id = row.get("scenario_id", "<missing-id>")
    missing = REQUIRED - set(row)
    if missing:
        raise ValueError(f"{scenario_id}: missing fields {sorted(missing)}")
    if not ID_PATTERN.match(scenario_id):
        raise ValueError(f"{scenario_id}: invalid scenario_id")
    if row["schema_version"] != "vertical-lift-case-v0.4":
        raise ValueError(f"{scenario_id}: wrong schema_version")
    if row["variant_type"] not in VARIANTS or row["risk_tier"] not in RISKS:
        raise ValueError(f"{scenario_id}: invalid variant_type or risk_tier")
    for field in ("prohibited_behaviors", "expected_behaviors", "hard_fail_tags",
                  "authority_refs"):
        require_string_list(row, field)

    turns = row["turns"]
    if not isinstance(turns, list) or not turns:
        raise ValueError(f"{scenario_id}: turns must be non-empty")
    expected_turn_ids = list(range(1, len(turns) + 1))
    actual_turn_ids = [turn.get("turn_id") for turn in turns]
    if actual_turn_ids != expected_turn_ids:
        raise ValueError(f"{scenario_id}: turn_id must be consecutive from 1")
    if not any(turn.get("evaluate") is True for turn in turns):
        raise ValueError(f"{scenario_id}: at least one turn must be evaluated")
    for turn in turns:
        if not isinstance(turn.get("user_message"), str) or not turn["user_message"].strip():
            raise ValueError(f"{scenario_id}: empty user_message")
        if not isinstance(turn.get("evaluate"), bool):
            raise ValueError(f"{scenario_id}: evaluate must be boolean")

    rubric = row["quality_rubric"]
    if not isinstance(rubric, dict) or not rubric:
        raise ValueError(f"{scenario_id}: quality_rubric must be non-empty")
    for axis, anchors in rubric.items():
        if not isinstance(anchors, dict) or not {"0", "3"}.issubset(anchors):
            raise ValueError(f"{scenario_id}: rubric {axis} needs 0 and 3 anchors")

    for assertion in row.get("state_assertions", []):
        if assertion.get("at_turn") not in expected_turn_ids:
            raise ValueError(f"{scenario_id}: assertion references missing turn")
        if assertion.get("op") not in OPS or not assertion.get("path"):
            raise ValueError(f"{scenario_id}: invalid state assertion")


def summarize(rows):
    return {
        "count": len(rows),
        "construct_counts": dict(sorted(Counter(r["construct"] for r in rows).items())),
        "variant_counts": dict(sorted(Counter(r["variant_type"] for r in rows).items())),
        "risk_counts": dict(sorted(Counter(r["risk_tier"] for r in rows).items())),
        "family_count": len({r["family_id"] for r in rows}),
        "multiturn_count": sum(len(r["turns"]) > 1 for r in rows),
    }


DOMAIN_PREFIX = {
    "companion": "VL-CMP",
    "finance": "VL-FIN",
    "community": "VL-COM",
}


def infer_domain(rows):
    domains = {row["domain"] for row in rows}
    if len(domains) != 1:
        raise ValueError(f"mixed domains in set: {domains}")
    return domains.pop()


def validate_collection(public_rows, hidden_rows=None, domain=None):
    all_rows = list(public_rows) + list(hidden_rows or [])
    ids = [row["scenario_id"] for row in all_rows]
    if len(ids) != len(set(ids)):
        duplicates = [item for item, count in Counter(ids).items() if count > 1]
        raise ValueError(f"duplicate scenario IDs: {duplicates}")
    for row in all_rows:
        validate_row(row)

    domain = domain or infer_domain(all_rows)
    prefix = DOMAIN_PREFIX.get(domain)
    if not prefix or not all(row["scenario_id"].startswith(prefix) for row in all_rows):
        raise ValueError(f"scenario_id prefix mismatch for domain {domain}")

    if hidden_rows is not None:
        if len(public_rows) != 12 or len(hidden_rows) != 18 or len(all_rows) != 30:
            raise ValueError(f"{domain} MVP requires 12 public + 18 hidden = 30 scenarios")
        by_construct = defaultdict(list)
        for row in all_rows:
            by_construct[row["construct"]].append(row)
        if sorted(len(rows) for rows in by_construct.values()) != [10, 10, 10]:
            raise ValueError(f"{domain} MVP requires 10 scenarios per construct")
        if any(len({r["family_id"] for r in rows}) != 4 for rows in by_construct.values()):
            raise ValueError(f"{domain} MVP requires four families per construct")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", required=True)
    parser.add_argument("--hidden")
    parser.add_argument("--manifest-out")
    parser.add_argument("--domain", choices=sorted(DOMAIN_PREFIX))
    args = parser.parse_args()

    public_rows = load_jsonl(args.public)
    hidden_rows = load_jsonl(args.hidden) if args.hidden else None
    domain = args.domain or (infer_domain(public_rows + (hidden_rows or [])) if public_rows else None)
    validate_collection(public_rows, hidden_rows, domain=domain)

    output = {"public": summarize(public_rows)}
    if hidden_rows is not None:
        hidden_path = Path(args.hidden)
        output["hidden"] = summarize(hidden_rows)
        output["hidden"]["sha256"] = hashlib.sha256(hidden_path.read_bytes()).hexdigest()
        output["combined"] = summarize(public_rows + hidden_rows)
    print(json.dumps(output, ensure_ascii=False, indent=2))

    if args.manifest_out:
        if hidden_rows is None:
            raise ValueError("--manifest-out requires --hidden")
        manifest = {
            "schema_version": "vertical-lift-hidden-manifest-v0.4",
            "domain": domain,
            "active": True,
            "content_published": False,
            "hidden": output["hidden"],
            "combined": output["combined"],
            "leakage_policy": "Active hidden prompts must not enter Git, model prompts, training data, or manual tuning.",
        }
        with open(args.manifest_out, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
            handle.write("\n")


if __name__ == "__main__":
    main()

