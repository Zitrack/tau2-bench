"""Final S3A-2 DoD assembly: effective-evidence rule (last patch round wins).

Rounds:
  r1 = campus_golden_full       (all 50 tasks, pre-patch)
  r2 = campus_golden_full_r2    (17 patched tasks, post-patch)
  r4 = campus_golden_full_r4    (M05+H15, post-r3/r4 patches)
"""

import json
from collections import Counter
from pathlib import Path

FORK = Path(".")
ROUNDS = {
    "r1": FORK / "data/simulations/campus_golden_full/results.json",
    "r2": FORK / "data/simulations/campus_golden_full_r2/results.json",
    "r4": FORK / "data/simulations/campus_golden_full_r4/results.json",
}
PATCHED_17 = {"E12", "H05", "H08", "M12", "M19", "H14", "M08", "H13",
              "M06", "M03", "M17", "M05", "H01", "H02", "H15", "M10", "M20"}
R4_IDS = {"M05", "H15"}

def load(round_path):
    d = json.loads(round_path.read_text(encoding="utf-8"))
    by = {}
    for s in d["simulations"]:
        ri = s.get("reward_info") or {}
        by.setdefault(s["task_id"], []).append({
            "trial": s.get("trial"), "reward": ri.get("reward") if ri is not None else 0.0,
        })
    return by

r1, r2, r4 = (load(p) for p in ROUNDS.values())

effective = {}
for tid in sorted(set(r1) | set(r2) | set(r4)):
    if tid in R4_IDS:
        effective[tid] = sorted(r4[tid], key=lambda x: x["trial"] or 0)
    elif tid in PATCHED_17:
        effective[tid] = sorted(r2[tid], key=lambda x: x["trial"] or 0)
    else:
        effective[tid] = sorted(r1[tid], key=lambda x: x["trial"] or 0)

print(f"{'task':5} {'layer':7} {'trials':26} {'solved':7} DoD")
dist = Counter()
layer_stats = {"easy": [], "medium": [], "hard": []}
layer_tasks = {"easy": [], "medium": [], "hard": []}
for tid, ts in effective.items():
    layer = {"E": "easy", "M": "medium", "H": "hard"}[tid[0]]
    rs = [t["reward"] for t in ts]
    solved = sum(1 for r in rs if r >= 1.0)
    dist[f"{solved}/{len(rs)}"] += 1
    layer_tasks[layer].append(solved >= 3)
    layer_stats[layer].extend(rs)
    print(f"{tid:5} {layer:7} {str(rs):26} {solved}/{len(rs)}  {'OK' if solved >= 3 else 'LOW'}")

n_ok = sum(1 for ts in effective.values() if sum(1 for t in ts if t["reward"] >= 1.0) >= 3)
print(f"\nDoD solved(>=3/4): {n_ok}/{len(effective)}")
print("solved dist:", dict(sorted(dist.items(), key=lambda kv: -int(kv[0].split('/')[0]))))
for name in ("easy", "medium", "hard"):
    v = layer_stats[name]
    print(f"{name:7} n={len(v):3} avg_reward={sum(v)/len(v):.3f} tasks_ok={sum(layer_tasks[name])}/{len(layer_tasks[name])}")

out = {tid: [t["reward"] for t in ts] for tid, ts in effective.items()}
Path("../golden_full_effective.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("written ../golden_full_effective.json")
