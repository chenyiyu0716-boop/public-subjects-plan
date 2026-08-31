#!/usr/bin/env python3
"""Verify downloaded ModelScope weights against the frozen SHA-256 table."""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-dir", required=True)
    args = parser.parse_args()

    expected = json.loads(Path(args.expected).read_text(encoding="utf-8"))
    model = expected["models"][args.model_id]
    model_dir = Path(args.model_dir)
    failures = []
    report = {
        "model_id": args.model_id,
        "revision": model["revision"],
        "model_dir": str(model_dir),
        "files": {},
    }
    for name, want in model["files"].items():
        path = model_dir / name
        if not path.is_file():
            failures.append(f"missing {name}")
            report["files"][name] = {"status": "missing"}
            continue
        got = sha256_file(path)
        ok = got == want
        report["files"][name] = {
            "status": "ok" if ok else "mismatch",
            "size": path.stat().st_size,
            "sha256": got,
            "expected_sha256": want,
        }
        if not ok:
            failures.append(f"hash mismatch {name}")
    report["ok"] = not failures
    report["failures"] = failures
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())
