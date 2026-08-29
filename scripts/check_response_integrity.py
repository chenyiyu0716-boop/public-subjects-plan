#!/usr/bin/env python3
"""在裁判前检查生成完整性；非正常结束不得进入模型失败率。"""
import json
import sys


bad = []
for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    for row in rows:
        meta = row.get("subject_meta") or {}
        if meta.get("infra_error") or not str(row.get("response_text", "")).strip():
            bad.append((path, row.get("case_id"), "infra_or_empty"))
        elif meta.get("finish_reason") != "stop":
            bad.append((path, row.get("case_id"),
                        f"finish_reason={meta.get('finish_reason')}"))
if bad:
    for item in bad:
        print("INTEGRITY_FAIL", *item)
    raise SystemExit(1)
print("response integrity ok", len(sys.argv) - 1, "files")
