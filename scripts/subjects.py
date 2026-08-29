#!/usr/bin/env python3
"""
公开测试对象适配器层 (v0.1)

职责：对给定评测集，调用命名公开对象（商业 API / 本地 ollama / mock），
生成 responses.jsonl（模型回复，与评分解耦）。
评分解耦到 eval_harness.py --responses。

依赖：仅标准库（urllib），零第三方包，沙箱外本机执行。
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# ---------------- 命名预设 ----------------
PRESETS = {
    "deepseek":        {"type": "openai", "base_url": "https://api.deepseek.com/v1",
                        "model": "deepseek-chat", "key_env": "DEEPSEEK_API_KEY"},
    "glm":             {"type": "openai", "base_url": "https://open.bigmodel.cn/api/paas/v4",
                        "model": "glm-4-flash", "key_env": "ZHIPU_API_KEY"},
    "doubao":          {"type": "openai", "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                        "model": "doubao-seed-1.6-250615", "key_env": "DOUBAO_API_KEY"},
    "qwen_tongyi":     {"type": "openai", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                        "model": "qwen-plus", "key_env": "DASHSCOPE_API_KEY"},
    # 百炼公开三方模型：用于国产模型跨家族扩展。
    "glm_5_2_bailian": {"type": "openai", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                          "model": "glm-5.2", "key_env": "DASHSCOPE_API_KEY",
                          "request_overrides": {"enable_thinking": False}},
    "kimi_k2_5_bailian": {"type": "openai", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                            "model": "kimi-k2.5", "key_env": "DASHSCOPE_API_KEY"},
    "minimax_m2_5_bailian": {"type": "openai", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                               "model": "MiniMax-M2.5", "key_env": "DASHSCOPE_API_KEY"},
    "claude":          {"type": "openai", "base_url": "https://openrouter.ai/api/v1",
                        "model": "anthropic/claude-3.5-sonnet", "key_env": "OPENROUTER_API_KEY"},
    "gpt":             {"type": "openai", "base_url": "https://api.openai.com/v1",
                        "model": "gpt-4o-mini", "key_env": "OPENAI_API_KEY"},
    # 公开、低成本、跨 Qwen 家族的 v0.2 对象；均可由任何 OpenRouter 开发者账号调用。
    "deepseek_v4_flash": {"type": "openai", "base_url": "https://openrouter.ai/api/v1",
                           "model": "deepseek/deepseek-v4-flash", "key_env": "OPENROUTER_API_KEY"},
    "stepfun_3_5_flash": {"type": "openai", "base_url": "https://openrouter.ai/api/v1",
                           "model": "stepfun/step-3.5-flash", "key_env": "OPENROUTER_API_KEY"},
    "qwen_local_7b":   {"type": "ollama", "model": "qwen2.5:7b"},
    "qwen_local_1_5b": {"type": "ollama", "model": "qwen2.5:1.5b"},  # 弱档基线
}
WEAK_SUBJECT = "qwen_local_1_5b"
PROMPT_TEMPLATE_VERSION = "v0.2"


def host_of(url):
    try:
        return urllib.parse.urlparse(url).netloc
    except Exception:
        return url


# ---------------- 真实调用（零依赖 urllib） ----------------
def call_openai(base_url, api_key, model, messages, temperature=0.0,
                max_output_tokens=512, timeout=120, request_overrides=None):
    url = base_url.rstrip("/") + "/chat/completions"
    # 锁定 temperature=0：基线必须可复现（非确定性 temp 导致重跑响应漂移，
    # 恒定项 verdict 翻转 → dp 虚变，见 ai-eval-pipeline pitfall #8）
    request_body = {"model": model, "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_output_tokens}
    request_body.update(request_overrides or {})
    payload = json.dumps(request_body).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}" if api_key else "",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    choice = data["choices"][0]
    return choice["message"]["content"], {
        "finish_reason": choice.get("finish_reason"),
        "usage": data.get("usage"),
    }


def call_ollama(model, messages, temperature=0.0, max_output_tokens=512,
                timeout=180):
    url = "http://localhost:11434/v1/chat/completions"
    # 锁定 temperature=0：基线可复现（见 pitfall #8）
    payload = json.dumps({"model": model, "messages": messages,
                          "temperature": temperature,
                          "max_tokens": max_output_tokens}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json"})
    # 强制直连本地 ollama：用空 ProxyHandler 构造专属 opener，
    # 彻底绕开系统代理 / 环境变量代理（macOS 上 urllib 会把 localhost:11434
    # 也发往系统代理 7897，代理一死就连不上；NO_PROXY 对系统代理源不生效）。
    # 外部 API（call_openai）仍走默认代理，不受影响。
    direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with direct_opener.open(req, timeout=timeout) as r:
        data = json.loads(r.read())
    choice = data["choices"][0]
    return choice["message"]["content"], {
        "finish_reason": choice.get("finish_reason"),
        "usage": data.get("usage"),
    }


def respond(preset_name, messages, system_prompt=None, temperature=0.0,
            max_output_tokens=512):
    cfg = PRESETS[preset_name]
    msgs = ([{"role": "system", "content": system_prompt}] if system_prompt else []) + messages
    if cfg["type"] == "openai":
        key = os.environ.get(cfg["key_env"], "")
        if not key:
            raise RuntimeError(f"缺少环境变量 {cfg['key_env']}（对象 {preset_name}）")
        return call_openai(cfg["base_url"], key, cfg["model"], msgs,
                           temperature=temperature,
                           max_output_tokens=max_output_tokens,
                           request_overrides=cfg.get("request_overrides"))
    elif cfg["type"] == "ollama":
        return call_ollama(cfg["model"], msgs, temperature=temperature,
                           max_output_tokens=max_output_tokens)
    raise ValueError(f"未知类型 {cfg['type']}")


# ---------------- mock（不触网自测） ----------------
GOOD = "（良好基线）我听到了，先陪你待会儿，不急着下结论。"
WEAK_PREFIX = "（弱基线）"


def mock_respond(case, weak):
    if not weak:
        return GOOD
    probs = case.get("prohibited_behaviors", [])
    if probs:
        return WEAK_PREFIX + " " + "；".join(probs)
    return WEAK_PREFIX + " 你到底怎么了，说说看。"


# ---------------- 构造对话 ----------------
def build_messages(case):
    if "turns" in case:
        msgs = []
        for t in case["turns"]:
            u = t.get("user_message") or t.get("user") or ""
            if u:
                msgs.append({"role": "user", "content": u})
            a = t.get("assistant_message") or t.get("assistant")
            if a:
                msgs.append({"role": "assistant", "content": a})
        return msgs
    um = (case.get("user_message") or case.get("user") or
          case.get("prompt") or case.get("input") or "")
    return [{"role": "user", "content": um}]


def case_id_of(case):
    return (case.get("case_id") or case.get("probe_id") or
            case.get("scenario_id") or case.get("id"))


# ---------------- 主流程 ----------------
def run_subject(set_path, subject_name, out_path, system_prompt=None,
                use_mock=False, weak=False, temperature=0.0,
                max_output_tokens=512):
    rows = []
    with open(set_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    outs = []
    infra_errors = []  # (case_id, error_str) —— 单条调用失败不中止整体，记录后继续
    for case in rows:
        cid = case_id_of(case)
        msgs = build_messages(case)
        infra_err = None
        if use_mock:
            resp = mock_respond(case, weak)
            generation_meta = {"finish_reason": "mock", "usage": None}
            sname = "mock_good" if not weak else "mock_weak"
            model = "mock"
            host = "mock"
        else:
            try:
                resp, generation_meta = respond(
                    subject_name, msgs, system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens)
                sname = subject_name
                model = PRESETS.get(subject_name, {}).get("model", "?")
                host = host_of(PRESETS.get(subject_name, {}).get("base_url", ""))
            except Exception as e:
                # 单条失败不应拖垮整轮：记录空 response，并标 infra_error；
                # v0.2 harness 会将其隔离为未评估，不计入模型失败率。
                err = f"{type(e).__name__}: {e}"
                print(f"[subjects] case {cid} 调用 {subject_name} 失败（跳过并继续）: {err}",
                      file=sys.stderr)
                infra_errors.append((cid, err))
                resp = ""
                generation_meta = {"finish_reason": "infra_error", "usage": None}
                infra_err = err
                sname = subject_name
                model = PRESETS.get(subject_name, {}).get("model", "?")
                host = host_of(PRESETS.get(subject_name, {}).get("base_url", ""))
        meta = {
            "subject": sname,
            "model": model,
            "base_host": host,
            "run_date_utc": datetime.now(timezone.utc).isoformat(),
            "prompt_template_version": PROMPT_TEMPLATE_VERSION,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "infra_error": infra_err,
            "finish_reason": generation_meta.get("finish_reason"),
            "usage": generation_meta.get("usage"),
            "request_overrides": PRESETS.get(subject_name, {}).get("request_overrides"),
        }
        outs.append({"case_id": cid, "response_text": resp, "subject_meta": meta})
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for o in outs:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    n_err = len(infra_errors)
    print(f"已生成 {out_path} 共 {len(outs)} 条 (subject={subject_name})"
          + (f"；{n_err} 条 infra_error（空 response，评分时隔离）" if n_err else ""))
    if n_err:
        print(f"[subjects] 失败 case 清单（贴回这段即可定位）：{infra_errors}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, help="评测集 JSONL 路径")
    ap.add_argument("--subject", required=True, help="预设名 或 mock")
    ap.add_argument("--out", required=True, help="responses.jsonl 输出路径")
    ap.add_argument("--system-prompt", default=None)
    ap.add_argument("--system-prompt-file", default=None,
                    help="从 UTF-8 文件读取公开、可版本化的 system policy")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-output-tokens", type=int, default=512)
    ap.add_argument("--mock", action="store_true", help="用 mock 主体（不触网）")
    ap.add_argument("--weak", action="store_true", help="mock 弱基线")
    args = ap.parse_args()
    system_prompt = args.system_prompt
    if args.system_prompt_file:
        with open(args.system_prompt_file, encoding="utf-8") as f:
            system_prompt = f.read().strip()
    if args.mock:
        run_subject(args.set, args.subject, args.out, system_prompt,
                    use_mock=True, weak=args.weak,
                    temperature=args.temperature,
                    max_output_tokens=args.max_output_tokens)
    else:
        if args.subject not in PRESETS:
            print(f"未知对象 {args.subject}，可选：{', '.join(PRESETS)}",
                  file=sys.stderr)
            sys.exit(1)
        run_subject(args.set, args.subject, args.out, system_prompt,
                    temperature=args.temperature,
                    max_output_tokens=args.max_output_tokens)


if __name__ == "__main__":
    main()
