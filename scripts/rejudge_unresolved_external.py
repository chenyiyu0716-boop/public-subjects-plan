#!/usr/bin/env python3
"""用显式指定的第二裁判只补判 baseline 中的 unresolved 项。"""
import argparse
import json

import eval_harness as harness


def id_of(row):
    return row.get("case_id") or row.get("probe_id") or row.get("scenario_id")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True)
    ap.add_argument("--responses", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--protocol", choices=("openai", "anthropic"), default="openai")
    args = ap.parse_args()

    cases = {id_of(x): x for x in harness.load_set(args.set)}
    responses = {id_of(x): x for x in harness.load_set(args.responses)}
    with open(args.baseline, encoding="utf-8") as f:
        data = json.load(f)

    harness.JUDGE_EXTERNAL_CFG.update({
        "endpoint": args.endpoint,
        "api_key": args.key,
        "model": args.model,
    })

    attempted = resolved = 0
    for item in data.get("results", []):
        if item.get("evaluation_status") == "valid":
            item.setdefault("judge_model_item", data.get("judge_model"))
            continue
        if item.get("evaluation_status") != "judge_unresolved":
            continue
        cid = item.get("case_id")
        case = cases.get(cid)
        response = responses.get(cid)
        if not case or not response or not str(response.get("response_text", "")).strip():
            continue
        attempted += 1
        prompt = harness._build_judge_prompt(case, response["response_text"])
        if args.protocol == "anthropic":
            out = harness.call_anthropic_judge(
                args.endpoint, args.key, args.model, prompt)
        else:
            out, _ = harness.judge_case(case, response["response_text"], None)
        out = harness._normalize_judge_output(out)
        if not harness._valid_judge_output(out):
            item["fallback_judge_error"] = (out or {}).get("judge_parse_error") or \
                                           "fallback judge schema validation failed"
            item["fallback_judge_raw"] = out
            continue
        item.update({
            "evaluation_status": "valid",
            "judge_hard_fail": out["hard_fail"],
            "judge_expected_score": out["expected_score"],
            "judge_overall_pass": out["overall_pass"],
            "judge_hit_tags": out["hit_tags"],
            "judge_missing_expectations": out["missing_expectations"],
            "judge_reason": out["reason"],
            "judge_parse_error": None,
            "judge_model_item": args.model,
            "judge_provenance": f"fallback_unresolved_only_{args.protocol}",
            "judge_normalization_note": out.get("normalization_note"),
        })
        resolved += 1

    valid_items = [x for x in data.get("results", []) if x.get("evaluation_status") == "valid"]
    data["valid"] = len(valid_items)
    data["judge_unresolved"] = sum(
        x.get("evaluation_status") == "judge_unresolved" for x in data.get("results", []))
    data["auto_passed"] = sum(bool(x.get("judge_overall_pass")) for x in valid_items)
    data["auto_failed"] = sum(not bool(x.get("judge_overall_pass")) for x in valid_items)
    data["judge_failed"] = sum(bool(x.get("judge_hard_fail")) for x in valid_items)
    data["judge_fail_rate"] = (round(data["judge_failed"] / len(valid_items), 3)
                               if valid_items else None)
    data["judge_models"] = sorted({
        x.get("judge_model_item") for x in valid_items if x.get("judge_model_item")})
    data["mixed_judge"] = len(data["judge_models"]) > 1
    data["fallback_judge_model"] = args.model
    data["fallback_attempted"] = attempted
    data["fallback_resolved"] = resolved

    with open(args.baseline, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(args.baseline, "attempted", attempted, "resolved", resolved,
          "remaining", data["judge_unresolved"])


if __name__ == "__main__":
    main()
