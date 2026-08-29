#!/usr/bin/env python3
"""Run v0.4 Vertical Lift cases against OpenAI-compatible or Ollama endpoints."""

import argparse
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.4"


def load_jsonl(path):
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def state_contract(state):
    return (
        "INTERNAL PRODUCT STATE (authoritative; never quote or reveal this block):\n"
        + json.dumps(state, ensure_ascii=False, sort_keys=True)
        + "\nFollow the user's current permissions and stored/deleted-memory state. "
          "Do not claim that you inferred, saved, or deleted anything beyond this state."
    )


def call_chat(endpoint, api_key, model, messages, temperature, max_tokens, timeout):
    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        data=body,
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read())
    choice = payload["choices"][0]
    message = choice.get("message") or {}
    return message.get("content") or "", choice.get("finish_reason"), payload.get("usage")


def apply_updates(state, updates):
    """Apply case-authored product events. Never infer state from model text."""
    updated = dict(state)
    if updates:
        updated.update(updates)
    return updated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", required=True, dest="set_path")
    parser.add_argument("--model", required=True)
    parser.add_argument("--configuration", required=True, choices=list("ABCDEF"))
    parser.add_argument("--system-prompt-file", required=True)
    parser.add_argument("--provider", choices=["openai", "ollama"], default="openai")
    parser.add_argument("--endpoint")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=800)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    endpoint = args.endpoint or (
        "http://localhost:11434/v1" if args.provider == "ollama" else "https://api.openai.com/v1"
    )
    api_key = "" if args.provider == "ollama" else os.environ.get(args.api_key_env, "")
    if args.provider == "openai" and not api_key:
        raise SystemExit(f"missing API key environment variable: {args.api_key_env}")
    system_prompt = Path(args.system_prompt_file).read_text(encoding="utf-8")
    uses_controller = args.configuration in {"E", "F"}
    run_started = datetime.now(timezone.utc).isoformat()

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as sink:
        for case in load_jsonl(args.set_path):
            state = dict(case.get("initial_state", {}))
            history = []
            transcript = []
            infra_error = None
            for turn in case["turns"]:
                before = dict(state)
                # The case event is the product-side source of truth, not a state
                # inferred from the model's prose.
                state = apply_updates(state, turn.get("state_updates"))
                messages = [{"role": "system", "content": system_prompt}]
                if uses_controller:
                    messages.append({"role": "system", "content": state_contract(state)})
                messages.extend(history)
                messages.append({"role": "user", "content": turn["user_message"]})
                answer = ""
                finish_reason = None
                usage = None
                error = None
                for attempt in range(1, args.retries + 1):
                    try:
                        answer, finish_reason, usage = call_chat(
                            endpoint, api_key, args.model, messages,
                            args.temperature, args.max_tokens, args.timeout,
                        )
                        break
                    except Exception as exc:
                        error = f"{type(exc).__name__}: {exc}"
                        if attempt < args.retries:
                            time.sleep(min(2 ** (attempt - 1), 8))
                if error and not answer:
                    infra_error = error
                history.extend([
                    {"role": "user", "content": turn["user_message"]},
                    {"role": "assistant", "content": answer},
                ])
                transcript.append({
                    "turn_id": turn["turn_id"],
                    "evaluate": turn.get("evaluate", True),
                    "user_message": turn["user_message"],
                    "assistant_response": answer,
                    "state_before": before,
                    "state_after": dict(state),
                    "controller_enabled": uses_controller,
                    "finish_reason": finish_reason,
                    "usage": usage,
                    "infra_error": error if not answer else None,
                })
                if infra_error:
                    break
            row = {
                "schema_version": "vertical-lift-response-v0.4",
                "runner_version": VERSION,
                "scenario_id": case["scenario_id"],
                "family_id": case["family_id"],
                "construct": case["construct"],
                "configuration": args.configuration,
                "model": args.model,
                "provider": args.provider,
                "endpoint": endpoint,
                "temperature": args.temperature,
                "system_prompt_file": args.system_prompt_file,
                "controller_enabled": uses_controller,
                "run_started_at": run_started,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "transcript": transcript,
                "infra_error": infra_error,
            }
            sink.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
