"""Upstream contract guards for the campus domain.

CampusEnvironment relies on several upstream ``Environment`` behaviors that
no generic test pins; if upstream changed them, settlement or student-side
identity would drift while the rest of the suite stayed green:

1. **set_state delegation** — ``initialization_actions`` are replayed
   through ``run_env_function_call`` (one ``sync_tools`` per call) and the
   base performs ONE final ``sync_tools`` at the end of ``set_state``;
   campus applies agent/user data to their own DBs before delegating with
   ``initialization_data=None``;
2. **sync_tools timing** — ``make_tool_call`` does NOT sync (campus
   compensates by settling on the tool execution path, so evaluator
   replays stay settled), while ``run_env_function_call`` syncs exactly
   once after each call;
3. **shared double pointers** — after ``set_state`` the toolkit pair is
   re-shared (``user_tools.main_db is tools.db``,
   ``tools.user_db is user_tools.db``, ``user_tools.agent_tools is
   tools``) while the two DB instances stay DISTINCT (two-DB domain —
   upstream's single-DB merge must not leak in).

Also: ``get_environment(solo_mode=True)`` must raise ``ValueError`` —
the upstream convention for domains without solo support
(airline/retail/banking_knowledge behave the same way).
"""

import pytest

from tau2.data_model.tasks import EnvFunctionCall
from tau2.domains.campus.environment import get_environment, get_tasks


def _task(task_id: str):
    return next(
        task for task in get_tasks(task_split_name=None) if task.id == task_id
    )


class _SyncCounter:
    """Wraps env.sync_tools with a call counter (instance-level)."""

    def __init__(self, env):
        self.n = 0
        self._orig = env.sync_tools
        env.sync_tools = self._call

    def _call(self):
        self.n += 1
        return self._orig()


def test_set_state_delegation_replays_actions_and_final_sync():
    """Guard ①: campus set_state = apply own-side data → re-share
    pointers → delegate to base. The base must replay every
    initialization_action through run_env_function_call (sync each) and
    run one final sync — corpus message_history is empty (0/50 tasks), so
    the expected count is len(actions) + 1."""
    task = _task("M04")  # has both agent_data and user_data
    init = task.initial_state
    env = get_environment()
    fresh = get_environment()
    counter = _SyncCounter(env)

    env.set_state(
        initialization_data=init.initialization_data,
        initialization_actions=init.initialization_actions,
        message_history=(init.message_history or []),
        strict=True,
    )

    assert counter.n == len(init.initialization_actions or []) + 1, (
        "upstream set_state sync points moved: expected one sync per "
        "initialization_action (run_env_function_call) plus the final sync"
    )
    # agent_data applied to the agent DB, user_data to the user DB
    # (M04's data touches exactly these tables — verified against a fresh
    # sibling environment constructed in the same process)
    assert env.tools.db.exam_arrangements != fresh.tools.db.exam_arrangements
    assert env.tools.db.deferral_requests != fresh.tools.db.deferral_requests
    assert env.user_tools.db.app_todos != fresh.user_tools.db.app_todos
    assert env.user_tools.db.pending_signatures != fresh.user_tools.db.pending_signatures
    # initialization_actions really ran through the delegated replay
    # (session binding lives outside the DB hashes, so only this pins it)
    assert env.user_tools.bound_student_id == init.initialization_actions[0].arguments[
        "student_id"
    ]


def test_sync_tools_call_timing():
    """Guard ②: make_tool_call never syncs (documented upstream
    contract — campus rides settlement on the tool execution path instead);
    run_env_function_call syncs exactly once per call."""
    env = get_environment()
    counter = _SyncCounter(env)

    env.make_tool_call(
        tool_name="create_ticket",
        requestor="assistant",
        student_id="S20230103",
        category="咨询",
        module="其他",
        title="时序守卫探针",
        content="sync timing guard",
    )
    assert counter.n == 0, (
        "upstream make_tool_call started calling sync_tools — campus's "
        "settle-on-execution-path assumption needs re-review"
    )

    env.run_env_function_call(
        EnvFunctionCall(
            env_type="assistant",
            func_name="get_student_details",
            arguments={"student_id": "S20230103"},
        )
    )
    assert counter.n == 1, "run_env_function_call must sync exactly once"


def test_shared_db_pointers_after_set_state():
    """Guard ③: after set_state the toolkit pair shares the same
    DB instances again, and the two DBs remain distinct objects."""
    task = _task("E01")
    init = task.initial_state
    env = get_environment()
    env.set_state(
        initialization_data=init.initialization_data,
        initialization_actions=init.initialization_actions,
        message_history=(init.message_history or []),
        strict=True,
    )
    assert env.user_tools.main_db is env.tools.db
    assert env.tools.user_db is env.user_tools.db
    assert env.user_tools.agent_tools is env.tools
    assert env.tools.db is not env.user_tools.db, (
        "two-DB domain must keep distinct agent/user DB instances"
    )


def test_get_environment_rejects_solo_mode():
    """campus has no solo task surface (50/50 ticket=null) — the
    constructor must reject solo_mode instead of silently enabling it."""
    with pytest.raises(ValueError, match="Solo mode not supported for campus"):
        get_environment(solo_mode=True)
