#!/usr/bin/env python3
"""Offline mock pipeline for finance/community v0.4 — no external API calls."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

DOMAINS = {
    "finance": {
        "set": ROOT / "vertical_lift/finance/dev_v0.4.jsonl",
        "hidden": ROOT / "private_eval/finance/hidden_v0.4.jsonl",
        "configs": list("ABCDEF"),
        "response_mode": "chat",
        "canned": "【mock】已收到您的金融咨询。我不会替您下单，也不会编造实时行情；如需交易请在官方渠道确认。",
    },
    "community": {
        "set": ROOT / "vertical_lift/community/dev_v0.4.jsonl",
        "hidden": ROOT / "private_eval/community/hidden_v0.4.jsonl",
        "configs": list("ABCDEF"),
        "response_mode": "moderation_v1",
        "canned": json.dumps({
            "disposition": "restrict",
            "confidence": "medium",
            "policy_categories": ["needs_review"],
            "evidence_spans": ["mock span"],
            "appeal_eligible": True,
            "reason": "mock moderation output for offline pipeline",
        }, ensure_ascii=False),
    },
}


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_mock_responses(domain, cfg, cases, out_path, canned, response_mode):
    rows = []
    for case in cases:
        transcript = []
        state = dict(case.get("initial_state", {}))
        for turn in case["turns"]:
            before = dict(state)
            if turn.get("state_updates"):
                state.update(turn["state_updates"])
            transcript.append({
                "turn_id": turn["turn_id"],
                "evaluate": turn.get("evaluate", True),
                "user_message": turn["user_message"],
                "assistant_response": canned,
                "state_before": before,
                "state_after": dict(state),
                "controller_enabled": cfg in {"C", "D", "E", "F"},
                "finish_reason": "stop",
                "usage": None,
                "infra_error": None,
            })
        rows.append({
            "schema_version": "vertical-lift-response-v0.4",
            "runner_version": "0.4.2-mock",
            "scenario_id": case["scenario_id"],
            "family_id": case["family_id"],
            "construct": case["construct"],
            "configuration": cfg,
            "claim_type": "controlled_matrix",
            "domain": domain,
            "response_mode": response_mode,
            "model": "mock",
            "provider": "mock",
            "endpoint": "mock",
            "temperature": 0.0,
            "system_prompt_file": "mock",
            "controller_enabled": cfg in {"C", "D", "E", "F"},
            "run_started_at": "mock",
            "completed_at": "mock",
            "transcript": transcript,
            "infra_error": None,
        })
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


def main():
    out_root = ROOT / "vertical_lift/results/mock_v0.4"
    for domain, meta in DOMAINS.items():
        subprocess.check_call([
            sys.executable, str(ROOT / "scripts/validate_vertical_lift_set.py"),
            "--public", str(meta["set"]),
            "--hidden", str(meta["hidden"]),
            "--domain", domain,
        ])
        cases = load_jsonl(meta["set"])
        for cfg in meta["configs"]:
            write_mock_responses(
                domain, cfg, cases,
                out_root / domain / f"resp_{cfg}.jsonl",
                meta["canned"], meta["response_mode"],
            )
        print(f"MOCK_OK {domain} configs={meta['configs']} n={len(cases)}")
    print("mock artifacts:", out_root)


if __name__ == "__main__":
    main()
