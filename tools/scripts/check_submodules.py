#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

"""Validate pinned Git submodules and their human-readable manifest."""

from __future__ import annotations

import configparser
import csv
import re
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path("research/reproducibility/submodules.tsv")
FIELDS = (
    "path",
    "repository",
    "role",
    "version_label",
    "pinned_commit",
    "license",
    "manuscript_use",
)


def repository_path(value: str, label: str, errors: list[str]) -> Path | None:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        errors.append(f"{label}: path must be a nonempty repository-relative path: {value!r}")
        return None
    return path


def read_manifest(root: Path, errors: list[str]) -> dict[Path, dict[str, str]]:
    path = root / MANIFEST_PATH
    if not path.exists():
        errors.append(f"missing {MANIFEST_PATH}")
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != FIELDS:
            errors.append(f"{MANIFEST_PATH}: expected columns {', '.join(FIELDS)}")
            return {}
        rows: dict[Path, dict[str, str]] = {}
        for line_number, row in enumerate(reader, start=2):
            label = f"{MANIFEST_PATH}:{line_number}"
            submodule_path = repository_path(row["path"].strip(), label, errors)
            if submodule_path is None:
                continue
            if submodule_path in rows:
                errors.append(f"{label}: duplicate submodule path {submodule_path}")
                continue
            for field in FIELDS:
                if not row[field].strip():
                    errors.append(f"{label}: missing {field}")
            commit = row["pinned_commit"].strip().lower()
            if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
                errors.append(f"{label}: pinned_commit must be a complete 40- or 64-character Git object ID")
            rows[submodule_path] = row
    return rows


def manifest_rows(root: Path) -> dict[Path, dict[str, str]]:
    errors: list[str] = []
    return read_manifest(root, errors)


def read_gitmodules(root: Path, errors: list[str]) -> dict[Path, str]:
    path = root / ".gitmodules"
    if not path.exists():
        return {}
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(path, encoding="utf-8")
    except configparser.Error as error:
        errors.append(f".gitmodules: {error}")
        return {}
    modules: dict[Path, str] = {}
    for section in parser.sections():
        if not section.startswith("submodule "):
            continue
        if not parser.has_option(section, "path") or not parser.has_option(section, "url"):
            errors.append(f".gitmodules:{section}: both path and url are required")
            continue
        module_path = repository_path(parser.get(section, "path").strip(), f".gitmodules:{section}", errors)
        if module_path is not None:
            modules[module_path] = parser.get(section, "url").strip()
    return modules


def index_commit(root: Path, path: Path) -> str | None:
    completed = subprocess.run(
        ["git", "ls-files", "--stage", "--", str(path)],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        return None
    mode, commit, _ = completed.stdout.split(maxsplit=2)
    return commit.lower() if mode == "160000" else None


def status_records(root: Path) -> list[dict[str, str]]:
    completed = subprocess.run(
        ["git", "submodule", "status", "--recursive"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return []
    records: list[dict[str, str]] = []
    for line in completed.stdout.splitlines():
        if not line:
            continue
        prefix = line[0]
        parts = line[1:].strip().split(maxsplit=2)
        if len(parts) < 2:
            continue
        records.append(
            {
                "path": parts[1],
                "commit": parts[0],
                "state": {" ": "pinned", "-": "uninitialized", "+": "mismatch", "U": "conflict"}.get(prefix, "unknown"),
                "description": parts[2] if len(parts) > 2 else "",
            }
        )
    return records


def validate_project(root: Path) -> tuple[list[str], list[str], list[dict[str, str]]]:
    errors: list[str] = []
    warnings: list[str] = []
    rows = read_manifest(root, errors)
    modules = read_gitmodules(root, errors)

    for path, url in modules.items():
        if path not in rows:
            errors.append(f"{path}: submodule is absent from {MANIFEST_PATH}")
            continue
        row = rows[path]
        if row["repository"].strip() != url:
            errors.append(f"{path}: manifest repository does not match .gitmodules URL")
        pinned = index_commit(root, path)
        if pinned is None:
            errors.append(f"{path}: Git index does not contain a submodule pointer")
        elif row["pinned_commit"].strip().lower() != pinned:
            errors.append(f"{path}: manifest pinned_commit does not match the superproject pointer {pinned}")

    for path in rows.keys() - modules.keys():
        errors.append(f"{path}: manifest entry has no matching .gitmodules section")

    records = status_records(root) if modules else []
    top_level_status = {Path(record["path"]): record for record in records}
    for path in modules:
        record = top_level_status.get(path)
        if record is None:
            errors.append(f"{path}: submodule status is unavailable")
        elif record["state"] == "uninitialized":
            errors.append(f"{path}: submodule is not initialized; run git submodule update --init --recursive")
        elif record["state"] in {"mismatch", "conflict", "unknown"}:
            errors.append(f"{path}: checked-out submodule state is {record['state']}")
        elif "dirty" in record["description"].lower():
            warnings.append(f"{path}: submodule working tree is dirty")
    for record in records:
        if record["state"] in {"uninitialized", "mismatch", "conflict", "unknown"}:
            path = Path(record["path"])
            if path not in modules:
                errors.append(f"{path}: nested submodule state is {record['state']}")
    return errors, warnings, records


def main() -> int:
    errors, warnings, records = validate_project(PROJECT_ROOT)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Checked {len(records)} submodule revisions: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
