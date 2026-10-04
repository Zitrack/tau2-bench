"""S3A-2 repair r4: run M05 + H15 x 4 trials into campus_golden_full_r4."""
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv(".env")

import tau2.evaluator.evaluator_nl_assertions as nl_mod  # noqa: E402

nl_mod.DEFAULT_LLM_NL_ASSERTIONS = "deepseek/deepseek-chat"

from tau2 import TextRunConfig  # noqa: E402
from tau2.data_model.tasks import Task  # noqa: E402
from tau2.metrics.agent_metrics import compute_metrics  # noqa: E402
from tau2.runner import run_tasks  # noqa: E402

REPAIR = {"M05", "H15"}
tasks_all = [Task.model_validate(t) for t in json.loads(
    Path("data/tau2/domains/campus/tasks.json").read_text(encoding="utf-8"))]
tasks = [t for t in tasks_all if t.id in REPAIR]
print("loaded", len(tasks), file=sys.stderr)

config = TextRunConfig(
    domain="campus", agent="llm_agent", user="user_simulator",
    llm_agent="deepseek/deepseek-chat", llm_user="deepseek/deepseek-chat",
    num_trials=4, max_concurrency=5, seed=20261004, max_steps=60,
)
save_dir = Path("data/simulations/campus_golden_full_r4")
results = run_tasks(config, tasks, save_dir=save_dir, save_path=save_dir / "results.json")

m = compute_metrics(results)
print(f"avg_reward={m.avg_reward}")
for sim in results.simulations:
    ri = sim.reward_info
    db = ri.db_check.db_match if ri is not None else None
    print(sim.task_id, "t", sim.trial, "r", (ri.reward if ri is not None else 0.0), "db", db)
