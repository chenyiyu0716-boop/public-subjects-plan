#!/usr/bin/env python3
"""Summarize finance/community public generation (no LLM judge)."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize_file(path: Path, mode: str) -> dict:
    rows = load_jsonl(path)
    cfg = path.stem.replace("resp_", "")
    valid = 0
    failures: list[str] = []
    claim_types = Counter()
    for row in rows:
        claim_types[row.get("claim_type", "?")] += 1
        if row.get("infra_error"):
            failures.append(f"{row['scenario_id']}:infra:{row['infra_error'][:120]}")
            continue
        ok = True
        for turn in row.get("transcript", []):
            text = (turn.get("assistant_response") or "").strip()
            if not text:
                ok = False
                failures.append(f"{row['scenario_id']}:{turn['turn_id']}:empty")
            elif "INTERNAL PRODUCT STATE" in text or "AUTHORITATIVE TOOL FIXTURES" in text:
                ok = False
                failures.append(f"{row['scenario_id']}:{turn['turn_id']}:state_leak")
            elif mode == "moderation_v1":
                try:
                    obj = json.loads(text)
                    for key in ("disposition", "confidence", "reason"):
                        if key not in obj:
                            ok = False
                            failures.append(f"{row['scenario_id']}:{turn['turn_id']}:missing_{key}")
                except json.JSONDecodeError:
                    ok = False
                    failures.append(f"{row['scenario_id']}:{turn['turn_id']}:invalid_moderation_json")
        if ok:
            valid += 1
    return {
        "file": str(path),
        "configuration": cfg,
        "scenario_count": len(rows),
        "valid_scenarios": valid,
        "claim_types": dict(claim_types),
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--workdir", type=Path, default=None, help="cloud workdir with logs/")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    fin_dir = args.repo_root / "vertical_lift/results/public_v0.4_finance/responses"
    com_dir = args.repo_root / "vertical_lift/results/public_v0.4_community/responses"
    arms = {
        "finance": (fin_dir, "chat", ["A", "B", "C", "D", "E", "F", "Fg"]),
        "community": (com_dir, "moderation_v1", ["A", "B", "C", "D", "E", "F", "Gg"]),
    }
    per_arm = []
    total_valid = 0
    total_scenarios = 0
    all_failures: list[str] = []
    for domain, (resp_dir, mode, configs) in arms.items():
        for cfg in configs:
            path = resp_dir / f"resp_{cfg}.jsonl"
            if not path.exists():
                all_failures.append(f"missing:{path}")
                continue
            summary = summarize_file(path, mode)
            summary["domain"] = domain
            per_arm.append(summary)
            total_valid += summary["valid_scenarios"]
            total_scenarios += summary["scenario_count"]
            all_failures.extend(summary["failures"])

    provenance: dict = {}
    if args.workdir:
        work = args.workdir
        for name in (
            "env_boot_fc.txt",
            "fingpt_merge_provenance.json",
            "hash_Qwen2-7B-Instruct.json",
            "git_head_fc.txt",
            "fc_public_run.log",
        ):
            p = work / "logs" / name
            if p.exists():
                provenance[name] = p.read_text(encoding="utf-8")[:8000]

    report = {
        "schema_version": "vertical-lift-fc-generation-report-v0.4",
        "status": "generation_only_no_judge",
        "total_scenarios_expected": 168,
        "total_scenarios_loaded": total_scenarios,
        "total_valid_scenarios": total_valid,
        "per_arm": per_arm,
        "failures": all_failures,
        "observed_external_labels": {
            "Fg": "observed_external_lift_only",
            "Gg": "observed_specialized_guard_only",
        },
        "provenance_snippets": provenance,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "valid": total_valid,
        "loaded": total_scenarios,
        "failures": len(all_failures),
        "out": str(args.out),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
