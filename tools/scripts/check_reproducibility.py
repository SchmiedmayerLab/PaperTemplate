#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

"""Validate and execute the repository's declared data-to-artifact pipeline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from check_submodules import manifest_rows as submodule_manifest_rows
from check_submodules import status_records as submodule_status_records
from check_submodules import validate_project as validate_submodules


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_PATH = Path("research/reproducibility/pipeline.json")
DATA_MANIFEST_PATH = Path("research/data/manifest.tsv")
RUN_RECORD_PATH = Path("build/reproducibility-run.json")
GENERATED_ROOTS = (Path("paper/figures/generated"), Path("paper/tables/generated"))
UNTRACKED_DERIVED_ROOTS = (
    Path("research/data/interim"),
    Path("research/data/derived"),
    Path("paper/figures/generated"),
    Path("paper/tables/generated"),
    Path("build"),
    Path("output"),
    Path("tmp"),
)
ALLOWED_OUTPUT_ROOTS = (
    Path("research/data/interim"),
    Path("research/data/derived"),
    Path("paper/figures/generated"),
    Path("paper/tables/generated"),
    Path("build"),
    Path("output"),
)
DATA_ROOTS = (Path("research/data/source"), Path("research/data/external"), Path("research/data/restricted"))
DATA_FIELDS = (
    "path",
    "category",
    "origin",
    "version_or_date",
    "license_or_access",
    "sensitivity",
    "checksum",
    "description",
)
STEP_FIELDS = (
    "id",
    "description",
    "inputs",
    "command",
    "outputs",
    "manuscript_locations",
    "requires_restricted_data",
)
GRAPHICS_PATTERN = re.compile(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}")
GENERATED_TABLE_PATTERN = re.compile(r"\\(?:input|include)\{(paper/tables/generated/[^}]+)\}")
ABSOLUTE_COMMAND_PATH_PATTERN = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="Execute valid pipeline steps in order.")
    parser.add_argument(
        "--submission",
        action="store_true",
        help="Require restricted inputs and every declared output.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_path(value: str, label: str, errors: list[str]) -> Path | None:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        errors.append(f"{label}: path must be a nonempty repository-relative path: {value!r}")
        return None
    return path


def under(path: Path, roots: tuple[Path, ...]) -> bool:
    return any(path == root or root in path.parents for root in roots)


def template_support_file(path: Path) -> bool:
    return path.name == "README.md" or path.name.endswith(".license") or path.name == ".gitkeep"


def read_data_manifest(
    root: Path,
    errors: list[str],
    warnings: list[str],
    submodules: dict[Path, dict[str, str]],
) -> dict[Path, dict[str, str]]:
    manifest_path = root / DATA_MANIFEST_PATH
    if not manifest_path.exists():
        errors.append(f"missing {DATA_MANIFEST_PATH}")
        return {}
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != DATA_FIELDS:
            errors.append(
                f"{DATA_MANIFEST_PATH}: expected columns {', '.join(DATA_FIELDS)}"
            )
            return {}
        rows: dict[Path, dict[str, str]] = {}
        for line_number, row in enumerate(reader, start=2):
            label = f"{DATA_MANIFEST_PATH}:{line_number}"
            path = repository_path(row["path"].strip(), label, errors)
            if path is None:
                continue
            if path in rows:
                errors.append(f"{label}: duplicate data path {path}")
                continue
            if not under(path, DATA_ROOTS):
                errors.append(f"{label}: data path must be under research/data/source, research/data/external, or research/data/restricted")
            for field in DATA_FIELDS:
                if not row[field].strip():
                    errors.append(f"{label}: missing {field}")
            expected_category = path.parts[2] if len(path.parts) > 2 else ""
            if row["category"].strip() != expected_category:
                errors.append(f"{label}: category must match path directory {expected_category!r}")
            absolute = root / path
            recorded_checksum = row["checksum"].strip().lower()
            if absolute.exists() and absolute.is_file():
                if not re.fullmatch(r"sha256:[0-9a-f]{64}", recorded_checksum):
                    errors.append(f"{label}: stored files require checksum sha256:<64-character digest>")
                elif sha256(absolute) != recorded_checksum.removeprefix("sha256:"):
                    errors.append(f"{label}: SHA-256 checksum does not match {path}")
            elif path in submodules:
                expected = f"git:{submodules[path]['pinned_commit'].strip().lower()}"
                if recorded_checksum != expected:
                    errors.append(f"{label}: data submodule checksum must match {expected}")
            elif absolute.exists():
                errors.append(f"{label}: directory paths are allowed only for registered data submodules")
            elif expected_category != "restricted":
                errors.append(f"{label}: declared data file does not exist: {path}")
            elif recorded_checksum in {"unknown", "todo", "n/a", "na", "unavailable"}:
                warnings.append(f"{label}: restricted input has no immutable checksum")
            rows[path] = row

    for data_root in DATA_ROOTS[:2]:
        absolute_root = root / data_root
        if not absolute_root.exists():
            errors.append(f"missing required directory {data_root}")
            continue
        for path in absolute_root.rglob("*"):
            if path.is_file() and not template_support_file(path):
                relative = path.relative_to(root)
                if any(relative == module or module in relative.parents for module in submodules):
                    continue
                if relative not in rows:
                    errors.append(f"{relative}: foundational or external data file is absent from {DATA_MANIFEST_PATH}")
    return rows


def read_pipeline(root: Path, errors: list[str]) -> dict[str, Any]:
    path = root / PIPELINE_PATH
    if not path.exists():
        errors.append(f"missing {PIPELINE_PATH}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{PIPELINE_PATH}: {error}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"{PIPELINE_PATH}: top-level value must be an object")
        return {}
    if payload.get("schema_version") != 1:
        errors.append(f"{PIPELINE_PATH}: schema_version must be 1")
    environment = payload.get("environment")
    if not isinstance(environment, str):
        errors.append(f"{PIPELINE_PATH}: environment must be a repository-relative path")
    else:
        environment_path = repository_path(environment, f"{PIPELINE_PATH}:environment", errors)
        if environment_path is not None and not (root / environment_path).exists():
            errors.append(f"{PIPELINE_PATH}: environment file does not exist: {environment_path}")
    if not isinstance(payload.get("steps"), list):
        errors.append(f"{PIPELINE_PATH}: steps must be an array")
    return payload


def validate_steps(
    root: Path,
    payload: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    submission: bool,
) -> tuple[list[dict[str, Any]], set[Path]]:
    valid_steps: list[dict[str, Any]] = []
    declared_outputs: set[Path] = set()
    step_ids: set[str] = set()
    steps = payload.get("steps", [])
    if not isinstance(steps, list):
        return valid_steps, declared_outputs

    for index, step in enumerate(steps):
        label = f"{PIPELINE_PATH}:steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{label}: step must be an object")
            continue
        missing = [field for field in STEP_FIELDS if field not in step]
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(missing)}")
            continue
        identifier = step["id"]
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", identifier):
            errors.append(f"{label}: id must use lowercase letters, digits, and hyphens")
        elif identifier in step_ids:
            errors.append(f"{label}: duplicate id {identifier!r}")
        else:
            step_ids.add(identifier)
        if not isinstance(step["description"], str) or not step["description"].strip():
            errors.append(f"{label}: description must be nonempty")
        if not isinstance(step["requires_restricted_data"], bool):
            errors.append(f"{label}: requires_restricted_data must be true or false")

        command = step["command"]
        if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
            errors.append(f"{label}: command must be a nonempty array of strings")
        elif any(ABSOLUTE_COMMAND_PATH_PATTERN.search(item) for item in command):
            errors.append(f"{label}: command contains an absolute machine-specific path")

        parsed_inputs: list[Path] = []
        parsed_outputs: list[Path] = []
        for field, target in (("inputs", parsed_inputs), ("outputs", parsed_outputs), ("manuscript_locations", [])):
            values = step[field]
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                errors.append(f"{label}: {field} must be an array of repository-relative paths")
                continue
            if field in {"inputs", "outputs"} and not values:
                errors.append(f"{label}: {field} must not be empty")
            for value in values:
                parsed = repository_path(value, f"{label}:{field}", errors)
                if parsed is not None and field != "manuscript_locations":
                    target.append(parsed)
                if parsed is not None and field == "manuscript_locations" and not (root / parsed).exists():
                    errors.append(f"{label}: manuscript location does not exist: {parsed}")

        requires_restricted = step.get("requires_restricted_data") is True
        for input_path in parsed_inputs:
            if not (root / input_path).exists():
                message = f"{label}: input does not exist: {input_path}"
                if requires_restricted and not submission:
                    warnings.append(message)
                else:
                    errors.append(message)
        for output_path in parsed_outputs:
            if not under(output_path, ALLOWED_OUTPUT_ROOTS):
                errors.append(f"{label}: output is outside an allowed generated directory: {output_path}")
            if output_path in declared_outputs:
                errors.append(f"{label}: output is declared by more than one step: {output_path}")
            declared_outputs.add(output_path)
            if submission and not (root / output_path).exists():
                warnings.append(f"{label}: output will be generated during this check: {output_path}")
        valid_steps.append(step)

    for generated_root in GENERATED_ROOTS:
        absolute_root = root / generated_root
        if not absolute_root.exists():
            errors.append(f"missing required directory {generated_root}")
            continue
        for path in absolute_root.rglob("*"):
            if path.is_file() and not template_support_file(path):
                relative = path.relative_to(root)
                if relative not in declared_outputs:
                    errors.append(f"{relative}: generated artifact is not declared in {PIPELINE_PATH}")
    return valid_steps, declared_outputs


def manuscript_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory in (root / "paper" / "sections", root / "paper" / "supplement"):
        if directory.exists():
            files.extend(directory.rglob("*.tex"))
    if (root / "main.tex").exists():
        files.append(root / "main.tex")
    return sorted(set(files))


def resolve_graphic(root: Path, value: str) -> Path | None:
    source = Path(value)
    candidates: list[Path] = []
    prefixes = (Path(), Path("paper/figures/generated"))
    suffixes = ("", ".pdf", ".png", ".jpg", ".jpeg", ".eps") if not source.suffix else ("",)
    for prefix in prefixes:
        for suffix in suffixes:
            candidates.append(prefix / f"{source}{suffix}")
    return next((candidate for candidate in candidates if (root / candidate).exists()), None)


def validate_manuscript_artifacts(
    root: Path,
    declared_outputs: set[Path],
    errors: list[str],
) -> None:
    for path in manuscript_files(root):
        text = path.read_text(encoding="utf-8")
        for value in GRAPHICS_PATTERN.findall(text):
            resolved = resolve_graphic(root, value)
            location = path.relative_to(root)
            if resolved is None:
                errors.append(f"{location}: included graphic does not exist: {value}")
            elif under(resolved, GENERATED_ROOTS) and resolved not in declared_outputs:
                errors.append(f"{location}: included generated graphic is undeclared: {resolved}")
        for value in GENERATED_TABLE_PATTERN.findall(text):
            table = Path(value)
            if not table.suffix:
                table = table.with_suffix(".tex")
            location = path.relative_to(root)
            if not (root / table).exists():
                errors.append(f"{location}: included generated table does not exist: {table}")
            elif table not in declared_outputs:
                errors.append(f"{location}: included generated table is undeclared: {table}")


def validate_tracked_outputs(root: Path, errors: list[str]) -> None:
    completed = subprocess.run(
        ["git", "ls-files", "--cached"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return
    for value in completed.stdout.splitlines():
        path = Path(value)
        if under(path, UNTRACKED_DERIVED_ROOTS) and not template_support_file(path):
            errors.append(f"{path}: derived, generated, build, or temporary output must not be tracked")


def validate_project(root: Path, submission: bool = False) -> tuple[list[str], list[str], list[dict[str, Any]], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    submodule_errors, submodule_warnings, _ = validate_submodules(root)
    errors.extend(submodule_errors)
    warnings.extend(submodule_warnings)
    submodules = submodule_manifest_rows(root)
    read_data_manifest(root, errors, warnings, submodules)
    payload = read_pipeline(root, errors)
    steps, outputs = validate_steps(root, payload, errors, warnings, submission)
    validate_manuscript_artifacts(root, outputs, errors)
    validate_tracked_outputs(root, errors)
    return errors, warnings, steps, payload


def file_record(root: Path, path: Path) -> dict[str, str]:
    absolute = root / path
    return {"path": str(path), "sha256": sha256(absolute)}


def execute(root: Path, steps: list[dict[str, Any]], payload: dict[str, Any], submission: bool) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    record: dict[str, Any] = {
        "schema_version": 1,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "environment": payload.get("environment"),
        "scope": "declared_steps" if steps else "no_steps_declared",
        "submodules": submodule_status_records(root),
        "steps": [],
    }
    for step in steps:
        inputs = [Path(value) for value in step["inputs"]]
        missing_inputs = [path for path in inputs if not (root / path).exists()]
        if missing_inputs and step["requires_restricted_data"] and not submission:
            record["steps"].append(
                {
                    "id": step["id"],
                    "status": "skipped_missing_restricted_data",
                    "missing_inputs": [str(path) for path in missing_inputs],
                }
            )
            continue
        if missing_inputs:
            errors.append(f"{step['id']}: cannot run with missing inputs: {', '.join(map(str, missing_inputs))}")
            break
        completed = subprocess.run(step["command"], cwd=root, check=False)
        if completed.returncode != 0:
            errors.append(f"{step['id']}: command failed with exit code {completed.returncode}")
            break
        outputs = [Path(value) for value in step["outputs"]]
        missing_outputs = [path for path in outputs if not (root / path).is_file()]
        if missing_outputs:
            errors.append(f"{step['id']}: command did not create outputs: {', '.join(map(str, missing_outputs))}")
            break
        record["steps"].append(
            {
                "id": step["id"],
                "status": "completed",
                "command": step["command"],
                "inputs": [file_record(root, path) for path in inputs if (root / path).is_file()],
                "outputs": [file_record(root, path) for path in outputs],
            }
        )
    record["completed_at"] = datetime.now(timezone.utc).isoformat()
    record["status"] = "failed" if errors else "completed"
    destination = root / RUN_RECORD_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return errors, record


def main() -> int:
    args = parse_args()
    root = args.project_root.resolve()
    errors, warnings, steps, payload = validate_project(root, submission=args.submission)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"Reproducibility check: {len(errors)} errors, {len(warnings)} warnings")
        return 1
    if args.run:
        execution_errors, _ = execute(root, steps, payload, submission=args.submission)
        for error in execution_errors:
            print(f"ERROR: {error}")
        if execution_errors:
            print(f"Reproduction failed: {len(execution_errors)} errors")
            return 1
        print(f"Executed {len(steps)} declared pipeline steps")
        if not steps:
            print("No pipeline steps declared; no scientific artifacts were regenerated.")
    print(f"Reproducibility check: 0 errors, {len(warnings)} warnings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
