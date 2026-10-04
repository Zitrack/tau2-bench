"""Extract failed-trial trajectories for given task ids from golden_full results.

Usage: .venv/Scripts/python.exe ../extract_golden_fail.py E12 H05 ... [--trial N]
Prints per failed trial: task communicate_info, agent text messages (trimmed),
user messages, tool call names+args.
"""

import json
import sys
from pathlib import Path

RESULTS = Path(sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "data/simulations/campus_golden_full/results.json")
TASKS = Path("data/tau2/domains/campus/tasks.json")

args = [a for a in sys.argv[1:] if not a.startswith("--")]
force_trial = None
if "--trial" in sys.argv:
    force_trial = int(sys.argv[sys.argv.index("--trial") + 1])

tasks = {t["id"]: t for t in json.loads(TASKS.read_text(encoding="utf-8"))}
d = json.loads(RESULTS.read_text(encoding="utf-8"))

for tid in args:
    t = tasks[tid]
    cc = t["evaluation_criteria"].get("communicate_info")
    acts = [(a.get("requestor"), a.get("name"), a.get("arguments"))
            for a in t["evaluation_criteria"].get("actions", [])]
    print("#" * 90)
    print(f"TASK {tid}  communicate_info={json.dumps(cc, ensure_ascii=False)}")
    print(f"  golden actions: {json.dumps(acts, ensure_ascii=False)[:600]}")
    print(f"  user_instructions(tail): ...{json.dumps(t['user_scenario']['instructions'], ensure_ascii=False)[-400:]}")
    for s in d["simulations"]:
        if s["task_id"] != tid:
            continue
        ri = s.get("reward_info") or {}
        r = ri.get("reward") if ri is not None else 0.0
        if r >= 1.0 and force_trial is None:
            continue
        if force_trial is not None and s.get("trial") != force_trial:
            continue
        print("=" * 90)
        print(f"SIM task={tid} trial={s.get('trial')} reward={r} term={s.get('termination_reason')} "
              f"msgs={len(s['messages'])} dur={round(s.get('duration') or 0)}s")
        for m in s["messages"]:
            role = m["role"]
            content = (m.get("content") or "").strip()
            if m.get("tool_calls"):
                calls = [(c.get("name"), json.dumps(c.get("arguments"), ensure_ascii=False)[:200])
                         for c in m["tool_calls"]]
                print(f"  [{role}][calls] {calls}")
            if not content:
                continue
            if role == "assistant":
                show = content if len(content) < 500 else content[:250] + " ...||... " + content[-250:]
                print(f"  [A] {show}")
            elif role == "user":
                show = content if len(content) < 400 else content[:200] + " ...||... " + content[-200:]
                print(f"  [U] {show}")
        # communicate checks detail
        for c in ri.get("communicate_checks") or []:
            if not c.get("met"):
                print(f"  COMM-MISS '{c.get('info')}' justification: {c.get('justification','')[:500]}")
        for e in ri.get("env_assertions") or []:
            if not e.get("met"):
                ea = e["env_assertion"]
                print(f"  ENV-MISS {ea['func_name']} {json.dumps(ea.get('arguments'), ensure_ascii=False)} "
                      f"msg={e.get('message')}")
