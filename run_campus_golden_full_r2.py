"""S3A-2 repair round r2: rerun the 17 patched tasks x 4 trials.

New dir campus_golden_full_r2 (checkpoint-safe). Pattern of run_campus_golden_full.py.
Run from fork root: .venv/Scripts/python.exe ../run_campus_golden_full_r2.py
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / "tau2-bench" / ".env")

import tau2.evaluator.evaluator_nl_assertions as nl_mod  # noqa: E402

nl_mod.DEFAULT_LLM_NL_ASSERTIONS = "deepseek/deepseek-chat"

from tau2 import TextRunConfig  # noqa: E402
from tau2.data_model.tasks import Task  # noqa: E402
from tau2.metrics.agent_metrics import compute_metrics  # noqa: E402
from tau2.runner import run_tasks  # noqa: E402

DEEPSEEK = "deepseek/deepseek-chat"

REPAIR_IDS = {"E12", "H05", "H08", "M12", "M19", "H14", "M08", "H13",
              "M06", "M03", "M17", "M05", "H01", "H02", "H15", "M10", "M20"}

tasks_path = Path("data/tau2/domains/campus/tasks.json")
all_tasks = [Task.model_validate(t) for t in json.loads(tasks_path.read_text(encoding="utf-8"))]
tasks = [t for t in all_tasks if t.id in REPAIR_IDS]
print(f"loaded {len(tasks)} repair tasks", file=sys.stderr)

TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
CONC = int(sys.argv[2]) if len(sys.argv) > 2 else 5

config = TextRunConfig(
    domain="campus",
    agent="llm_agent",
    user="user_simulator",
    llm_agent=DEEPSEEK,
    llm_user=DEEPSEEK,
    num_trials=TRIALS,
    max_concurrency=CONC,
    seed=20261004,
    max_steps=60,
)

save_dir = Path("data/simulations/campus_golden_full_r2")
results = run_tasks(config, tasks, save_dir=save_dir, save_path=save_dir / "results.json")

m = compute_metrics(results)
print(f"avg_reward={m.avg_reward}")
by_task = {}
total_cost = 0.0
for sim in results.simulations:
    ri = sim.reward_info
    r = ri.reward if ri is not None else 0.0
    by_task.setdefault(sim.task_id, []).append(round(r, 3))
    total_cost += (sim.agent_cost or 0.0) + (sim.user_cost or 0.0)
for tid, rs in sorted(by_task.items()):
    solved = sum(1 for r in rs if r >= 1.0)
    flag = "OK " if solved >= 3 else "LOW"
    print(f"{flag} {tid}: trials={rs} solved={solved}/{len(rs)}")
n_ok = sum(1 for rs in by_task.values() if sum(1 for r in rs if r >= 1.0) >= 3)
print(f"repair tasks solved(3/4+): {n_ok}/{len(by_task)}")
tin = sum((mm.get("usage") or {}).get("prompt_tokens", 0) or 0
          for s in results.simulations for mm in (s.messages or []))
tout = sum((mm.get("usage") or {}).get("completion_tokens", 0) or 0
           for s in results.simulations for mm in (s.messages or []))
print(f"tokens in={tin} out={tout}  report_cost_USD={total_cost:.4f}")
