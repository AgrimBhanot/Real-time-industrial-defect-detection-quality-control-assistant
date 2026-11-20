#!/usr/bin/env python3
"""Stand-in for native/qc_llm_server speaking the same stdin/stdout protocol (tests only).

Replies with a fixed advice JSON for the defect named after 'DEFECT=' in the prompt. A prompt containing
'HANG' never gets a reply (timeout test); 'CRASH' exits the process.
"""
import json
import re
import sys
import time

out = sys.stdout.buffer
inp = sys.stdin.buffer
print("noise on stderr", file=sys.stderr)
out.write(b'READY {"load_ms":12,"warmup_ms":3,"threads":4,"pid":0}\n')
out.flush()
while True:
    line = inp.readline()
    if not line or line.startswith(b"QUIT"):
        break
    _, max_new, temp, n = line.split()
    prompt = inp.read(int(n)).decode()
    if "HANG" in prompt:
        time.sleep(60)
        continue
    if "CRASH" in prompt:
        sys.exit(3)
    m = re.search(r"DEFECT=(\w[\w-]*)", prompt)
    d = m.group(1) if m else "open"
    text = json.dumps({
        "summary": f"FAIL: {d} found.", "likely_causes": ["over-etching"], "recommended_actions": ["check etch"],
        "verify": "re-inspect", "log_entry": f"{d} — ünïcode ok",
    }, ensure_ascii=False) + "<|eot_id|>"
    data = text.encode()
    t = 1000
    stats = {"prompt_tokens": len(prompt) // 4, "generated_tokens": 41, "model_load_start_ms": 0,
             "model_load_end_ms": 0, "inference_start_ms": t, "inference_end_ms": t + 2400, "prompt_eval_end_ms": t + 400,
             "first_token_ms": t + 400, "aggregate_sampling_time_ms": 5, "SCALING_FACTOR_UNITS_PER_SECOND": 1000}
    out.write(b"OK %d\n" % len(data) + data + b"STATS " + json.dumps(stats).encode() + b"\n")
    out.flush()
