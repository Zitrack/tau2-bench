"""Dump first-user-message + agent calls (with ids) for given task/trials of golden_full r3.

Usage: .venv/Scripts/python.exe ../dump_r3_fail.py
"""
import json
from pathlib import Path

d = json.loads(Path("data/simulations/campus_golden_full_r3/results.json").read_text(encoding="utf-8"))
for s in d["simulations"]:
    tid, tr = s["task_id"], s.get("trial")
    if not (tid == "M05" and tr in (0, 1) or tid == "H15" and tr == 1):
        continue
    print("=" * 84)
    ri = s.get("reward_info") or {}
    print(f"SIM {tid} t{tr} r={ri.get('reward')} term={s.get('termination_reason')} msgs={len(s['messages'])}")
    users = [m for m in s["messages"] if m["role"] == "user"]
    for m in users[:2]:
        c = (m.get("content") or "").strip()
        if c:
            print("  [U-first]", c[:250].replace("\n", "|"))
    for m in s["messages"]:
        if m.get("tool_calls"):
            for c in m["tool_calls"]:
                nm = c.get("name")
                if nm in ("get_student_details", "get_grades", "get_enrollments",
                          "get_course_offerings", "get_service_requests", "search_policy"):
                    continue
                args = c.get("arguments")
                if isinstance(args, str):
                    args = json.loads(args) if args else {}
                print(f"  [CALL {m['role'][0]}] {nm} {json.dumps(args, ensure_ascii=False)[:200]}")
