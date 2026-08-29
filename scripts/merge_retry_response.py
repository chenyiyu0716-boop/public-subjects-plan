#!/usr/bin/env python3
"""按 case_id 将单条重试结果替换回完整 responses JSONL，并保存被替换记录。"""
import argparse
import json


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", required=True)
    ap.add_argument("--retry", required=True)
    ap.add_argument("--replaced", required=True)
    args = ap.parse_args()
    full = load(args.full)
    retry = load(args.retry)
    if not retry:
        raise SystemExit("retry file is empty")
    replacements = {x["case_id"]: x for x in retry}
    if len(replacements) != len(retry):
        raise SystemExit("retry file contains duplicate case_id")
    old = [x for x in full if x.get("case_id") in replacements]
    if len(old) != len(replacements):
        raise SystemExit(f"expected {len(replacements)} originals, got {len(old)}")
    merged = [replacements.get(x.get("case_id"), x) for x in full]
    with open(args.replaced, "w", encoding="utf-8") as f:
        for row in old:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with open(args.full, "w", encoding="utf-8") as f:
        for row in merged:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("replaced", sorted(replacements), "finish_reasons",
          {cid: row.get("subject_meta", {}).get("finish_reason")
           for cid, row in replacements.items()})


if __name__ == "__main__":
    main()
