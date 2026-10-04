"""Replay a failed sim's tool calls into a fresh campus env and diff vs golden-final DB.

Usage: .venv/Scripts/python.exe ../replay_golden_diff.py TASK_ID TRIAL
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from tau2.domains.campus.environment import get_environment  # noqa: E402
from tau2.data_model.tasks import Task  # noqa: E402

tid, trial = sys.argv[1], int(sys.argv[2])

tasks_path = Path("data/tau2/domains/campus/tasks.json")
task = Task.model_validate(
    [t for t in json.loads(tasks_path.read_text(encoding="utf-8")) if t["id"] == tid][0]
)
RESULTS_ARG = sys.argv[3] if len(sys.argv) > 3 else "data/simulations/campus_golden_full/results.json"
d = json.loads(Path(RESULTS_ARG).read_text(encoding="utf-8"))
sim = [s for s in d["simulations"] if s["task_id"] == tid and s.get("trial") == trial][0]

init_data = task.initial_state.initialization_data if task.initial_state else None
init_actions = task.initial_state.initialization_actions if task.initial_state else None

def build_and_replay(calls_iter):
    env = get_environment()
    env.set_state(
        initialization_data=init_data,
        initialization_actions=init_actions,
        message_history=[],
        strict=True,
    )
    errors = []
    for req, name, args in calls_iter:
        try:
            env.make_tool_call(tool_name=name, requestor=req, **args)
        except Exception as e:
            errors.append(f"{req}/{name}: {e}")
    return env, errors

# golden final
golden_calls = [
    (a.requestor, a.name, a.arguments) for a in (task.evaluation_criteria.actions or [])
]
gold_env, gold_err = build_and_replay(iter(golden_calls))
gold_agent = json.loads(json.dumps(gold_env.tools.db.model_dump(), ensure_ascii=False))
gold_user = json.loads(json.dumps(gold_env.user_tools.db.model_dump(), ensure_ascii=False))

# sim final: walk messages
sim_calls = []
for m in sim["messages"]:
    for c in m.get("tool_calls") or []:
        args = c.get("arguments")
        if isinstance(args, str):
            args = json.loads(args) if args else {}
        sim_calls.append(("user" if m["role"] == "user" else "assistant", c.get("name"), args or {}))
sim_env, sim_err = build_and_replay(iter(sim_calls))
sim_agent = json.loads(json.dumps(sim_env.tools.db.model_dump(), ensure_ascii=False))
sim_user = json.loads(json.dumps(sim_env.user_tools.db.model_dump(), ensure_ascii=False))

print("golden replay errors:", gold_err)
print("sim replay errors:", sim_err)
for side, g, s in (("agent_db", gold_agent, sim_agent), ("user_db", gold_user, sim_user)):
    print(f"--- {side} diff ---")
    keys = set(g) | set(s)
    for t in sorted(keys):
        if g.get(t) != s.get(t):
            gt, st = g.get(t) or {}, s.get(t) or {}
            gk, sk = set(gt) if isinstance(gt, dict) else set(), set(st) if isinstance(st, dict) else set()
            for k in sorted(gk | sk):
                if gt.get(k) != st.get(k):
                    print(f"  {t}.{k}:")
                    print(f"    gold: {json.dumps(gt.get(k), ensure_ascii=False)[:300]}")
                    print(f"    sim : {json.dumps(st.get(k), ensure_ascii=False)[:300]}")
