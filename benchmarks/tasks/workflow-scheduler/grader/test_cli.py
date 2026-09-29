from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reference import run_reference

TASK_DIR = Path(os.environ["AGENTBENCH_TASK_DIR"])
WORKSPACE = Path.cwd()
ENV = os.environ.copy()


def run_cli(workflows):
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "in.json"
        output = Path(tmp) / "out.json"
        source.write_text(json.dumps(workflows), encoding="utf-8")
        proc = subprocess.run([sys.executable, "-m", "flowbench", str(source), "--output", str(output)],
                              cwd=WORKSPACE, env=ENV, text=True, capture_output=True, timeout=30)
        return proc, json.loads(output.read_text(encoding="utf-8")) if output.exists() else None


class WorkflowContractTests(unittest.TestCase):
    def test_supplied_workflows_match_reference(self):
        workflows = json.loads((TASK_DIR / "inputs/workflows.json").read_text(encoding="utf-8"))
        proc, actual = run_cli(workflows)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(actual, [run_reference(w) for w in workflows])
        saved = WORKSPACE / "submission/schedules.json"
        self.assertTrue(saved.is_file(), "agent must also save the requested schedules.json")
        self.assertEqual(json.loads(saved.read_text(encoding="utf-8")), [run_reference(w) for w in workflows])

    def test_input_order_does_not_change_schedule(self):
        workflows = json.loads((TASK_DIR / "inputs/workflows.json").read_text(encoding="utf-8"))
        changed = []
        for workflow in workflows:
            copy = dict(workflow)
            copy["tasks"] = list(reversed(workflow["tasks"]))
            changed.append(copy)
        proc, actual = run_cli(changed)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(actual, [run_reference(w) for w in workflows])

    def test_generated_acyclic_workflows(self):
        rng = random.Random(918273)
        workflows = []
        for case in range(12):
            tasks = []
            count = 8 + case
            for i in range(count):
                dependencies = [f"j{j:02d}" for j in range(i) if rng.random() < 0.18]
                maximum = rng.randint(1, 3)
                tasks.append({"id": f"j{i:02d}", "duration": rng.randint(1, 7),
                              "depends_on": dependencies, "max_attempts": maximum,
                              "fail_attempts": rng.randint(0, maximum)})
            workflows.append({"workflow_id": f"generated-{case}", "workers": rng.randint(1, 4), "tasks": tasks})
        proc, actual = run_cli(workflows)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(actual, [run_reference(w) for w in workflows])

    def test_duplicate_ids_are_rejected(self):
        workflow = {"workflow_id": "bad", "workers": 1, "tasks": [
            {"id": "x", "duration": 1}, {"id": "x", "duration": 2}]}
        self.assertNotEqual(run_cli([workflow])[0].returncode, 0)

    def test_missing_dependency_is_rejected(self):
        workflow = {"workflow_id": "bad", "workers": 1, "tasks": [
            {"id": "x", "duration": 1, "depends_on": ["absent"]}]}
        self.assertNotEqual(run_cli([workflow])[0].returncode, 0)

    def test_cycle_is_rejected(self):
        workflow = {"workflow_id": "bad", "workers": 1, "tasks": [
            {"id": "x", "duration": 1, "depends_on": ["y"]},
            {"id": "y", "duration": 1, "depends_on": ["x"]}]}
        self.assertNotEqual(run_cli([workflow])[0].returncode, 0)

    def test_boolean_is_not_accepted_as_integer(self):
        workflow = {"workflow_id": "bad", "workers": True, "tasks": [{"id": "x", "duration": 1}]}
        self.assertNotEqual(run_cli([workflow])[0].returncode, 0)


if __name__ == "__main__":
    unittest.main()
