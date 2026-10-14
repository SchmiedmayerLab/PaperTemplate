#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

"""Build, sanitize, package, and validate an arXiv LaTeX source archive.

The LaTeX recorder file is the source of truth for manuscript dependencies.
Only project-local files used by the build and explicitly mapped generated files
enter the archive.  This avoids both broad source-tree uploads and fragile
hand-maintained exclusion lists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = Path("project/submission/arxiv.json")
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
SAFE_ARCHIVE_PATH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
FORBIDDEN_EXTENSIONS = {
    ".aux",
    ".bcf",
    ".bib",
    ".blg",
    ".fdb_latexmk",
    ".fls",
    ".glg",
    ".glo",
    ".ist",
    ".lof",
    ".log",
    ".lot",
    ".out",
    ".run.xml",
    ".synctex",
    ".synctex.gz",
    ".toc",
    ".xdv",
    ".zip",
}
FORBIDDEN_NAMES = {
    ".DS_Store",
    "AGENTS.md",
    "Makefile",
    "Thumbs.db",
    "latexmkrc",
    "references.bib",
}
LITERAL_ENVIRONMENTS = {
    "Verbatim",
    "Verbatim*",
    "lstlisting",
    "minted",
    "verbatim",
    "verbatim*",
}
URL_ARGUMENT_COMMANDS = {"nolinkurl", "path", "url"}
TEX_LANGUAGE_EXTENSIONS = {
    ".bbl",
    ".bbx",
    ".bst",
    ".cbx",
    ".cfg",
    ".clo",
    ".cls",
    ".def",
    ".fd",
    ".gls",
    ".ind",
    ".ldf",
    ".lbx",
    ".ltx",
    ".nls",
    ".pgf",
    ".sty",
    ".tex",
    ".tikz",
}
UNSAFE_COMPILER_OPTIONS = {
    "--enable-write18",
    "--shell-escape",
    "-enable-write18",
    "-shell-escape",
}
LOG_FAILURE_PATTERNS = (
    re.compile(r"LaTeX Warning: Citation .+ undefined", re.IGNORECASE),
    re.compile(r"LaTeX Warning: Reference .+ undefined", re.IGNORECASE),
    re.compile(r"There were undefined (?:citations|references)", re.IGNORECASE),
    re.compile(r"No file .+\.bbl", re.IGNORECASE),
    re.compile(r"I couldn't open database file", re.IGNORECASE),
    re.compile(r"Emergency stop", re.IGNORECASE),
    re.compile(r"Fatal error occurred", re.IGNORECASE),
)
INTERNAL_SOURCE_PATTERNS = (
    (re.compile(r"\\begin\s*\{comment\}"), r"\begin{comment}"),
    (re.compile(r"\\iffalse\b"), r"\iffalse"),
    (re.compile(r"\\excludecomment\b"), r"\excludecomment"),
    (re.compile(r"\\catcode\b"), r"\catcode"),
)


class ArxivPackageError(RuntimeError):
    """Raised when a source archive cannot be proven safe and complete."""


@dataclass(frozen=True)
class GeneratedFile:
    source: Path
    destination: Path


@dataclass(frozen=True)
class ExtraFile:
    source: Path
    destination: Path
    purpose: str


@dataclass(frozen=True)
class ArxivConfig:
    project_root: Path
    config_path: Path
    entrypoint: Path
    compiler: tuple[str, ...]
    texlive_version: str
    recorder: Path
    allowed_roots: tuple[Path, ...]
    generated_files: tuple[GeneratedFile, ...]
    extra_files: tuple[ExtraFile, ...]
    strip_comment_extensions: frozenset[str]
    copy_extensions: frozenset[str]
    archive: Path
    max_archive_bytes: int
    max_uncompressed_bytes: int
    compile_timeout_seconds: int


@dataclass(frozen=True)
class RecorderData:
    inputs: frozenset[Path]
    outputs: frozenset[Path]


@dataclass(frozen=True)
class PackageResult:
    archive: Path
    contents_report: Path
    checksum_report: Path
    members: tuple[str, ...]
    sha256: str


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create and locally validate a minimal arXiv source ZIP."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Configuration path relative to the project root (default: {DEFAULT_CONFIG_PATH}).",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--submission-date",
        type=date.fromisoformat,
        metavar="YYYY-MM-DD",
        help="Freeze the template date in staged source (default: today's local date).",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        type=Path,
        metavar="ZIP",
        help="Validate an existing trusted source ZIP instead of building a new archive.",
    )
    mode.add_argument(
        "--clear-output",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    mode.add_argument(
        "--smoke-test",
        action="store_true",
        help="Validate packaging in temporary storage without publishing a source ZIP.",
    )
    return parser.parse_args(argv)


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ArxivPackageError(f"missing arXiv configuration: {path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise ArxivPackageError(f"cannot read arXiv configuration {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ArxivPackageError(f"{path}: top-level JSON value must be an object")
    return payload


def _relative_path(value: object, label: str, *, allow_dot: bool = False) -> Path:
    if not isinstance(value, str) or not value:
        raise ArxivPackageError(f"{label} must be a nonempty repository-relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or (not allow_dot and path == Path(".")):
        raise ArxivPackageError(f"{label} must be a repository-relative path without '..': {value!r}")
    if any(part.startswith(".") for part in path.parts):
        raise ArxivPackageError(f"{label} contains a hidden path component: {value!r}")
    if not SAFE_ARCHIVE_PATH.fullmatch(path.as_posix()):
        raise ArxivPackageError(
            f"{label} must use portable ASCII letters, digits, '.', '_', '-', and '/': {value!r}"
        )
    return path


def _compiler(value: object, label: str) -> tuple[str, ...]:
    if isinstance(value, str):
        command = tuple(shlex.split(value))
    elif isinstance(value, list) and all(isinstance(item, str) and item for item in value):
        command = tuple(value)
    else:
        raise ArxivPackageError(f"{label} must be a command string or an array of strings")
    if not command:
        raise ArxivPackageError(f"{label} must not be empty")
    if any(item in UNSAFE_COMPILER_OPTIONS for item in command):
        raise ArxivPackageError(f"{label} must not enable shell escape")
    if command[0] in {"latex", "lualatex", "pdflatex", "xelatex"}:
        if len(command) != 1:
            raise ArxivPackageError(
                f"{label}: configure engine {command[0]!r} without arguments, or provide a latexmk command"
            )
        latexmk_mode = {
            "latex": "-pdf",
            "lualatex": "-lualatex",
            "pdflatex": "-pdf",
            "xelatex": "-xelatex",
        }[command[0]]
        command = (
            "latexmk",
            latexmk_mode,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
        )
    return command


def load_config(
    project_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> ArxivConfig:
    """Load and strictly validate repository-local arXiv configuration."""

    root = project_root.resolve()
    config_absolute = config_path if config_path.is_absolute() else root / config_path
    payload = _load_json_object(config_absolute)
    allowed_keys = {
        "schema_version",
        "entrypoint",
        "compiler",
        "texlive_version",
        "recorder",
        "allowed_roots",
        "generated_files",
        "extra_files",
        "strip_comment_extensions",
        "copy_extensions",
        "archive",
        "max_archive_bytes",
        "max_uncompressed_bytes",
        "compile_timeout_seconds",
    }
    unknown = sorted(set(payload) - allowed_keys)
    if unknown:
        raise ArxivPackageError(f"{config_absolute}: unknown fields: {', '.join(unknown)}")
    if payload.get("schema_version") != 1:
        raise ArxivPackageError(f"{config_absolute}: schema_version must be 1")

    entrypoint = _relative_path(payload.get("entrypoint"), "entrypoint")
    recorder = _relative_path(payload.get("recorder"), "recorder")
    archive = _relative_path(payload.get("archive"), "archive")
    if archive.suffix.lower() != ".zip" or archive.parts[:2] != ("output", "arxiv"):
        raise ArxivPackageError("archive must be a .zip file below output/arxiv/")
    compiler = _compiler(payload.get("compiler"), "compiler")
    if recorder.name != entrypoint.with_suffix(".fls").name:
        raise ArxivPackageError(
            "recorder must use the entrypoint stem and .fls extension "
            f"({entrypoint.with_suffix('.fls').name})"
        )

    texlive_version = payload.get("texlive_version", "")
    if not isinstance(texlive_version, str):
        raise ArxivPackageError("texlive_version must be a string")

    roots_payload = payload.get("allowed_roots")
    if not isinstance(roots_payload, list) or not roots_payload:
        raise ArxivPackageError("allowed_roots must be a nonempty array")
    allowed_roots = tuple(
        _relative_path(value, f"allowed_roots[{index}]")
        for index, value in enumerate(roots_payload)
    )

    generated_payload = payload.get("generated_files", [])
    if not isinstance(generated_payload, list):
        raise ArxivPackageError("generated_files must be an array")
    generated: list[GeneratedFile] = []
    for index, item in enumerate(generated_payload):
        if not isinstance(item, dict) or set(item) != {"source", "destination"}:
            raise ArxivPackageError(
                f"generated_files[{index}] must contain only source and destination"
            )
        generated.append(
            GeneratedFile(
                source=_relative_path(item["source"], f"generated_files[{index}].source"),
                destination=_relative_path(
                    item["destination"], f"generated_files[{index}].destination"
                ),
            )
        )

    extra_payload = payload.get("extra_files", [])
    if not isinstance(extra_payload, list):
        raise ArxivPackageError("extra_files must be an array")
    extra_files: list[ExtraFile] = []
    for index, item in enumerate(extra_payload):
        if not isinstance(item, dict) or set(item) != {"source", "destination", "purpose"}:
            raise ArxivPackageError(
                f"extra_files[{index}] must contain only source, destination, and purpose"
            )
        purpose = item["purpose"]
        if not isinstance(purpose, str) or not purpose.strip():
            raise ArxivPackageError(f"extra_files[{index}].purpose must be a nonempty string")
        extra_files.append(
            ExtraFile(
                source=_relative_path(item["source"], f"extra_files[{index}].source"),
                destination=_relative_path(
                    item["destination"], f"extra_files[{index}].destination"
                ),
                purpose=purpose.strip(),
            )
        )

    extensions_payload = payload.get("strip_comment_extensions", [".tex", ".bbl"])
    if not isinstance(extensions_payload, list) or not all(
        isinstance(value, str) and re.fullmatch(r"\.[A-Za-z0-9]+", value)
        for value in extensions_payload
    ):
        raise ArxivPackageError(
            "strip_comment_extensions must be an array of extensions such as '.tex'"
        )
    strip_extensions = frozenset(value.lower() for value in extensions_payload)
    unsafe_strip_extensions = strip_extensions - TEX_LANGUAGE_EXTENSIONS
    if unsafe_strip_extensions:
        raise ArxivPackageError(
            "comment stripping is supported only for explicitly configured TeX-language files; "
            f"refusing: {', '.join(sorted(unsafe_strip_extensions))}"
        )

    copy_payload = payload.get("copy_extensions", [])
    if not isinstance(copy_payload, list) or not all(
        isinstance(value, str) and re.fullmatch(r"\.[A-Za-z0-9]+", value)
        for value in copy_payload
    ):
        raise ArxivPackageError(
            "copy_extensions must be an array of extensions such as '.pdf'"
        )
    copy_extensions = frozenset(value.lower() for value in copy_payload)
    overlap = strip_extensions & copy_extensions
    if overlap:
        raise ArxivPackageError(
            "extensions cannot be both sanitized and copied verbatim: "
            + ", ".join(sorted(overlap))
        )

    max_archive_bytes = payload.get("max_archive_bytes")
    if not isinstance(max_archive_bytes, int) or isinstance(max_archive_bytes, bool):
        raise ArxivPackageError("max_archive_bytes must be a positive integer")
    if max_archive_bytes <= 0:
        raise ArxivPackageError("max_archive_bytes must be a positive integer")
    max_uncompressed_bytes = payload.get("max_uncompressed_bytes")
    if not isinstance(max_uncompressed_bytes, int) or isinstance(max_uncompressed_bytes, bool):
        raise ArxivPackageError("max_uncompressed_bytes must be a positive integer")
    if max_uncompressed_bytes <= 0:
        raise ArxivPackageError("max_uncompressed_bytes must be a positive integer")
    compile_timeout_seconds = payload.get("compile_timeout_seconds")
    if not isinstance(compile_timeout_seconds, int) or isinstance(compile_timeout_seconds, bool):
        raise ArxivPackageError("compile_timeout_seconds must be a positive integer")
    if compile_timeout_seconds <= 0:
        raise ArxivPackageError("compile_timeout_seconds must be a positive integer")

    destinations = [item.destination for item in generated] + [item.destination for item in extra_files]
    if len(destinations) != len(set(destinations)):
        raise ArxivPackageError("generated file destinations must be unique")
    _assert_casefold_unique(destinations, "configured archive destinations")

    return ArxivConfig(
        project_root=root,
        config_path=config_absolute,
        entrypoint=entrypoint,
        compiler=compiler,
        texlive_version=texlive_version,
        recorder=recorder,
        allowed_roots=allowed_roots,
        generated_files=tuple(generated),
        extra_files=tuple(extra_files),
        strip_comment_extensions=strip_extensions,
        copy_extensions=copy_extensions,
        archive=archive,
        max_archive_bytes=max_archive_bytes,
        max_uncompressed_bytes=max_uncompressed_bytes,
        compile_timeout_seconds=compile_timeout_seconds,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _has_forbidden_extension(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(extension) for extension in FORBIDDEN_EXTENSIONS)


def _assert_safe_archive_path(path: Path, label: str) -> None:
    _relative_path(path.as_posix(), label)
    if path.name in FORBIDDEN_NAMES:
        raise ArxivPackageError(f"{label} uses forbidden file name: {path}")
    if _has_forbidden_extension(path):
        raise ArxivPackageError(f"{label} uses forbidden generated extension: {path}")


def _assert_casefold_unique(paths: Iterable[Path], label: str) -> None:
    seen: dict[str, Path] = {}
    for path in paths:
        folded = path.as_posix().casefold()
        previous = seen.get(folded)
        if previous is not None and previous != path:
            raise ArxivPackageError(
                f"{label} collide on case-insensitive filesystems: {previous}, {path}"
            )
        seen[folded] = path


def _assert_no_symlinks(root: Path, relative: Path, label: str) -> None:
    current = root
    for part in relative.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError as error:
            raise ArxivPackageError(f"{label} does not exist: {relative}") from error
        if stat.S_ISLNK(mode):
            raise ArxivPackageError(f"{label} must not contain a symbolic link: {relative}")


def _assert_no_existing_symlinks(root: Path, relative: Path, label: str) -> None:
    current = root
    for part in relative.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return
        if stat.S_ISLNK(mode):
            raise ArxivPackageError(f"{label} must not contain a symbolic link: {relative}")


def _is_under(path: Path, roots: Iterable[Path]) -> bool:
    return any(path == root or root in path.parents for root in roots)


def _is_allowed(relative: Path, allowed_roots: Sequence[Path]) -> bool:
    return any(relative == root or root in relative.parents for root in allowed_roots)


def _canonical_project_file(root: Path, recorded_path: Path, label: str) -> tuple[Path, Path]:
    """Return lexical relative and absolute paths without hiding symlink traversal."""

    if recorded_path.is_absolute():
        try:
            relative = recorded_path.relative_to(root)
        except ValueError as error:
            raise ArxivPackageError(f"{label} is outside the project root: {recorded_path}") from error
    else:
        relative = recorded_path
    if ".." in relative.parts:
        raise ArxivPackageError(f"{label} contains path traversal: {recorded_path}")
    relative = Path(*[part for part in relative.parts if part not in {"", "."}])
    _assert_safe_archive_path(relative, label)
    _assert_no_symlinks(root, relative, label)
    absolute = root / relative
    if not absolute.is_file():
        raise ArxivPackageError(f"{label} is not a regular file: {relative}")
    return relative, absolute


def discover_tex_system_roots() -> tuple[Path, ...]:
    """Return the installed TeX tree roots that may safely remain outside the archive."""

    roots: set[Path] = set()
    for variable in ("TEXMFDIST", "TEXMFSYSVAR"):
        try:
            process = subprocess.run(
                ["kpsewhich", f"--var-value={variable}"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as error:
            raise ArxivPackageError(
                "kpsewhich is required to distinguish TeX-distribution files from manuscript inputs"
            ) from error
        value = process.stdout.strip()
        if value:
            roots.add(Path(value).resolve())
    try:
        texmf_configuration = subprocess.run(
            ["kpsewhich", "texmf.cnf"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise ArxivPackageError("kpsewhich could not locate the active texmf.cnf") from error
    if texmf_configuration:
        roots.add(Path(texmf_configuration).resolve())
    if not roots:
        raise ArxivPackageError("kpsewhich did not report any TeX distribution roots")
    return tuple(sorted(roots, key=lambda item: item.as_posix()))


def parse_recorder(path: Path, initial_working_directory: Path) -> RecorderData:
    """Parse INPUT and OUTPUT records, retaining their lexical locations."""

    if not path.is_file():
        raise ArxivPackageError(f"LaTeX recorder file does not exist: {path}")
    working_directory = initial_working_directory
    inputs: set[Path] = set()
    outputs: set[Path] = set()
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8", errors="strict").splitlines(), start=1
    ):
        if raw_line.startswith("PWD "):
            candidate = Path(raw_line[4:])
            if not candidate.is_absolute():
                raise ArxivPackageError(f"{path}:{line_number}: PWD must be absolute")
            working_directory = candidate
            continue
        for marker, target in (("INPUT ", inputs), ("OUTPUT ", outputs)):
            if raw_line.startswith(marker):
                value = raw_line[len(marker) :]
                if not value:
                    raise ArxivPackageError(f"{path}:{line_number}: empty {marker.strip()} record")
                candidate = Path(value)
                if not candidate.is_absolute():
                    candidate = working_directory / candidate
                target.add(candidate)
                break
    if not inputs:
        raise ArxivPackageError(f"LaTeX recorder contains no inputs: {path}")
    return RecorderData(inputs=frozenset(inputs), outputs=frozenset(outputs))


def discover_archive_files(
    config: ArxivConfig,
    recorder: RecorderData,
    tex_system_roots: Sequence[Path],
) -> dict[Path, Path]:
    """Map archive destinations to source files using the recorder dependency closure."""

    root = config.project_root
    system_roots = tuple(path.resolve() for path in tex_system_roots)
    output_resolved = {path.resolve(strict=False) for path in recorder.outputs}
    generated_by_source: dict[Path, GeneratedFile] = {}
    for item in config.generated_files:
        relative, absolute = _canonical_project_file(root, item.source, "generated file source")
        _assert_safe_archive_path(item.destination, "generated file destination")
        generated_by_source[absolute.resolve()] = GeneratedFile(relative, item.destination)

    extra_by_destination: dict[Path, Path] = {}
    for item in config.extra_files:
        _, absolute = _canonical_project_file(root, item.source, "extra file source")
        _assert_safe_archive_path(item.destination, "extra file destination")
        extra_by_destination[item.destination] = absolute

    archive_files: dict[Path, Path] = {}
    seen_generated: set[Path] = set()
    for recorded in sorted(recorder.inputs, key=lambda item: item.as_posix()):
        resolved = recorded.resolve(strict=False)
        if _is_under(resolved, system_roots):
            continue
        try:
            relative_lexical = recorded.relative_to(root)
        except ValueError:
            raise ArxivPackageError(
                f"recorder input is neither in the project nor the TeX distribution: {recorded}"
            )
        if ".." in relative_lexical.parts:
            raise ArxivPackageError(f"recorder input escapes the project root: {recorded}")

        generated = generated_by_source.get(resolved)
        if generated is not None:
            _, absolute = _canonical_project_file(root, generated.source, "generated file source")
            if generated.destination in archive_files:
                raise ArxivPackageError(f"archive destination collision: {generated.destination}")
            archive_files[generated.destination] = absolute
            seen_generated.add(resolved)
            continue

        if resolved in output_resolved:
            continue

        relative, absolute = _canonical_project_file(root, relative_lexical, "recorder input")
        if not _is_allowed(relative, config.allowed_roots):
            raise ArxivPackageError(f"recorder input is outside allowed_roots: {relative}")
        if relative in archive_files and archive_files[relative] != absolute:
            raise ArxivPackageError(f"archive destination collision: {relative}")
        archive_files[relative] = absolute

    missing_generated = sorted(set(generated_by_source) - seen_generated)
    if missing_generated:
        formatted = ", ".join(str(path.relative_to(root)) for path in missing_generated)
        raise ArxivPackageError(
            f"configured generated files were not used by the recorded build: {formatted}"
        )
    if config.entrypoint not in archive_files:
        raise ArxivPackageError(f"recorded build did not use the configured entrypoint: {config.entrypoint}")
    if not archive_files:
        raise ArxivPackageError("recorded build produced an empty project dependency set")
    for destination, source in extra_by_destination.items():
        if destination in archive_files:
            raise ArxivPackageError(f"archive destination collision: {destination}")
        archive_files[destination] = source
    _assert_casefold_unique(archive_files, "archive destinations")
    return dict(sorted(archive_files.items(), key=lambda item: item[0].as_posix()))


def _read_control_word(text: str, start: int) -> tuple[str, int]:
    """Read a TeX control word at a backslash; control symbols have a one-char name."""

    if start >= len(text) or text[start] != "\\":
        raise ValueError("control sequence must start with a backslash")
    cursor = start + 1
    if cursor >= len(text):
        return "", cursor
    if text[cursor].isalpha() or text[cursor] == "@":
        end = cursor + 1
        while end < len(text) and (text[end].isalpha() or text[end] == "@"):
            end += 1
        return text[cursor:end], end
    return text[cursor], cursor + 1


def _balanced_group_end(text: str, start: int, *, url_mode: bool = False) -> int:
    if start >= len(text) or text[start] != "{":
        raise ArxivPackageError("expected a braced argument while sanitizing LaTeX")
    depth = 0
    cursor = start
    while cursor < len(text):
        character = text[cursor]
        if character == "\\":
            _, cursor = _read_control_word(text, cursor)
            continue
        if character == "%":
            if url_mode and re.match(r"[0-9A-Fa-f]{2}", text[cursor + 1 : cursor + 3]):
                cursor += 3
                continue
            if url_mode:
                raise ArxivPackageError(
                    "ambiguous percent in URL-like argument; use a percent-encoded URL or remove it"
                )
            newline = text.find("\n", cursor + 1)
            if newline < 0:
                raise ArxivPackageError("comment hides the end of a braced LaTeX argument")
            cursor = newline + 1
            continue
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return cursor + 1
        cursor += 1
    raise ArxivPackageError("unclosed braced argument while sanitizing LaTeX")


def _literal_environment_span(text: str, start: int) -> tuple[int, int] | None:
    match = re.match(r"\\begin\s*\{([^{}]+)\}", text[start:])
    if match is None or match.group(1) not in LITERAL_ENVIRONMENTS:
        return None
    environment = match.group(1)
    body_start = start + match.end()
    closing = re.compile(r"\\end\s*\{" + re.escape(environment) + r"\}")
    end_match = closing.search(text, body_start)
    if end_match is None:
        raise ArxivPackageError(f"unclosed literal environment: {environment}")
    literal_end = end_match.end()
    opening_line_end = text.find("\n", start, literal_end)
    body_start = opening_line_end + 1 if opening_line_end >= 0 else start
    return body_start, literal_end


def _contains_unescaped_percent(text: str) -> bool:
    cursor = 0
    while cursor < len(text):
        if text[cursor] == "\\":
            _, cursor = _read_control_word(text, cursor)
            continue
        if text[cursor] == "%":
            return True
        cursor += 1
    return False


def _sanitize_url_group(text: str) -> str:
    """Remove comments from a URL-like argument while preserving percent escapes."""

    output: list[str] = []
    cursor = 0
    while cursor < len(text):
        character = text[cursor]
        if character == "\\":
            _, command_end = _read_control_word(text, cursor)
            output.append(text[cursor:command_end])
            cursor = command_end
            continue
        if character == "%":
            if re.match(r"[0-9A-Fa-f]{2}", text[cursor + 1 : cursor + 3]):
                output.append(text[cursor : cursor + 3])
                cursor += 3
                continue
            raise ArxivPackageError(
                "ambiguous percent in URL-like argument; use a percent-encoded URL or remove it"
            )
        output.append(character)
        cursor += 1
    return "".join(output)


def strip_latex_comments(text: str) -> str:
    """Remove TeX comments while retaining literal percent characters.

    The newline consumed by an unescaped percent marker is also removed.  This
    preserves TeX token adjacency for inline comments such as ``foo%\nbar``.
    Visible literal content in ``\\verb`` and common literal environments is
    retained. URL percent escapes are retained while source comments are removed.
    """

    output: list[str] = []
    cursor = 0
    while cursor < len(text):
        character = text[cursor]
        if character == "\\":
            literal_span = _literal_environment_span(text, cursor)
            if literal_span is not None:
                body_start, literal_end = literal_span
                opening_line = text[cursor:body_start]
                if _contains_unescaped_percent(opening_line):
                    raise ArxivPackageError(
                        "remove comments from literal-environment opening lines before packaging"
                    )
                output.append(opening_line)
                output.append(text[body_start:literal_end])
                cursor = literal_end
                continue

            command, command_end = _read_control_word(text, cursor)
            if command == "verb":
                if command_end < len(text) and text[command_end] == "*":
                    command_end += 1
                if command_end >= len(text) or text[command_end].isspace():
                    raise ArxivPackageError(r"malformed \verb command while sanitizing LaTeX")
                delimiter = text[command_end]
                verb_end = text.find(delimiter, command_end + 1)
                if verb_end < 0:
                    raise ArxivPackageError(r"unclosed \verb command while sanitizing LaTeX")
                output.append(text[cursor : verb_end + 1])
                cursor = verb_end + 1
                continue

            protected_arguments = 0
            if command in URL_ARGUMENT_COMMANDS:
                protected_arguments = 1
            elif command == "href":
                protected_arguments = 1
            if protected_arguments:
                argument_start = command_end
                while argument_start < len(text) and text[argument_start].isspace():
                    argument_start += 1
                if argument_start < len(text) and text[argument_start] == "{":
                    argument_end = _balanced_group_end(text, argument_start, url_mode=True)
                    output.append(text[cursor:argument_start])
                    output.append(_sanitize_url_group(text[argument_start:argument_end]))
                    cursor = argument_end
                    continue

            output.append(text[cursor:command_end])
            cursor = command_end
            continue

        if character == "%":
            newline = text.find("\n", cursor + 1)
            if newline < 0:
                break
            cursor = newline + 1
            while cursor < len(text) and text[cursor] in {" ", "\t"}:
                cursor += 1
            continue

        output.append(character)
        cursor += 1
    return "".join(output)


def _mask_literal_regions(text: str) -> str:
    """Mask visible literal content before scanning for hidden-source constructs."""

    masked = list(text)

    def blank(start: int, end: int) -> None:
        for index in range(start, end):
            if masked[index] != "\n":
                masked[index] = " "

    cursor = 0
    while cursor < len(text):
        if text[cursor] != "\\":
            cursor += 1
            continue
        literal_span = _literal_environment_span(text, cursor)
        if literal_span is not None:
            _, literal_end = literal_span
            blank(cursor, literal_end)
            cursor = literal_end
            continue
        command, command_end = _read_control_word(text, cursor)
        if command == "verb":
            delimiter_start = command_end + (1 if text[command_end:command_end + 1] == "*" else 0)
            if delimiter_start >= len(text) or text[delimiter_start].isspace():
                raise ArxivPackageError(r"malformed \verb command while scanning LaTeX")
            delimiter = text[delimiter_start]
            verb_end = text.find(delimiter, delimiter_start + 1)
            if verb_end < 0:
                raise ArxivPackageError(r"unclosed \verb command while scanning LaTeX")
            blank(cursor, verb_end + 1)
            cursor = verb_end + 1
            continue
        if command in URL_ARGUMENT_COMMANDS or command == "href":
            argument_start = command_end
            while argument_start < len(text) and text[argument_start].isspace():
                argument_start += 1
            if argument_start < len(text) and text[argument_start] == "{":
                argument_end = _balanced_group_end(text, argument_start, url_mode=True)
                blank(argument_start, argument_end)
                cursor = argument_end
                continue
        cursor = command_end
    return "".join(masked)


def find_internal_source_constructs(text: str) -> tuple[str, ...]:
    """Find common constructs that can conceal internal source from the PDF."""

    sanitized = strip_latex_comments(text)
    matches: list[str] = []
    if "^^" in sanitized:
        matches.append(r"TeX ^^ character notation")
    scannable = _mask_literal_regions(sanitized)
    matches.extend(
        label for pattern, label in INTERNAL_SOURCE_PATTERNS if pattern.search(scannable)
    )
    end_document = re.search(r"\\end\s*\{document\}", scannable)
    if end_document is not None and sanitized[end_document.end() :].strip():
        matches.append(r"content after \end{document}")
    end_input = re.search(r"\\endinput\b", scannable)
    if end_input is not None and sanitized[end_input.end() :].strip():
        matches.append(r"content after \endinput")
    return tuple(matches)


def freeze_submission_date(text: str, submission_date: date) -> str:
    r"""Freeze the standard \paperdate definition, never literal examples or user macros."""

    months = (
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    )
    formatted = f"{months[submission_date.month - 1]} {submission_date.day}, {submission_date.year}"
    pattern = re.compile(r"(\\newcommand\s*\{\\paperdate\}\s*\{)\s*\\today\s*(\})")
    for match in reversed(list(pattern.finditer(_mask_literal_regions(text)))):
        text = text[:match.start()] + match[1] + formatted + match[2] + text[match.end():]
    if re.search(r"(?<!\\)\\today\b", _mask_literal_regions(text)):
        raise ArxivPackageError(
            r"unfrozen \today outside the standard \newcommand{\paperdate}{\today}; "
            "use an explicit date for custom or localized date expressions"
        )
    return text


def submission_build_environment(submission_date: date) -> dict[str, str]:
    """Make the reference PDF use the same date as staged source, including near midnight."""

    timestamp = datetime(
        submission_date.year, submission_date.month, submission_date.day, 12,
        tzinfo=timezone.utc,
    )
    return {
        **os.environ,
        "SOURCE_DATE_EPOCH": str(int(timestamp.timestamp())),
        "FORCE_SOURCE_DATE": "1",
        "TZ": "UTC",
    }


def sanitized_source(
    source: Path,
    destination: Path,
    strip_extensions: frozenset[str],
    copy_extensions: frozenset[str],
    *,
    explicitly_reviewed: bool,
    submission_date: date,
) -> None:
    payload = source.read_bytes()
    extension = destination.suffix.lower()
    if extension in TEX_LANGUAGE_EXTENSIONS and extension not in strip_extensions:
        raise ArxivPackageError(
            f"TeX-language source extension must be listed in strip_comment_extensions: {destination}"
        )
    if extension not in strip_extensions:
        if not explicitly_reviewed and extension not in copy_extensions:
            raise ArxivPackageError(
                "archive input has an unclassified extension; add it to copy_extensions only "
                f"after reviewing the file, or declare it as an extra file: {destination}"
            )
        destination.write_bytes(payload)
        return
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ArxivPackageError(f"manuscript source is not UTF-8: {source}") from error
    internal = find_internal_source_constructs(text)
    if internal:
        raise ArxivPackageError(
            f"{source}: remove internal or ambiguous LaTeX constructs before upload: "
            + ", ".join(internal)
        )
    with destination.open("w", encoding="utf-8", newline="") as handle:
        handle.write(freeze_submission_date(strip_latex_comments(text), submission_date))


def stage_archive_files(
    archive_files: dict[Path, Path],
    staging_root: Path,
    strip_extensions: frozenset[str],
    copy_extensions: frozenset[str],
    reviewed_destinations: frozenset[Path],
    submission_date: date,
) -> tuple[Path, ...]:
    members: list[Path] = []
    for relative, source in sorted(archive_files.items(), key=lambda item: item[0].as_posix()):
        _assert_safe_archive_path(relative, "archive member")
        destination = staging_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        sanitized_source(
            source,
            destination,
            strip_extensions,
            copy_extensions,
            explicitly_reviewed=relative in reviewed_destinations,
            submission_date=submission_date,
        )
        members.append(relative)
    return tuple(members)


def write_deterministic_zip(staging_root: Path, members: Sequence[Path], archive: Path) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    temporary_archive = archive.with_name(f".{archive.name}.tmp")
    try:
        with zipfile.ZipFile(
            temporary_archive,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as bundle:
            for relative in sorted(members, key=lambda item: item.as_posix()):
                info = zipfile.ZipInfo(relative.as_posix(), date_time=FIXED_ZIP_TIME)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.flag_bits |= 0x800
                bundle.writestr(info, (staging_root / relative).read_bytes(), compresslevel=9)
        temporary_archive.replace(archive)
    finally:
        if temporary_archive.exists():
            temporary_archive.unlink()


def report_paths(archive: Path) -> tuple[Path, Path]:
    return (
        archive.with_suffix(archive.suffix + ".contents.txt"),
        archive.with_suffix(archive.suffix + ".sha256"),
    )


def write_reports(archive: Path, members: Sequence[Path]) -> PackageResult:
    contents_report, checksum_report = report_paths(archive)
    names = tuple(sorted((path.as_posix() for path in members)))
    contents_report.write_text("\n".join(names) + "\n", encoding="utf-8")
    digest = sha256(archive)
    checksum_report.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return PackageResult(archive, contents_report, checksum_report, names, digest)


def _final_output_paths(config: ArxivConfig) -> tuple[Path, Path, Path]:
    archive = config.project_root / config.archive
    contents_report, checksum_report = report_paths(archive)
    return archive, contents_report, checksum_report


def clear_package_outputs(config: ArxivConfig) -> None:
    """Remove prior package artifacts so a failed run cannot leave a stale ZIP."""

    _assert_no_existing_symlinks(config.project_root, config.archive.parent, "archive output path")
    for path in _final_output_paths(config):
        if path.is_symlink():
            raise ArxivPackageError(f"archive output must not be a symbolic link: {path}")
        if path.exists():
            if not path.is_file():
                raise ArxivPackageError(f"archive output is not a regular file: {path}")
            path.unlink()


def publish_package(candidate: PackageResult, config: ArxivConfig) -> PackageResult:
    """Publish validated reports first and the uploadable ZIP last."""

    final_archive, final_contents, final_checksum = _final_output_paths(config)
    _assert_no_existing_symlinks(config.project_root, config.archive.parent, "archive output path")
    final_archive.parent.mkdir(parents=True, exist_ok=True)
    transfers = (
        (candidate.contents_report, final_contents),
        (candidate.checksum_report, final_checksum),
        (candidate.archive, final_archive),
    )
    for source, destination in transfers:
        temporary = destination.with_name(f".{destination.name}.tmp")
        try:
            shutil.copyfile(source, temporary)
            temporary.replace(destination)
        finally:
            if temporary.exists():
                temporary.unlink()
    return PackageResult(
        final_archive,
        final_contents,
        final_checksum,
        candidate.members,
        candidate.sha256,
    )


def _compiler_command(
    config: ArxivConfig,
    *,
    recorder: bool,
    output_directory: Path | None = None,
) -> list[str]:
    command = [item.replace("{entrypoint}", config.entrypoint.as_posix()) for item in config.compiler]
    if not any("{entrypoint}" in item for item in config.compiler):
        command.append(config.entrypoint.as_posix())
    executable = Path(command[0]).name
    if recorder and executable in {"latex", "latexmk", "lualatex", "pdflatex", "xelatex"}:
        if "-recorder" not in command:
            command.insert(1, "-recorder")
        if executable == "latexmk" and "-g" not in command:
            command.insert(1, "-g")
    if executable == "latexmk" and output_directory is not None:
        output_option = f"-outdir={output_directory.as_posix()}"
        auxiliary_option = f"-auxdir={output_directory.as_posix()}"
        if not any(item.startswith("-outdir=") for item in command):
            command.insert(1, output_option)
        if not any(item.startswith("-auxdir=") for item in command):
            command.insert(1, auxiliary_option)
    if executable in {"latex", "latexmk", "lualatex", "pdflatex", "xelatex"}:
        if "-no-shell-escape" not in command:
            command.insert(1, "-no-shell-escape")
    return command


def run_source_build(config: ArxivConfig, *, submission_date: date) -> None:
    recorder = config.project_root / config.recorder
    if recorder.exists():
        recorder.unlink()
    command = _compiler_command(config, recorder=True, output_directory=config.recorder.parent)
    try:
        process = subprocess.run(
            command,
            cwd=config.project_root,
            env=submission_build_environment(submission_date),
            capture_output=True,
            text=True,
            timeout=config.compile_timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        raise ArxivPackageError(
            f"source manuscript build exceeded {config.compile_timeout_seconds} seconds"
        ) from error
    if process.returncode != 0:
        combined_output = process.stdout + "\n" + process.stderr
        raise ArxivPackageError(
            f"source manuscript build failed with exit code {process.returncode}\n"
            + combined_output[-4000:]
        )
    if not recorder.is_file():
        raise ArxivPackageError(f"source build did not create recorder file: {config.recorder}")


def run_submission_checks(config: ArxivConfig) -> None:
    """Run the repository's strict final-readiness gate before publishing an archive."""

    try:
        process = subprocess.run(
            ["make", "submission-check"],
            cwd=config.project_root,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise ArxivPackageError("make is required to run submission readiness checks") from error
    if process.returncode != 0:
        combined_output = process.stdout + "\n" + process.stderr
        raise ArxivPackageError(
            "submission readiness checks failed; no arXiv ZIP was published\n"
            + combined_output[-12000:]
        )


def _validated_zip_members(
    bundle: zipfile.ZipFile,
    max_uncompressed_bytes: int,
) -> tuple[zipfile.ZipInfo, ...]:
    infos = tuple(bundle.infolist())
    if not infos:
        raise ArxivPackageError("source ZIP is empty")
    names: set[str] = set()
    total_uncompressed_bytes = 0
    for info in infos:
        if info.is_dir():
            raise ArxivPackageError(f"source ZIP must not contain explicit directories: {info.filename}")
        path = _relative_path(info.filename, "ZIP member")
        if info.filename != path.as_posix():
            raise ArxivPackageError(
                f"source ZIP contains a noncanonical member path: {info.filename}"
            )
        _assert_safe_archive_path(path, "ZIP member")
        if info.filename in names:
            raise ArxivPackageError(f"source ZIP contains a duplicate member: {info.filename}")
        names.add(info.filename)
        total_uncompressed_bytes += info.file_size
        if total_uncompressed_bytes > max_uncompressed_bytes:
            raise ArxivPackageError(
                "source ZIP exceeds the configured uncompressed-size limit of "
                f"{max_uncompressed_bytes} bytes"
            )
        unix_mode = (info.external_attr >> 16) & 0xFFFF
        if stat.S_ISLNK(unix_mode):
            raise ArxivPackageError(f"source ZIP contains a symbolic link: {info.filename}")
    _assert_casefold_unique((Path(name) for name in names), "ZIP members")
    return infos


def extract_validated_zip(
    archive: Path,
    destination: Path,
    max_uncompressed_bytes: int,
) -> tuple[Path, ...]:
    try:
        with zipfile.ZipFile(archive) as bundle:
            infos = _validated_zip_members(bundle, max_uncompressed_bytes)
            members: list[Path] = []
            for info in infos:
                relative = Path(info.filename)
                output = destination / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(info) as source, output.open("wb") as target:
                    shutil.copyfileobj(source, target)
                members.append(relative)
            return tuple(members)
    except (OSError, zipfile.BadZipFile) as error:
        raise ArxivPackageError(f"cannot read source ZIP {archive}: {error}") from error


def _isolated_environment(sandbox: Path) -> dict[str, str]:
    environment = dict(os.environ)
    for variable in (
        "BIBINPUTS",
        "BSTINPUTS",
        "LATEXINPUTS",
        "TEXINPUTS",
        "TEXMFCONFIG",
        "TEXMFHOME",
        "TEXMFVAR",
    ):
        environment.pop(variable, None)
    home = sandbox / "home"
    texmf_home = sandbox / "texmf-home"
    texmf_config = sandbox / "texmf-config"
    texmf_var = sandbox / "texmf-var"
    for directory in (home, texmf_home, texmf_config, texmf_var):
        directory.mkdir(parents=True, exist_ok=True)
    environment.update(
        {
            "HOME": str(home),
            "TEXMFHOME": str(texmf_home),
            "TEXMFCONFIG": str(texmf_config),
            "TEXMFVAR": str(texmf_var),
        }
    )
    return environment


def _read_compile_log(root: Path, entrypoint: Path, process_output: str) -> str:
    expected = root / entrypoint.with_suffix(".log")
    candidates = [expected] if expected.is_file() else sorted(root.rglob(entrypoint.stem + ".log"))
    if not candidates:
        raise ArxivPackageError("isolated compilation did not produce a LaTeX log")
    return process_output + "\n" + candidates[-1].read_text(encoding="utf-8", errors="replace")


def validate_compile_log(log_text: str) -> None:
    failures = sorted({pattern.pattern for pattern in LOG_FAILURE_PATTERNS if pattern.search(log_text)})
    if failures:
        raise ArxivPackageError(
            "isolated compilation log reports missing citations, references, or a fatal error: "
            + "; ".join(failures)
        )


def _render_pdf_pages(
    pdf: Path,
    output_root: Path,
    timeout_seconds: int,
) -> tuple[Path, ...]:
    ghostscript = shutil.which("gs")
    if ghostscript is None:
        raise ArxivPackageError(
            "Ghostscript ('gs') is required to compare the repository and packaged PDFs"
        )
    output_root.mkdir(parents=True, exist_ok=True)
    output_pattern = output_root / "page-%04d.png"
    try:
        process = subprocess.run(
            [
                ghostscript,
                "-dSAFER",
                "-dBATCH",
                "-dNOPAUSE",
                "-dUseCropBox",
                "-sDEVICE=png16m",
                "-r144",
                "-dTextAlphaBits=4",
                "-dGraphicsAlphaBits=4",
                f"-sOutputFile={output_pattern}",
                str(pdf),
            ],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        raise ArxivPackageError(
            f"PDF rendering exceeded {timeout_seconds} seconds: {pdf}"
        ) from error
    if process.returncode != 0:
        raise ArxivPackageError(
            f"could not render PDF for archive comparison: {pdf}\n"
            + (process.stdout + "\n" + process.stderr)[-4000:]
        )
    pages = tuple(sorted(output_root.glob("page-*.png")))
    if not pages:
        raise ArxivPackageError(f"PDF rendering produced no pages: {pdf}")
    return pages


def validate_rendered_equivalence(
    reference_pdf: Path,
    packaged_pdf: Path,
    work_root: Path,
    timeout_seconds: int = 300,
) -> None:
    """Require the sanitized source package to render exactly like the repository build."""

    if not reference_pdf.is_file():
        raise ArxivPackageError(f"repository build PDF does not exist: {reference_pdf}")
    reference_pages = _render_pdf_pages(
        reference_pdf,
        work_root / "repository",
        timeout_seconds,
    )
    packaged_pages = _render_pdf_pages(
        packaged_pdf,
        work_root / "package",
        timeout_seconds,
    )
    if len(reference_pages) != len(packaged_pages):
        raise ArxivPackageError(
            "sanitized source package changed the rendered page count: "
            f"repository={len(reference_pages)}, package={len(packaged_pages)}"
        )
    changed_pages = [
        index
        for index, (reference, packaged) in enumerate(
            zip(reference_pages, packaged_pages), start=1
        )
        if sha256(reference) != sha256(packaged)
    ]
    if changed_pages:
        page_list = ", ".join(str(page) for page in changed_pages)
        raise ArxivPackageError(
            "sanitizing or relocating the source changed rendered manuscript pages: " + page_list
        )


def audit_isolated_recorder_inputs(
    recorder: RecorderData,
    extraction_root: Path,
    trusted_tex_roots: Sequence[Path],
) -> frozenset[Path]:
    """Return used package members and reject undeclared external build inputs."""

    extraction_root = extraction_root.resolve()
    trusted_roots = tuple(path.resolve() for path in trusted_tex_roots)
    compiled_outputs = {path.resolve(strict=False) for path in recorder.outputs}
    used_members: set[Path] = set()
    for recorded in recorder.inputs:
        resolved = recorded.resolve(strict=False)
        if resolved in compiled_outputs:
            continue
        try:
            used_members.add(resolved.relative_to(extraction_root))
            continue
        except ValueError:
            pass
        if _is_under(resolved, trusted_roots):
            continue
        raise ArxivPackageError(
            "isolated compilation read an undeclared external file: " + str(recorded)
        )
    return frozenset(used_members)


def validate_archive(
    archive: Path,
    config: ArxivConfig,
    reference_pdf: Path | None = None,
) -> tuple[str, ...]:
    """Extract and compile an archive without access to repository-local inputs."""

    if not archive.is_file():
        raise ArxivPackageError(f"source ZIP does not exist: {archive}")
    if archive.stat().st_size > config.max_archive_bytes:
        raise ArxivPackageError(
            f"source ZIP is {archive.stat().st_size} bytes; limit is {config.max_archive_bytes} bytes"
        )
    with tempfile.TemporaryDirectory(prefix="arxiv-validate-") as temporary:
        sandbox = Path(temporary)
        extraction_root = sandbox / "source"
        extraction_root.mkdir()
        members = extract_validated_zip(
            archive,
            extraction_root,
            config.max_uncompressed_bytes,
        )
        if config.entrypoint not in members:
            raise ArxivPackageError(f"source ZIP is missing entrypoint: {config.entrypoint}")
        command = _compiler_command(config, recorder=True)
        try:
            process = subprocess.run(
                command,
                cwd=extraction_root,
                env=_isolated_environment(sandbox),
                capture_output=True,
                text=True,
                timeout=config.compile_timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            raise ArxivPackageError(
                f"isolated compilation exceeded {config.compile_timeout_seconds} seconds"
            ) from error
        combined_output = process.stdout + "\n" + process.stderr
        if process.returncode != 0:
            raise ArxivPackageError(
                f"isolated source ZIP compilation failed with exit code {process.returncode}\n"
                + combined_output[-4000:]
            )
        log_text = _read_compile_log(extraction_root, config.entrypoint, combined_output)
        validate_compile_log(log_text)
        packaged_pdf = extraction_root / config.entrypoint.with_suffix(".pdf")
        if not packaged_pdf.is_file():
            candidates = tuple(extraction_root.rglob(config.entrypoint.stem + ".pdf"))
            if not candidates:
                raise ArxivPackageError("isolated compilation did not produce the manuscript PDF")
            packaged_pdf = candidates[-1]
        if reference_pdf is not None:
            validate_rendered_equivalence(
                reference_pdf,
                packaged_pdf,
                sandbox / "rendered",
                config.compile_timeout_seconds,
            )
        recorder_candidates = sorted(extraction_root.rglob(config.entrypoint.stem + ".fls"))
        if not recorder_candidates:
            raise ArxivPackageError("isolated compilation did not produce a recorder file")
        packaged_recorder = parse_recorder(recorder_candidates[-1], extraction_root)
        used_members = audit_isolated_recorder_inputs(
            packaged_recorder,
            extraction_root,
            discover_tex_system_roots(),
        )
        exempt = {item.destination for item in config.extra_files}
        unused = sorted(set(members) - exempt - used_members)
        if unused:
            raise ArxivPackageError(
                "source ZIP contains runtime files not used by the isolated build: "
                + ", ".join(path.as_posix() for path in unused)
            )
        return tuple(path.as_posix() for path in members)


def package_from_recorder(
    config: ArxivConfig,
    tex_system_roots: Sequence[Path] | None = None,
    archive_path: Path | None = None,
    *,
    submission_date: date | None = None,
) -> PackageResult:
    recorder = parse_recorder(config.project_root / config.recorder, config.project_root)
    system_roots = tuple(tex_system_roots) if tex_system_roots is not None else discover_tex_system_roots()
    archive_files = discover_archive_files(config, recorder, system_roots)
    archive = archive_path if archive_path is not None else config.project_root / config.archive
    if archive_path is None:
        _assert_no_existing_symlinks(
            config.project_root,
            config.archive.parent,
            "archive output path",
        )
    with tempfile.TemporaryDirectory(prefix="arxiv-stage-") as temporary:
        staging_root = Path(temporary)
        members = stage_archive_files(
            archive_files,
            staging_root,
            config.strip_comment_extensions,
            config.copy_extensions,
            frozenset(item.destination for item in config.extra_files),
            submission_date or date.today(),
        )
        write_deterministic_zip(staging_root, members, archive)
    if archive.stat().st_size > config.max_archive_bytes:
        archive.unlink()
        raise ArxivPackageError(
            f"source ZIP exceeds configured limit of {config.max_archive_bytes} bytes"
        )
    return write_reports(archive, members)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv)
    try:
        config = load_config(arguments.project_root, arguments.config)
        if arguments.clear_output:
            clear_package_outputs(config)
            print("Cleared prior arXiv package outputs.")
            return 0
        if arguments.check is not None:
            archive = arguments.check
            if not archive.is_absolute():
                archive = config.project_root / archive
            members = validate_archive(archive, config)
            print(f"Validated {archive} ({len(members)} files).")
            print(f"At arXiv, select only {config.entrypoint.as_posix()} as the primary TeX file.")
            return 0

        if not arguments.smoke_test:
            clear_package_outputs(config)
            run_submission_checks(config)
        submission_date = arguments.submission_date or date.today()
        print(f"Submission date: {submission_date.isoformat()} (working source is unchanged).")
        run_source_build(config, submission_date=submission_date)
        with tempfile.TemporaryDirectory(prefix="arxiv-candidate-") as temporary:
            candidate_path = Path(temporary) / config.archive.name
            candidate = package_from_recorder(
                config, archive_path=candidate_path, submission_date=submission_date,
            )
            reference_pdf = config.project_root / config.recorder.with_suffix(".pdf")
            validate_archive(candidate.archive, config, reference_pdf=reference_pdf)
            if arguments.smoke_test:
                print(
                    "Smoke-tested arXiv source packaging "
                    f"({len(candidate.members)} files); no ZIP was published."
                )
                if config.texlive_version:
                    print(f"Configured TeX Live compatibility target: {config.texlive_version}")
                return 0
            result = publish_package(candidate, config)
        print(f"Created and validated {result.archive} ({len(result.members)} files).")
        print(f"SHA-256: {result.sha256}")
        print(f"Contents: {result.contents_report}")
        print(f"Checksum: {result.checksum_report}")
        if config.texlive_version:
            print(f"Configured TeX Live compatibility target: {config.texlive_version}")
        print(f"At arXiv, select only {config.entrypoint.as_posix()} as the primary TeX file.")
        return 0
    except ArxivPackageError as error:
        print(f"arXiv package error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
