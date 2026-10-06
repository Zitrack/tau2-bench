"""Release-snapshot regression guards for the campus domain (W3, P1-13).

Freezes two kinds of "must not drift back" facts as pytest assertions:

1. **Runtime metadata constants** exposed by ``tau2.domains.campus``
   (``__version__`` / ``POLICY_VERSION`` / ``SCORING_PROTOCOL``).
2. **The W1/W2 data-cleaning results** on the two public data files:
   - ``policy.md``: zero internal meta-annotations — "坑点" pitfall tags,
     ``v1.x/F|R|M`` internal version labels, and the ``P1-10`` changelog
     reference (W1 scrub);
   - ``tasks.json``: zero ``description.notes`` keys (W1), zero ``issues``
     keys, and zero exam-point number hints (``P0[0-9]``) / "坑点" in the
     agent-visible ``purpose`` / ``relevant_policies`` fields (W2 scrub).

Version linkage: ``POLICY_VERSION == "1.4.1"`` is the **current contract
value**. If the v2.0.0 release batch bumps it (e.g. to ``1.4.1``), this
assertion and the release manifest must be updated **in the same change**
(W-SERIES-PLAN §v2.0.0 发布批 §1) — they move together.

A failure here means a cleaned field regressed (or an authorized version
bump landed without updating this snapshot): fix the drift or update the
snapshot deliberately — never weaken the assertions to get green.
"""

import json
import re

import pytest

import tau2.domains.campus as campus
from tau2.domains.campus.utils import CAMPUS_POLICY_PATH, CAMPUS_TASK_SET_PATH

# --- fixtures (read once per module) -------------------------------------


@pytest.fixture(scope="module")
def policy_text() -> str:
    return CAMPUS_POLICY_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def tasks_text() -> str:
    return CAMPUS_TASK_SET_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def tasks(tasks_text) -> list[dict]:
    return json.loads(tasks_text)


# --- 1. runtime metadata constants ---------------------------------------


def test_version_is_semver():
    """__version__ tracks the campus benchmark axis (campus-vX.Y.Z tags)."""
    assert re.fullmatch(r"\d+\.\d+\.\d+", campus.__version__)


def test_policy_version_contract():
    """Current contract value — bump together with the release manifest."""
    assert campus.POLICY_VERSION == "1.4.1"


def test_scoring_protocol_contract():
    assert campus.SCORING_PROTOCOL == "tau2-v1.0.1-compatible"


# --- 2. policy.md — W1 meta-annotation scrub must hold --------------------


def test_policy_has_no_pitfall_annotations(policy_text):
    assert "坑点" not in policy_text


def test_policy_has_no_internal_version_tags(policy_text):
    """v1.x/F|R|M labels were internal review tags, not policy content."""
    assert re.search(r"v1\.[0-9]/[FRM]", policy_text) is None


def test_policy_has_no_p1_10_reference(policy_text):
    assert "P1-10" not in policy_text


# --- 3. tasks.json — W1/W2 scrubs must hold -------------------------------


def test_task_count(tasks):
    assert len(tasks) == 50


def test_descriptions_have_no_notes_key(tasks):
    """W1 stripped description.notes from 50/50 tasks (gold-hinting QA)."""
    offenders = [t["id"] for t in tasks if "notes" in t["description"]]
    assert not offenders, f"description.notes reintroduced: {offenders}"


def test_tasks_text_has_no_issues_key(tasks_text):
    assert '"issues"' not in tasks_text


def test_agent_visible_fields_free_of_exam_point_hints(tasks):
    """W2 scrub: no P0x-style exam-point numbers or 坑点 in fields the
    agent can see through TaskDescription rendering."""
    offenders = []
    for task in tasks:
        description = task["description"]
        for field in ("purpose", "relevant_policies"):
            value = description.get(field) or ""
            if re.search(r"P0[0-9]", value) or "坑点" in value:
                offenders.append(f"{task['id']}.{field}")
    assert not offenders, f"exam-point hints reintroduced: {offenders}"
