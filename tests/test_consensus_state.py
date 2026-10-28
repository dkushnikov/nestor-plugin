"""Executable record of the pal `consensus` state contract Nestor depends on.

Nestor's `references/consensus-execution.md` says: one unfinished consensus
workflow per pal process; `continuation_id` does not isolate parallel workflows;
`models` is read at step 1 only; a failed seat is appended as `status: error`
and the workflow continues. These are facts about pal's `ConsensusTool`, not
about Nestor's text — so they can rot silently when pal is upgraded. This test
extracts `execute_workflow` from the pal checkout by AST (no server import, no
network, no model calls) and drives it with stubs. Origin: Codex audit
2026-10-27 (F1/F3), harness reproduced and extended by Atlas.

Run:  PAL_SRC=<path to pal-mcp-server checkout> python3 -m pytest tests/
      (or python3 tests/test_consensus_state.py). Skips when PAL_SRC is unset or wrong.
"""
import ast
import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

PAL_SRC = Path(os.environ.get("PAL_SRC", "pal-mcp-server"))
CONSENSUS = PAL_SRC / "tools" / "consensus.py"


def _load_execute_workflow():
    tree = ast.parse(CONSENSUS.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ConsensusTool")
    method = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "execute_workflow")
    ns = {"Any": Any, "json": json, "TextContent": SimpleNamespace, "ConsolidatedFindings": dict,
          "create_thread": lambda name, args: "id-" + args["step"]}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(CONSENSUS), "exec"), ns)
    return ns["execute_workflow"]


class Harness:
    """Minimal stand-in for ConsensusTool state; `_consult_model` can be told to fail."""
    execute_workflow = None

    def __init__(self, failing=()):
        self.original_proposal = None
        self.initial_prompt = None
        self.models_to_consult = []
        self.accumulated_responses = []
        self.work_history = []
        self.failing = set(failing)

    def get_workflow_request_model(self):
        return lambda **kw: SimpleNamespace(**({"continuation_id": None, "models": None} | kw))

    def get_name(self):
        return "consensus"

    def store_initial_issue(self, question):
        self.original_proposal = question

    def prepare_step_data(self, request):
        return {}

    def _update_consolidated_findings(self, data):
        pass

    async def _consult_model(self, model, request):
        if model["model"] in self.failing:
            return {"model": model["model"], "stance": "neutral", "status": "error", "error": "boom"}
        return {"model": model["model"], "stance": "neutral", "status": "success",
                "verdict": "ok", "question": self.original_proposal}

    def customize_workflow_response(self, data, request):
        return data

    def _add_workflow_metadata(self, data, arguments):
        pass

    def store_conversation_turn(self, *args):
        pass

    def _build_continuation_offer(self, *args):
        return None


def _call(h, prefix, step, cid=None, models_prefix=None, total=3):
    args = dict(step="Q-" + prefix, step_number=step, total_steps=total, next_step_required=step < total,
                findings="offline", continuation_id=cid)
    if step == 1 or models_prefix:
        args["models"] = [{"model": f"{models_prefix or prefix}{i}"} for i in range(1, 4)]
    return json.loads(asyncio.run(h.execute_workflow(args))[0].text)


def setup_module(module=None):
    if not CONSENSUS.exists():
        import pytest
        pytest.skip(f"pal checkout not found at {PAL_SRC}", allow_module_level=True)
    Harness.execute_workflow = _load_execute_workflow()


def test_serial_workflow_consults_roster_in_order():
    h = Harness()
    rows = [_call(h, "A", i, None if i == 1 else "id-Q-A") for i in range(1, 4)]
    assert [r["model_consulted"] for r in rows] == ["A1", "A2", "A3"]
    assert rows[-1]["status"] == "consensus_workflow_complete"


def test_interleaved_workflows_contaminate_regardless_of_continuation_id():
    for cid in (None, "id-Q-A"):
        h = Harness()
        _call(h, "A", 1)
        _call(h, "B", 1)  # second workflow's step 1 overwrites the instance state
        r = _call(h, "A", 2, cid)
        assert r["model_consulted"] == "B2", cid
        assert r["model_response"]["question"] == "Q-B", cid


def test_models_passed_on_step_2_are_ignored():
    h = Harness()
    _call(h, "A", 1)
    r = _call(h, "A", 2, "id-Q-A", models_prefix="F")
    assert r["model_consulted"] == "A2"


def test_failed_seat_is_appended_and_workflow_continues():
    h = Harness(failing={"A2"})
    _call(h, "A", 1)
    r2 = _call(h, "A", 2, "id-Q-A")
    r3 = _call(h, "A", 3, "id-Q-A")
    assert r2["model_response"]["status"] == "error"
    assert r3["status"] == "consensus_workflow_complete"
    # total_responses counts the error entry too — usable answers must be counted by status
    assert r3["complete_consensus"]["total_responses"] == 3
    usable = [m for m in h.accumulated_responses if m.get("status") == "success"]
    assert len(usable) == 2


def test_total_steps_is_normalised_to_roster_size():
    h = Harness()
    r = _call(h, "A", 1, total=4)
    assert r["total_steps"] == 3


if __name__ == "__main__":
    setup_module()
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except AssertionError as e:
                failures += 1
                print("FAIL", name, e)
    sys.exit(1 if failures else 0)
