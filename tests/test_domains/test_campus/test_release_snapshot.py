"""Release-snapshot regression guards for the campus domain (W3, P1-13).

Freezes two kinds of "must not drift back" facts as pytest assertions:

1. **Runtime metadata constants** exposed by ``tau2.domains.campus``
   (``__version__`` / ``POLICY_VERSION`` / ``SCORING_PROTOCOL``).
2. **The data-cleaning results** on the two public data files:
   - ``policy.md``: zero internal meta-annotations — "坑点" pitfall tags,
     ``v1.x/F|R|M`` internal version labels, and the ``P1-10`` changelog
     reference (W1 scrub); plus a single-line version footer
     (``本规程版本：vX.Y.Z（YYYY-MM-DD）`` as the exact last line, exactly
     once, version equal to ``POLICY_VERSION``);
   - ``tasks.json``: zero ``description.notes`` keys (W1), zero ``issues``
     keys, and zero exam-point number hints (``P0[0-9]``) / "坑点" in the
     agent-visible ``purpose`` / ``relevant_policies`` fields (W2 scrub);
     plus an **all-string-leaves** census — no authoring marker
     (金标 / D-S# / v1.x-bracket / 钉死 / 抽签 / 考点 / tools-spec /
     E-DATA / leading "考 " / M#-LETTER / P#-#) anywhere in any string
     leaf of any task (scope: the whole file, not just the
     agent-visible fields).

Version linkage: ``POLICY_VERSION == "1.4.2"`` is the **current contract
value**. If a future release bumps it, this assertion and the release
manifest must be updated **in the same change** — they move together.

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
    assert campus.POLICY_VERSION == "1.4.2"


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


# --- 4. all-string-leaves marker census + policy version footer ------------

# Authoring/internal markers scrubbed from the public data. Scope: EVERY
# string leaf of tasks.json (not only the agent-visible fields). "考 " is
# leaf-anchored (leading only) so words like "缺考" never match.
INTERNAL_MARKER_PATTERNS = {
    "金标": r"金标",
    "D-S": r"D-S\d",
    "v1.x-bracket": r"v1\.\d[/（( ]",
    "钉死": r"钉死",
    "抽签": r"抽签",
    "考点": r"考点",
    "tools-spec": r"tools-spec",
    "E-DATA": r"E-DATA",
    "leading-考": r"^考 ",
    "M#-LETTER": r"M\d+-[A-Z]",
    "P#-#": r"P\d+-\d",
}

POLICY_FOOTER_RE = re.compile(r"本规程版本：v(\d+\.\d+\.\d+)（(\d{4}-\d{2}-\d{2})）")


def _walk_strings(node, path=""):
    """Yield (path, text) for every string leaf in a JSON-like structure."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk_strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk_strings(value, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def test_tasks_all_string_leaves_free_of_internal_markers(tasks):
    """No authoring marker in ANY string leaf of tasks.json — including
    persona, actions[].info, instructions, etc."""
    offenders = []
    for task in tasks:
        for path, text in _walk_strings(task):
            for name, pattern in INTERNAL_MARKER_PATTERNS.items():
                if re.search(pattern, text):
                    offenders.append(f"{task['id']}{path}:{name}")
    assert not offenders, f"internal markers reintroduced: {offenders}"


def test_policy_has_version_footer(policy_text):
    """policy.md ends with exactly one single-line version footer whose
    version equals POLICY_VERSION (footer and constant move together)."""
    lines = [line for line in policy_text.splitlines() if line.strip()]
    assert lines, "policy.md is empty"
    last = lines[-1]
    match = POLICY_FOOTER_RE.fullmatch(last)
    assert match, f"policy.md last line must be the version footer, got: {last!r}"
    footers = [line for line in lines if line.startswith("本规程版本：")]
    assert len(footers) == 1, f"expected exactly one version footer: {footers}"
    assert match.group(1) == campus.POLICY_VERSION, (
        f"policy footer v{match.group(1)} != POLICY_VERSION "
        f"{campus.POLICY_VERSION} — bump both in the same change"
    )
