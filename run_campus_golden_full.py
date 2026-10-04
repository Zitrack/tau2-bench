"""S3A-2 full golden run: campus 50 tasks x 4 trials, all LLM roles on DeepSeek.

Same pattern as dev/run_campus_golden.py (S3A) — new save dir campus_golden_full
to avoid the checkpoint-resume stdin prompt on rerun of a killed run (S3A pitfall #1).

Run from D:/Projects/tau2-zh/dev/tau2-bench:
  .venv/Scripts/python.exe ../run_campus_golden_full.py 4 5
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

tasks_path = Path("data/tau2/domains/campus/tasks.json")
tasks = [Task.model_validate(t) for t in json.loads(tasks_path.read_text(encoding="utf-8"))]
print(f"loaded {len(tasks)} campus tasks", file=sys.stderr)

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

save_dir = Path("data/simulations/campus_golden_full")
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
print(f"overall solved(3/4+): {n_ok}/{len(by_task)}")
print(f"total_cost_USD={total_cost:.4f}")
