from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from . import __version__

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "benchmarks" / "tasks"
RESULTS_DIR = ROOT / "results" / "runs"
CONFIG_DIR = ROOT / ".agentbench"
CONFIG_PATH = CONFIG_DIR / "agents.json"
RECEIPT_NAME = "run-receipt.json"


class BenchError(Exception):
    pass


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchError(f"Cannot read JSON {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_tasks() -> dict[str, tuple[dict[str, Any], Path]]:
    tasks: dict[str, tuple[dict[str, Any], Path]] = {}
    for manifest in sorted(TASKS_DIR.glob("*/task.json")):
        task = read_json(manifest)
        task_id = task["id"]
        context_files = task.get("context_files")
        if not isinstance(context_files, list) or not context_files:
            raise BenchError(f"Task {task_id} must declare one or more context_files")
        for rel in context_files:
            if not isinstance(rel, str) or not rel.startswith("context/"):
                raise BenchError(f"Task {task_id} has an invalid context file path: {rel!r}")
            context_path = (manifest.parent / rel).resolve()
            if manifest.parent.resolve() not in context_path.parents or not context_path.is_file():
                raise BenchError(f"Task {task_id} is missing declared context file: {rel}")
        for field in ("input_files", "starter_files", "generated_input_files", "output_files"):
            if not isinstance(task.get(field), list):
                raise BenchError(f"Task {task_id} must declare an array named {field}")
        for field in ("input_files", "starter_files"):
            for rel in task[field]:
                path = (manifest.parent / rel).resolve()
                if manifest.parent.resolve() not in path.parents or not path.is_file():
                    raise BenchError(f"Task {task_id} is missing declared {field} file: {rel}")
        for rel in task["generated_input_files"]:
            if not isinstance(rel, str) or not rel.startswith("inputs/"):
                raise BenchError(f"Task {task_id} has an invalid generated input path: {rel!r}")
        for rel in task["output_files"]:
            if not isinstance(rel, str) or not rel.startswith("submission/"):
                raise BenchError(f"Task {task_id} has an invalid output path: {rel!r}")
        expected_rel = task.get("evaluator", {}).get("expected")
        if expected_rel:
            expected_path = (manifest.parent / expected_rel).resolve()
            if manifest.parent.resolve() not in expected_path.parents or not expected_path.is_file():
                raise BenchError(f"Task {task_id} is missing evaluator reference data: {expected_rel}")
        if task_id in tasks:
            raise BenchError(f"Duplicate task ID: {task_id}")
        tasks[task_id] = (task, manifest.parent)
    return tasks


def load_agents() -> list[dict[str, Any]]:
    if not CONFIG_PATH.exists():
        raise BenchError("Agent profiles are not configured. Run: python -m agentbench init")
    data = read_json(CONFIG_PATH)
    agents = data.get("agents", [])
    if not isinstance(agents, list):
        raise BenchError(f"{CONFIG_PATH} must contain an 'agents' array")
    return agents


def cmd_init(_: argparse.Namespace) -> int:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        print(f"Already exists: {CONFIG_PATH}")
        return 0
    example = ROOT / ".agentbench" / "agents.example.json"
    if not example.exists():
        raise BenchError(f"Missing example profile file: {example}")
    shutil.copyfile(example, CONFIG_PATH)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Created {CONFIG_PATH}")
    print("Edit this file to add the command or adapter used by each AI product.")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    tasks = load_tasks()
    print(f"Agent Benchmark {__version__}: {len(tasks)} runnable tasks")
    print(f"{'TASK ID':38} {'CATEGORY':22} {'LEVEL':22} {'ORACLE':20} STATUS")
    for task_id, (task, _) in tasks.items():
        print(f"{task_id:38} {task.get('category','-'):22} {task.get('difficulty','-'):22} "
              f"{task['evaluator']['type']:20} {task.get('status','draft')}")
    return 0


def _load_environment(env_spec: dict[str, str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
    for key, value in env_spec.items():
        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            found = os.environ.get(name)
            if found is None:
                raise BenchError(f"Required environment variable {name} is not set")
            return found
        resolved[key] = pattern.sub(replace, value)
    return resolved


def _task_prompt(task: dict[str, Any], task_dir: Path, workspace: Path) -> str:
    prompt_path = task_dir / "prompt.md"
    if not prompt_path.exists():
        raise BenchError(f"Task prompt missing: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def _sha256_files(paths: list[Path], relative_to: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(relative_to).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _workspace_input_hash(workspace: Path) -> str:
    files = [workspace / "task.json"]
    for folder in ("context", "inputs", "submission"):
        directory = workspace / folder
        if directory.exists():
            files.extend(p for p in directory.rglob("*") if p.is_file())
    return _sha256_files(files, workspace)


def _prepare_workspace(task_dir: Path, run_dir: Path, task: dict[str, Any], rows: int, seed: int) -> Path:
    workspace = run_dir / "workspace"
    workspace.mkdir(parents=True)
    shutil.copyfile(task_dir / "task.json", workspace / "task.json")
    starter = task_dir / "starter"
    if starter.exists():
        shutil.copytree(starter, workspace, dirs_exist_ok=True)
    inputs = task_dir / "inputs"
    if inputs.exists():
        shutil.copytree(inputs, workspace / "inputs", dirs_exist_ok=True)
    context = task_dir / "context"
    if context.exists():
        shutil.copytree(context, workspace / "context", dirs_exist_ok=True)
    (workspace / "submission").mkdir()
    if task["id"] == "data.clean-large-csv.v1":
        _generate_events(workspace / "inputs" / "events.csv", rows, seed)
    return workspace


def _generate_events(path: Path, rows: int, seed: int) -> None:
    import random
    from datetime import datetime, timedelta, timezone

    if rows < 1:
        raise BenchError("--rows must be at least 1")
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["record_id", "email", "event_time", "amount"])
        previous_id = ""
        for i in range(rows):
            record_id = f"evt-{i:09d}"
            if i > 0 and i % 997 == 0:
                record_id = previous_id
            else:
                previous_id = record_id
            email = f"user{i % 50000}@example.test"
            if i % 89 == 0:
                email = f" User{i % 50000}@EXAMPLE.TEST "
            if i % 991 == 0:
                email = "bad-address"
            timestamp = base + timedelta(seconds=rng.randrange(0, 20_000_000))
            stamp = timestamp.isoformat().replace("+00:00", "Z")
            writer.writerow([record_id, email, stamp, f"{rng.randrange(1, 500000) / 100:.2f}"])


def _run_process(profile: dict[str, Any], prompt: str, workspace: Path,
                 run_dir: Path, task_id: str) -> dict[str, Any]:
    command = profile.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
        raise BenchError(f"Agent {profile.get('id')} needs a non-empty command array in {CONFIG_PATH}")
    submission = workspace / "submission"
    metrics_path = run_dir / "adapter-metrics.json"
    replacements = {
        "{workspace}": str(workspace), "{submission}": str(submission),
        "{prompt_file}": str(run_dir / "prompt.md"), "{run_dir}": str(run_dir),
        "{task_id}": task_id, "{metrics_file}": str(metrics_path), "{repo}": str(ROOT),
    }
    (run_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    actual_command = [arg.format(**{key.strip("{}"): value for key, value in replacements.items()}) for arg in command]
    env = os.environ.copy()
    env.update(_load_environment(profile.get("env", {})))
    env.update({
        "AGENTBENCH_TASK_ID": task_id,
        "AGENTBENCH_WORKSPACE": str(workspace),
        "AGENTBENCH_SUBMISSION": str(submission),
        "AGENTBENCH_PROMPT_FILE": str(run_dir / "prompt.md"),
        "AGENTBENCH_METRICS_FILE": str(metrics_path),
    })
    timeout = int(profile.get("timeout_seconds", 900))
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            actual_command,
            cwd=workspace,
            input=prompt if profile.get("stdin", "prompt") == "prompt" else None,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            env=env,
            shell=False,
            check=False,
        )
        timed_out = False
        return_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        return_code = None
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    elapsed = round((time.perf_counter() - start) * 1000)
    (run_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
    (run_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    metrics: dict[str, Any] = {"provider_cost": None, "currency": None, "input_tokens": None,
                               "output_tokens": None, "model_calls": None, "source": "unavailable"}
    parser = profile.get("parser", "none")
    if parser in ("claude-code-json", "json"):
        parsed = _find_json_result(stdout)
        if parsed:
            metrics.update(_usage_from_json(parsed, parser))
    if metrics_path.exists():
        adapter_metrics = read_json(metrics_path)
        metrics.update(adapter_metrics)
        metrics["source"] = adapter_metrics.get("source", "adapter")
    reported = _read_agent_receipt(submission / RECEIPT_NAME, task_id)
    return {
        "command": actual_command,
        "exit_code": return_code,
        "timed_out": timed_out,
        "wall_time_ms": elapsed,
        "usage": metrics,
        "agent_receipt": reported,
    }


def _find_json_result(stdout: str) -> dict[str, Any] | None:
    candidates = [stdout.strip()]
    candidates.extend(line.strip() for line in reversed(stdout.splitlines()))
    for candidate in candidates:
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            if parsed.get("type") == "result" or "total_cost_usd" in parsed or "usage" in parsed:
                return parsed
            # Codex and other JSONL adapters can put the final usage in a result event.
        elif isinstance(parsed, list):
            for item in reversed(parsed):
                if isinstance(item, dict) and (item.get("type") == "result" or "total_cost_usd" in item):
                    return item
    for line in reversed(stdout.splitlines()):
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and (item.get("type") == "result" or "total_cost_usd" in item or "usage" in item):
            return item
    return None


def _usage_from_json(value: dict[str, Any], parser: str) -> dict[str, Any]:
    usage = value.get("usage") if isinstance(value.get("usage"), dict) else {}
    cost = value.get("total_cost_usd", value.get("cost", usage.get("cost")))
    return {
        "provider_cost": cost,
        "currency": "USD" if cost is not None and "total_cost_usd" in value else value.get("currency"),
        "input_tokens": usage.get("input_tokens", value.get("input_tokens")),
        "output_tokens": usage.get("output_tokens", value.get("output_tokens")),
        "cached_input_tokens": usage.get("cache_read_input_tokens", usage.get("cached_input_tokens")),
        "model_calls": value.get("num_turns", usage.get("model_calls")),
        "tool_calls": value.get("tool_calls"),
        "provider_duration_ms": value.get("duration_ms"),
        "session_id": value.get("session_id"),
        "source": "provider_cli_json" if parser == "claude-code-json" else "agent_cli_json",
    }


def _read_agent_receipt(path: Path, task_id: str) -> dict[str, Any]:
    if not path.exists():
        return {"valid": False, "error": "receipt file missing"}
    try:
        receipt = read_json(path)
        reported = receipt["agent_reported"]
        required = {"model", "input_tokens", "output_tokens", "cached_input_tokens", "model_calls",
                    "tool_calls", "wall_time_ms", "cost", "cost_currency", "cost_basis"}
        if receipt.get("schema_version") != 1 or receipt.get("task_id") != task_id or not required.issubset(reported):
            raise ValueError("receipt does not satisfy schema v1")
        if set(reported) != required:
            raise ValueError("agent_reported contains unexpected fields")
        if reported["model"] is not None and not isinstance(reported["model"], str):
            raise ValueError("model must be a string or null")
        if reported["cost_currency"] is not None and not isinstance(reported["cost_currency"], str):
            raise ValueError("cost_currency must be a string or null")
        if reported["cost_basis"] not in {"provider_reported", "rate_card_estimate", "subscription", "unknown"}:
            raise ValueError("invalid cost_basis")
        for field in required - {"model", "cost_currency", "cost_basis"}:
            value = reported[field]
            if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
                raise ValueError(f"{field} must be a non-negative number or null")
            if field != "cost" and value is not None and not isinstance(value, int):
                raise ValueError(f"{field} must be an integer or null")
        if not isinstance(receipt.get("unavailable_fields"), list):
            raise ValueError("unavailable_fields must be an array")
        for item in receipt["unavailable_fields"]:
            if not isinstance(item, dict) or set(item) != {"field", "reason"} or not all(isinstance(item[k], str) for k in item):
                raise ValueError("each unavailable field needs string field and reason values")
        if receipt.get("status") not in {"completed", "partial", "failed", "timed_out"}:
            raise ValueError("invalid status")
        if set(receipt) - {"schema_version", "task_id", "status", "agent_reported", "unavailable_fields", "notes"}:
            raise ValueError("receipt contains unexpected fields")
        if "notes" in receipt and not isinstance(receipt["notes"], str):
            raise ValueError("notes must be a string")
        return {"valid": True, "data": receipt}
    except (ValueError, KeyError, TypeError, BenchError) as exc:
        return {"valid": False, "error": str(exc)}


def evaluate(task: dict[str, Any], task_dir: Path, workspace: Path) -> dict[str, Any]:
    submission = workspace / "submission"
    kind = task["evaluator"]["type"]
    details: list[str] = []
    passed = False
    if kind == "json-exact":
        output = submission / task["evaluator"].get("output", "result.json")
        expected = read_json(task_dir / task["evaluator"]["expected"])
        try:
            actual = read_json(output)
            passed = actual == expected
            if not passed:
                details.append("JSON content differs from the reference")
        except BenchError as exc:
            details.append(str(exc))
    elif kind == "bugfix-python":
        module = submission / task["evaluator"].get("module", "solution.py")
        passed, details = _eval_bugfix(module)
    elif kind == "pr-review-json":
        output = submission / task["evaluator"].get("output", "findings.json")
        expected = read_json(task_dir / task["evaluator"]["expected"])
        try:
            actual = read_json(output)
            found = actual.get("findings", [])
            expected_findings = expected if isinstance(expected, list) else [expected]
            fields = ("path", "line", "severity")
            expected_keys = [tuple(item.get(key) for key in fields) for item in expected_findings]
            found_keys = [tuple(item.get(key) for key in fields) for item in found if isinstance(item, dict)] if isinstance(found, list) else []
            passed = (len(found_keys) == len(found) == len(expected_keys) and
                      len(set(found_keys)) == len(found_keys) and set(found_keys) == set(expected_keys) and
                      all(isinstance(item.get("rule_id"), str) and item["rule_id"].strip() and
                          isinstance(item.get("explanation"), str) and item["explanation"].strip()
                          for item in found if isinstance(item, dict)))
            if not passed:
                details.append(f"Expected exactly {len(expected_keys)} seeded defects with matching path, line, and severity; got {len(found_keys)} findings")
        except (BenchError, AttributeError, TypeError) as exc:
            details.append(f"Invalid findings JSON: {exc}")
    elif kind == "data-clean-csv":
        passed, details = _eval_data_clean(workspace)
    elif kind == "ascii-exact":
        output = submission / task["evaluator"].get("output", "art.txt")
        source = workspace / "inputs" / "portrait.pgm"
        try:
            expected = _pgm_to_ascii(source.read_text(encoding="ascii"))
            actual = output.read_text(encoding="ascii")
            passed = actual.rstrip("\n") == expected
            if not passed:
                details.append("ASCII rendering differs from the fixed pixel-to-character reference")
        except (OSError, UnicodeError, ValueError) as exc:
            details.append(str(exc))
    elif kind == "xlsx-contract":
        passed, details = _eval_xlsx(task, task_dir, workspace)
    elif kind == "png-properties":
        passed, details = _eval_png(task, submission)
    elif kind == "mp4-properties":
        passed, details = _eval_mp4(task, submission)
    else:
        raise BenchError(f"Unknown evaluator type: {kind}")
    return {"passed": passed, "type": kind, "details": details}


def _eval_bugfix(path: Path) -> tuple[bool, list[str]]:
    details: list[str] = []
    if not path.exists():
        return False, ["submission/solution.py missing"]
    import importlib.util
    spec = importlib.util.spec_from_file_location("agentbench_submission", path)
    if spec is None or spec.loader is None:
        return False, ["cannot load solution.py"]
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        fn = module.calculate_total
        cases = [(10.0, 2, 0.0, 20.0), (19.99, 3, 0.2, 71.964), (0.0, 8, 0.2, 0.0)]
        for price, quantity, tax, expected in cases:
            actual = fn(price, quantity, tax)
            if not math.isclose(float(actual), expected, rel_tol=0, abs_tol=0.0001):
                details.append(f"calculate_total({price}, {quantity}, {tax}) returned {actual}, expected {expected}")
        try:
            fn(10, -1, 0.1)
            details.append("negative quantity was not rejected")
        except (ValueError, TypeError):
            pass
    except Exception as exc:
        details.append(f"could not run calculate_total: {type(exc).__name__}: {exc}")
    return not details, details


def _parse_stamp(value: str) -> str:
    from datetime import datetime, timezone
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _valid_email(value: str) -> bool:
    return re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value.strip()) is not None


def _reference_clean(input_path: Path) -> tuple[list[dict[str, str]], dict[str, int]]:
    with input_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    accepted: dict[str, dict[str, str]] = {}
    rejected = duplicates = 0
    for row in rows:
        email = row["email"].strip().lower()
        if not _valid_email(email):
            rejected += 1
            continue
        record_id = row["record_id"].strip()
        if record_id in accepted:
            duplicates += 1
            continue
        accepted[record_id] = {"record_id": record_id, "email": email,
                               "event_time": _parse_stamp(row["event_time"]),
                               "amount": f"{float(row['amount']):.2f}"}
    cleaned = sorted(accepted.values(), key=lambda r: (r["event_time"], r["record_id"]))
    return cleaned, {"input_rows": len(rows), "output_rows": len(cleaned),
                     "rejected_rows": rejected, "duplicate_rows": duplicates}


def _eval_data_clean(workspace: Path) -> tuple[bool, list[str]]:
    submission = workspace / "submission"
    script = submission / "solution.py"
    if not script.exists():
        return False, ["submission/solution.py missing"]
    input_path = workspace / "inputs" / "events.csv"
    cleaned_path = submission / "cleaned.csv"
    summary_path = submission / "summary.json"
    try:
        result = subprocess.run([sys.executable, str(script), "--input", str(input_path),
                                 "--output", str(cleaned_path), "--summary", str(summary_path)],
                                cwd=workspace, capture_output=True, text=True, timeout=180, check=False)
        if result.returncode != 0:
            return False, [f"solution.py exited {result.returncode}: {result.stderr[-2000:]}"]
        expected_rows, expected_summary = _reference_clean(input_path)
        with cleaned_path.open(newline="", encoding="utf-8") as stream:
            actual_rows = list(csv.DictReader(stream))
        actual_summary = read_json(summary_path)
        if actual_rows != expected_rows:
            return False, [f"cleaned.csv differs from reference ({len(actual_rows)} rows; expected {len(expected_rows)})"]
        if actual_summary != expected_summary:
            return False, [f"summary.json differs from reference: {actual_summary!r}"]
        return True, []
    except (OSError, subprocess.TimeoutExpired, BenchError, csv.Error) as exc:
        return False, [str(exc)]


def _pgm_to_ascii(text: str) -> str:
    tokens = [line.split("#", 1)[0] for line in text.splitlines()]
    values = " ".join(tokens).split()
    if not values or values[0] != "P2":
        raise ValueError("expected a plain PGM P2 image")
    width, height, maximum = map(int, values[1:4])
    pixels = list(map(int, values[4:]))
    if width * height != len(pixels) or maximum <= 0:
        raise ValueError("invalid PGM dimensions or pixels")
    ramp = "@%#*+=-:. "
    lines = []
    for y in range(height):
        chars = []
        for x in range(width):
            pixel = pixels[y * width + x]
            index = min(len(ramp) - 1, pixel * (len(ramp) - 1) // (maximum + 1))
            chars.append(ramp[index])
        lines.append("".join(chars).rstrip())
    return "\n".join(lines) + "\n"


def _ns(root: ET.Element) -> dict[str, str]:
    if root.tag.startswith("{"):
        return {"m": root.tag[1:].split("}", 1)[0]}
    return {"m": ""}


def _eval_xlsx(task: dict[str, Any], task_dir: Path, workspace: Path) -> tuple[bool, list[str]]:
    path = workspace / "submission" / task["evaluator"].get("output", "quarterly-sales.xlsx")
    details: list[str] = []
    if not path.exists():
        return False, [f"{path.name} missing"]
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            required = {"xl/workbook.xml", "xl/_rels/workbook.xml.rels"}
            if not required.issubset(names):
                return False, ["file is not a valid XLSX workbook"]
            workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
            ns = _ns(workbook_root)
            sheets = workbook_root.findall(".//m:sheets/m:sheet", ns)
            sheet_names = [item.attrib.get("name") for item in sheets]
            if sheet_names[:2] != ["Transactions", "Summary"]:
                return False, [f"expected sheets Transactions and Summary; got {sheet_names}"]
            relroot = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
            rel_ns = _ns(relroot)
            rels = {r.attrib["Id"]: r.attrib["Target"] for r in relroot.findall("m:Relationship", rel_ns)}
            sheet_paths = []
            for sheet in sheets[:2]:
                rel_id = next((v for k, v in sheet.attrib.items() if k.endswith("}id") or k == "id"), None)
                target = rels.get(rel_id, "")
                target = target.lstrip("/")
                if not target.startswith("xl/"):
                    target = "xl/" + target
                sheet_paths.append(target)
            shared = []
            if "xl/sharedStrings.xml" in names:
                root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                n = _ns(root)
                shared = ["".join(t.text or "" for t in item.findall(".//m:t", n)) for item in root.findall("m:si", n)]
            tables: list[dict[str, tuple[str, str, str]]] = []
            panes: list[bool] = []
            for sheet_path in sheet_paths:
                root = ET.fromstring(archive.read(sheet_path))
                n = _ns(root)
                cells: dict[str, tuple[str, str, str]] = {}
                for cell in root.findall(".//m:c", n):
                    ref = cell.attrib.get("r", "")
                    typ = cell.attrib.get("t", "")
                    formula = cell.find("m:f", n)
                    val = cell.find("m:v", n)
                    inline = cell.findall(".//m:is/m:t", n)
                    value = "".join(t.text or "" for t in inline) if inline else (val.text if val is not None and val.text else "")
                    if typ == "s" and value:
                        value = shared[int(value)]
                    cells[ref] = (value, formula.text if formula is not None and formula.text else "", cell.attrib.get("s", "0"))
                pane = root.find(".//m:pane", n)
                panes.append(pane is not None and pane.attrib.get("ySplit") == "1")
                tables.append(cells)
            # Source rows and report controls are specified in the task contract.
            expected = read_json(task_dir / task["evaluator"]["expected"])
            for sheet_index, cell_ref, wanted in expected["cells"]:
                cell = tables[sheet_index].get(cell_ref)
                if cell is None or cell[0] != str(wanted):
                    details.append(f"sheet {sheet_index + 1} cell {cell_ref}: expected {wanted!r}, got {cell[0] if cell else 'missing'!r}")
            for sheet_index, cell_ref, wanted_formula in expected.get("formulas", []):
                cell = tables[sheet_index].get(cell_ref)
                formula = (cell[1] if cell else "").replace("$", "").upper()
                if formula != wanted_formula.upper().lstrip("="):
                    details.append(f"sheet {sheet_index + 1} cell {cell_ref}: formula expected {wanted_formula!r}, got {formula!r}")
            if expected.get("require_frozen_header") and not panes[0]:
                details.append("Transactions header row is not frozen")
            return not details, details
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, ET.ParseError, IndexError) as exc:
        return False, [f"cannot read XLSX: {exc}"]


def _eval_png(task: dict[str, Any], submission: Path) -> tuple[bool, list[str]]:
    file = submission / task["evaluator"].get("output", "image.png")
    if not file.exists():
        return False, ["PNG output missing"]
    data = file.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return False, ["invalid PNG signature or IHDR"]
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    expected = task["evaluator"].get("dimensions", [256, 256])
    ok = [width, height] == expected
    return ok, [] if ok else [f"image dimensions {width}x{height}; expected {expected[0]}x{expected[1]}"]


def _eval_mp4(task: dict[str, Any], submission: Path) -> tuple[bool, list[str]]:
    file = submission / task["evaluator"].get("output", "video.mp4")
    if not file.exists():
        return False, ["MP4 output missing"]
    data = file.read_bytes()
    ok = len(data) >= 16 and data[4:8] == b"ftyp" and b"moov" in data and b"mdat" in data
    return ok, [] if ok else ["file does not contain the expected MP4 ftyp, moov, and mdat boxes"]


def _run_one(profile: dict[str, Any], task: dict[str, Any], task_dir: Path,
             repetition: int, rows: int, seed: int) -> dict[str, Any]:
    run_id = f"{profile['id']}__{task['id']}__{repetition}__{uuid.uuid4().hex[:8]}"
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    workspace = _prepare_workspace(task_dir, run_dir, task, rows, seed)
    prompt = _task_prompt(task, task_dir, workspace)
    task_hash = __import__("hashlib").sha256(prompt.encode("utf-8")).hexdigest()
    input_hash = _workspace_input_hash(workspace)
    start_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        process = _run_process(profile, prompt, workspace, run_dir, task["id"])
        if process["timed_out"]:
            evaluation = {"passed": False, "type": task["evaluator"]["type"], "details": ["agent exceeded timeout"]}
        elif process["exit_code"] != 0:
            evaluation = {"passed": False, "type": task["evaluator"]["type"],
                          "details": [f"agent process exited {process['exit_code']}"]}
        else:
            evaluation = evaluate(task, task_dir, workspace)
        result = {
            "run_id": run_id, "task_id": task["id"], "category": task.get("category"),
            "agent_id": profile["id"], "agent_label": profile.get("label", profile["id"]),
            "repetition": repetition, "started_at": start_iso,
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "benchmark_version": __version__, "prompt_sha256": task_hash,
            "input_sha256": input_hash,
            "seed": seed, "rows": rows if task["id"] == "data.clean-large-csv.v1" else None,
            "environment": {"python": sys.version.split()[0], "platform": sys.platform},
            "process": process, "evaluation": evaluation,
            "receipt_valid": process["agent_receipt"]["valid"],
            "passed": bool(evaluation["passed"] and process["agent_receipt"]["valid"]),
        }
        write_json(run_dir / "run.json", result)
        return result
    except Exception as exc:
        result = {"run_id": run_id, "task_id": task["id"], "agent_id": profile.get("id"),
                  "repetition": repetition, "passed": False, "error": f"{type(exc).__name__}: {exc}"}
        write_json(run_dir / "run.json", result)
        return result


def cmd_run(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    agents = {a.get("id"): a for a in load_agents() if not a.get("disabled", False)}
    if args.agent not in agents:
        raise BenchError(f"Unknown agent {args.agent!r}. Configured agents: {', '.join(sorted(agents)) or '(none)'}")
    profile = agents[args.agent]
    required = 1 if args.task else 0
    if bool(args.task) == bool(args.all) and not args.category:
        raise BenchError("Choose exactly one of --task TASK_ID, --category NAME, or --all")
    if args.task:
        selected = [args.task]
    elif args.category:
        selected = [task_id for task_id, (t, _) in tasks.items() if t.get("category") == args.category]
    else:
        selected = sorted(tasks)
    missing = [task_id for task_id in selected if task_id not in tasks]
    if missing:
        raise BenchError("Unknown task ID(s): " + ", ".join(missing))
    capabilities = set(profile.get("capabilities", []))
    output = []
    for task_id in selected:
        task, task_dir = tasks[task_id]
        needed = set(task.get("requires", []))
        if capabilities and not needed.issubset(capabilities):
            print(f"SKIP {task_id}: agent profile lacks {', '.join(sorted(needed - capabilities))}")
            continue
        for rep in range(1, args.repetitions + 1):
            print(f"RUN  {profile.get('label', profile['id'])} / {task_id} / {rep}/{args.repetitions}", flush=True)
            result = _run_one(profile, task, task_dir, rep, args.rows, args.seed)
            output.append(result)
            print(f"{'PASS' if result.get('passed') else 'FAIL'} {result['run_id']}" +
                  f" ({result.get('process', {}).get('wall_time_ms', '?')} ms)", flush=True)
    passed = sum(bool(x.get("passed")) for x in output)
    print(f"\nResult: {passed}/{len(output)} attempts passed; results in {RESULTS_DIR}")
    return 0 if output and passed == len(output) else 1


def cmd_prepare(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    if args.task not in tasks:
        raise BenchError(f"Unknown task ID {args.task!r}")
    task, task_dir = tasks[args.task]
    agent_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", args.agent.strip()).strip("-.") or "manual-agent"
    run_id = f"{agent_id}__{task['id']}__{args.repetition}__{uuid.uuid4().hex[:8]}"
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    workspace = _prepare_workspace(task_dir, run_dir, task, args.rows, args.seed)
    prompt = _task_prompt(task, task_dir, workspace)
    (run_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    (workspace / "prompt.md").write_text(prompt, encoding="utf-8")
    files = [p for p in workspace.rglob("*") if p.is_file()]
    input_hash = _workspace_input_hash(workspace)
    prompt_hash = __import__("hashlib").sha256(prompt.encode("utf-8")).hexdigest()
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_json(run_dir / "pending.json", {
        "run_id": run_id, "task_id": task["id"], "category": task.get("category"),
        "agent_id": agent_id, "agent_label": args.agent, "repetition": args.repetition,
        "started_at": started_at, "benchmark_version": __version__,
        "prompt_sha256": prompt_hash, "input_sha256": input_hash,
        "seed": args.seed, "rows": args.rows if task["id"] == "data.clean-large-csv.v1" else None,
        "environment": {"python": sys.version.split()[0], "platform": sys.platform},
    })
    package = run_dir / "task-package.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(workspace).as_posix())
    print(f"Prepared {task['id']} for {args.agent}")
    print(f"Upload/extract this package for the agent: {package}")
    print(f"Send the exact prompt in: {run_dir / 'prompt.md'}")
    print(f"After the run, put its requested files in: {workspace / 'submission'}")
    print(f"Run ID for evaluation: {run_id}")
    return 0


def cmd_evaluate_manual(args: argparse.Namespace) -> int:
    run_dir = RESULTS_DIR / args.run_id
    pending_path = run_dir / "pending.json"
    if not pending_path.is_file():
        raise BenchError(f"No prepared manual run found for {args.run_id!r}")
    pending = read_json(pending_path)
    tasks = load_tasks()
    task, task_dir = tasks[pending["task_id"]]
    workspace = run_dir / "workspace"
    evaluation = evaluate(task, task_dir, workspace)
    receipt = _read_agent_receipt(workspace / "submission" / RECEIPT_NAME, task["id"])
    usage = {
        "provider_cost": args.provider_cost, "currency": args.currency,
        "input_tokens": args.input_tokens, "output_tokens": args.output_tokens,
        "cached_input_tokens": None, "model_calls": None, "tool_calls": None,
        "provider_duration_ms": None,
        "source": args.usage_source if any(x is not None for x in (args.provider_cost, args.input_tokens, args.output_tokens)) else "unavailable",
    }
    process = {"command": ["manual"], "exit_code": 0, "timed_out": False,
               "wall_time_ms": args.wall_time_ms, "usage": usage, "agent_receipt": receipt}
    result = {**pending, "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "process": process, "evaluation": evaluation, "receipt_valid": receipt["valid"],
              "passed": bool(evaluation["passed"] and receipt["valid"])}
    write_json(run_dir / "run.json", result)
    pending_path.unlink()
    print(f"{'PASS' if result['passed'] else 'FAIL'} {args.run_id}: {evaluation['details'] or 'all checks passed'}")
    print(f"Saved result: {run_dir / 'run.json'}")
    return 0 if result["passed"] else 1


def cmd_agents(_: argparse.Namespace) -> int:
    for agent in load_agents():
        print(f"{agent.get('id')}\t{agent.get('label', '')}\t{agent.get('parser', 'none')}\t{agent.get('command')}")
    return 0


def cmd_report(_: argparse.Namespace) -> int:
    files = sorted(RESULTS_DIR.glob("*/run.json"))
    rows = [read_json(path) for path in files]
    report_dir = ROOT / "results"
    report_dir.mkdir(exist_ok=True)
    out_csv = report_dir / "leaderboard.csv"
    columns = ["agent_id", "agent_label", "category", "task_id", "attempts", "pass_rate",
               "mean_provider_cost", "p50_provider_cost", "provider_cost_iqr", "provider_cost_per_success",
               "provider_cost_currency", "provider_cost_source", "cost_cv_percent",
               "mean_agent_reported_cost", "agent_reported_currency", "agent_reported_cost_basis",
               "mean_wall_time_ms", "p50_wall_time_ms", "wall_time_iqr_ms",
               "mean_input_tokens", "mean_output_tokens", "valid_receipts"]
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault((row.get("agent_id", "?"), row.get("task_id", "?"), row.get("category", "?")), []).append(row)
    output_rows = []
    for (agent_id, task_id, category), group in sorted(groups.items()):
        cost_observations = [(r.get("process", {}).get("usage", {}).get("provider_cost"),
                              r.get("process", {}).get("usage", {}).get("currency"),
                              r.get("process", {}).get("usage", {}).get("source")) for r in group]
        cost_observations = [(float(c), cur, src) for c, cur, src in cost_observations
                             if isinstance(c, (int, float))]
        currencies = {cur for _, cur, _ in cost_observations}
        sources = sorted({str(src) for _, _, src in cost_observations if src})
        costs = [c for c, _, _ in cost_observations] if len(currencies) == 1 and None not in currencies else []
        currency = next(iter(currencies)) if len(currencies) == 1 and None not in currencies else None
        reported_costs = []
        for r in group:
            data = r.get("process", {}).get("agent_receipt", {}).get("data", {}).get("agent_reported", {})
            value = data.get("cost")
            if isinstance(value, (int, float)):
                reported_costs.append((float(value), data.get("cost_currency"), data.get("cost_basis")))
        reported_currencies = {cur for _, cur, _ in reported_costs}
        reported_bases = {basis for _, _, basis in reported_costs}
        times = [r.get("process", {}).get("wall_time_ms") for r in group]
        times = [float(t) for t in times if isinstance(t, (int, float))]
        def percentile(values: list[float], fraction: float) -> float | None:
            sorted_values = sorted(values)
            if not sorted_values:
                return None
            position = (len(sorted_values) - 1) * fraction
            lower = math.floor(position)
            upper = math.ceil(position)
            return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (position - lower)
        ins = [r.get("process", {}).get("usage", {}).get("input_tokens") for r in group]
        ins = [float(n) for n in ins if isinstance(n, (int, float))]
        outs = [r.get("process", {}).get("usage", {}).get("output_tokens") for r in group]
        outs = [float(n) for n in outs if isinstance(n, (int, float))]
        mean_cost = statistics.mean(costs) if costs else None
        successful = sum(bool(r.get("passed")) for r in group)
        cv = None
        if len(costs) > 1 and mean_cost:
            cv = statistics.stdev(costs) / mean_cost * 100
        output_rows.append({
            "agent_id": agent_id, "agent_label": group[0].get("agent_label", agent_id),
            "category": category, "task_id": task_id, "attempts": len(group),
            "pass_rate": round(sum(bool(r.get("passed")) for r in group) / len(group), 4),
            "mean_provider_cost": round(mean_cost, 6) if mean_cost is not None else None,
            "p50_provider_cost": round(percentile(costs, 0.5), 6) if costs else None,
            "provider_cost_iqr": round((percentile(costs, 0.75) or 0) - (percentile(costs, 0.25) or 0), 6) if costs else None,
            "provider_cost_per_success": round(sum(costs) / successful, 6) if costs and len(costs) == len(group) and successful else None,
            "provider_cost_currency": currency,
            "provider_cost_source": ";".join(sources) if sources else None,
            "cost_cv_percent": round(cv, 3) if cv is not None else None,
            "mean_agent_reported_cost": round(statistics.mean([c for c, _, _ in reported_costs]), 6) if reported_costs and len(reported_currencies) <= 1 else None,
            "agent_reported_currency": next(iter(reported_currencies)) if len(reported_currencies) == 1 else None,
            "agent_reported_cost_basis": next(iter(reported_bases)) if len(reported_bases) == 1 else None,
            "mean_wall_time_ms": round(statistics.mean(times), 1) if times else None,
            "p50_wall_time_ms": round(percentile(times, 0.5), 1) if times else None,
            "wall_time_iqr_ms": round((percentile(times, 0.75) or 0) - (percentile(times, 0.25) or 0), 1) if times else None,
            "mean_input_tokens": statistics.mean(ins) if ins else None,
            "mean_output_tokens": statistics.mean(outs) if outs else None,
            "valid_receipts": sum(bool(r.get("receipt_valid")) for r in group),
        })
    with out_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {out_csv}")
    for row in output_rows:
        cost = "n/a" if row["mean_provider_cost"] is None else f"{row['mean_provider_cost']} {row['provider_cost_currency']}"
        print(f"{row['agent_id']:18} {row['task_id']:36} pass={row['pass_rate']:.0%} cost={cost} p50={row['p50_wall_time_ms'] or 'n/a'}ms")
    if not output_rows:
        print("No completed runs yet.")
    return 0


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentbench", description="Run reproducible tasks against different AI agent tools.")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("init", help="create local agent profile configuration")
    sub.add_parser("list", help="list runnable benchmark tasks")
    sub.add_parser("agents", help="show configured agent profiles")
    run = sub.add_parser("run", help="run one task, one category, or the complete battery")
    run.add_argument("--agent", required=True, help="profile ID in .agentbench/agents.json")
    choose = run.add_mutually_exclusive_group(required=True)
    choose.add_argument("--task", help="task ID")
    choose.add_argument("--category", help="run all tasks in a category")
    choose.add_argument("--all", action="store_true", help="run every task the agent profile supports")
    run.add_argument("--repetitions", type=int, default=1)
    run.add_argument("--rows", type=int, default=1_000_000, help="data task input size (default: 1 million)")
    run.add_argument("--seed", type=int, default=20260929)
    prepare = sub.add_parser("prepare", help="export the identical task package for a web/desktop AI tool")
    prepare.add_argument("--task", required=True, help="task ID")
    prepare.add_argument("--agent", required=True, help="label for the AI tool/model")
    prepare.add_argument("--repetition", type=int, default=1)
    prepare.add_argument("--rows", type=int, default=1_000_000)
    prepare.add_argument("--seed", type=int, default=20260929)
    finish = sub.add_parser("evaluate", help="score a prepared manual run and save provider metrics")
    finish.add_argument("--run-id", required=True, help="ID printed by prepare")
    finish.add_argument("--provider-cost", type=float)
    finish.add_argument("--currency", default="USD")
    finish.add_argument("--input-tokens", type=int)
    finish.add_argument("--output-tokens", type=int)
    finish.add_argument("--wall-time-ms", type=int)
    finish.add_argument("--usage-source", default="provider-dashboard")
    sub.add_parser("report", help="aggregate all saved runs into a CSV scorecard")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    actions = {"init": cmd_init, "list": cmd_list, "agents": cmd_agents, "run": cmd_run,
               "prepare": cmd_prepare, "evaluate": cmd_evaluate_manual, "report": cmd_report}
    try:
        if getattr(args, "repetitions", 1) < 1:
            raise BenchError("--repetitions must be at least 1")
        if getattr(args, "repetition", 1) < 1:
            raise BenchError("--repetition must be at least 1")
        if getattr(args, "rows", 1) < 1:
            raise BenchError("--rows must be at least 1")
        if getattr(args, "provider_cost", None) is not None and args.provider_cost < 0:
            raise BenchError("--provider-cost cannot be negative")
        for field in ("input_tokens", "output_tokens", "wall_time_ms"):
            value = getattr(args, field, None)
            if value is not None and value < 0:
                raise BenchError(f"--{field.replace('_', '-')} cannot be negative")
        return actions[args.action](args)
    except BenchError as exc:
        print(f"agentbench: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
