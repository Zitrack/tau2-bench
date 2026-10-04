"""S3A-2 analysis of campus_golden_full (50 tasks x 4 trials).

Usage (from fork root):
  .venv/Scripts/python.exe ../analyze_golden_full.py [results.json path]

Outputs:
- per-task trials + solved count + DoD flag
- difficulty split means (easy/medium/hard) + solved rates
- failure component breakdown (DB / COMMUNICATE / env_assertion) per failed trial
- termination reason distribution for failed trials
- zero-write & rejection-task communicate details
- cost total (USD)
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

RESULTS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "data/simulations/campus_golden_full/results.json"
)
d = json.loads(RESULTS.read_text(encoding="utf-8"))
sims = d["simulations"]

REJECT_16 = {"E04", "E08", "E14", "M01", "M03", "M04", "M07", "M08", "M09",
             "M15", "M17", "M18", "H05", "H11", "H13", "H14"}
ZERO_WRITE_5 = {"E01", "E05", "E15", "M03", "M19"}

by_task: dict[str, list[dict]] = defaultdict(list)
for s in sims:
    ri = s.get("reward_info") or {}
    db = (ri.get("db_check") or {}).get("db_match", False)
    cc = ri.get("communicate_checks") or []
    comm_ok = all(c.get("met") for c in cc) if cc else True
    envs = ri.get("env_assertions") or []
    env_ok = all(e.get("met") for e in envs) if envs else True
    env_miss = [f"{e['env_assertion']['func_name']}:{e['env_assertion'].get('arguments', {})}"
                for e in envs if not e.get("met")]
    comm_miss = [c.get("info") for c in cc if not c.get("met")]
    by_task[s["task_id"]].append({
        "reward": ri.get("reward") if ri is not None else 0.0,
        "db": db,
        "comm_ok": comm_ok,
        "comm_miss": comm_miss,
        "env_ok": env_ok,
        "env_miss": env_miss,
        "term": s.get("termination_reason"),
        "n_msgs": len(s.get("messages") or []),
        "cost": (s.get("agent_cost") or 0) + (s.get("user_cost") or 0),
        "trial": s.get("trial"),
    })

# --- per-task table ---
print("=" * 100)
print(f"{'task':6} {'trials':28} solved  DoD")
rows = []
for tid in sorted(by_task):
    ts = sorted(by_task[tid], key=lambda x: x["trial"] or 0)
    rs = [t["reward"] for t in ts]
    solved = sum(1 for r in rs if r >= 1.0)
    ok = solved >= 3
    rows.append((tid, ts, rs, solved, ok))
    print(f"{tid:6} {str(rs):28} {solved}/{len(rs)}   {'OK' if ok else 'LOW'}")

n_ok = sum(1 for _, _, _, _, ok in rows if ok)
print(f"\nDoD solved(>=3/4): {n_ok}/{len(rows)}")
avg_all = sum(sum(rs) / len(rs) for _, _, rs, _, _ in rows) / max(len(rows), 1)
print(f"avg reward overall: {avg_all:.3f}")

# --- difficulty split ---
for name, ids in (("easy", [t for t in sorted(by_task) if t.startswith("E")]),
                  ("medium", [t for t in sorted(by_task) if t.startswith("M")]),
                  ("hard", [t for t in sorted(by_task) if t.startswith("H")])):
    sub = [r for tid, _, rs, _, _ in rows if tid in ids for r in rs]
    solved_n = sum(1 for tid, _, _, _, ok in rows if tid in ids and ok)
    if sub:
        print(f"{name:7} n={len(ids):2}  avg_reward={sum(sub)/len(sub):.3f}  "
              f"tasks_ok={solved_n}/{len(ids)}")

# --- failure components ---
print("\n--- failed trials breakdown ---")
comp_counter = Counter()
term_counter = Counter()
for tid, ts, _, _, _ in rows:
    for t in ts:
        if t["reward"] >= 1.0:
            continue
        if not t["db"] and t["comm_ok"]:
            cls = "DB-only"
        elif t["db"] and not t["comm_ok"]:
            cls = "COMM-only"
        elif not t["db"] and not t["comm_ok"]:
            cls = "DB+COMM"
        else:
            cls = "env-only"
        comp_counter[cls] += 1
        term_counter[t["term"]] += 1
        envm = f" ENV:{t['env_miss']}" if t["env_miss"] else ""
        commm = f" COMM-miss:{t['comm_miss']}" if t["comm_miss"] else ""
        print(f"{tid} t{t['trial']} r={t['reward']} {cls} term={t['term']} msgs={t['n_msgs']}{envm}{commm}")
print("component dist:", dict(comp_counter))
print("termination dist:", dict(term_counter))

# --- special groups ---
print("\n--- zero-write 5 (E01/E05/E15/M03/M19) ---")
for tid in sorted(ZERO_WRITE_5):
    if tid not in by_task:
        continue
    for t in by_task[tid]:
        flag = "OK" if t["comm_ok"] else f"MISS {t['comm_miss']}"
        print(f"{tid} t{t['trial']} reward={t['reward']} db={t['db']} comm={flag}")

print("\n--- rejection 16 ---")
r_ok = 0
for tid in sorted(REJECT_16):
    if tid not in by_task:
        continue
    rs = [t["reward"] for t in sorted(by_task[tid], key=lambda x: x["trial"] or 0)]
    solved = sum(1 for r in rs if r >= 1.0)
    r_ok += solved >= 3
    comm_bad = [t["comm_miss"] for t in by_task[tid] if not t["comm_ok"]]
    db_bad = sum(1 for t in by_task[tid] if not t["db"])
    print(f"{tid}: trials={rs} solved={solved}/4 db_bad={db_bad} comm_bad={comm_bad}")
print(f"rejection-16 tasks >=3/4: {r_ok}/16")

# --- uns-smoked 38 ---
SEED10 = {"E02", "E04", "E06", "H01", "H10", "H13", "M05", "M08", "M10", "M20"}
SMOKED = SEED10 | {"H02", "H15", "M20"}
uns = [tid for tid in sorted(by_task) if tid not in SMOKED and tid != "M20"]
uns_ok = sum(1 for tid, _, _, _, ok in rows if tid in uns and ok)
print(f"\nuns-smoked new tasks (38): pass={uns_ok}/{len(uns)}")

# --- cost ---
total = sum(t["cost"] for ts in by_task.values() for t in ts)
tin = sum((m.get("usage") or {}).get("prompt_tokens", 0) or 0
          for s in sims for m in (s.get("messages") or []))
tout = sum((m.get("usage") or {}).get("completion_tokens", 0) or 0
           for s in sims for m in (s.get("messages") or []))
print(f"\nsims={len(sims)}  total_cost_USD={total:.4f}  (x7.2 => CNY {total*7.2:.2f})")
print(f"tokens in={tin} out={tout}")
