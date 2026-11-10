#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
# SPDX-License-Identifier: MIT

"""Export immutable Word review bundles and extract returned edits without changing LaTeX."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import io
import json
import re
import shutil
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile

from credit_contributions import check as check_contributions

ROOT = Path(__file__).resolve().parents[2]
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
INCLUDE = re.compile(r"(?<!\\)\\(?:input|include|subfile)\s*\{([^{}]+)\}")
TEX_TOKENS = re.compile(
    r"(?P<literal>\\begin\s*\{(?P<environment>verbatim\*?|Verbatim\*?|lstlisting|minted)\}"
    r".*?\\end\s*\{(?P=environment)\}|\\verb\*?(?P<delimiter>[^\sA-Za-z]).*?(?P=delimiter))"
    r"|\\.|(?P<comment>%[^\n]*)", re.DOTALL)
MAX_DOCX_BYTES = 100 * 1024 * 1024


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path is outside the project: {value}")
    return path


def run_pandoc(args: list[str], text: str | None = None) -> str:
    result = subprocess.run(["pandoc", *args], input=text, text=True, capture_output=True, cwd=ROOT, timeout=120)
    if result.returncode or result.stderr.strip():
        raise ValueError("Pandoc requires attention:\n" + (result.stderr or result.stdout))
    return result.stdout


def prepare_tex(text: str) -> tuple[str, dict[str, str]]:
    """Remove comments and protect literal text from include expansion."""
    literals = {}
    prefix = "WORDLITERAL" + uuid.uuid4().hex

    def replace(match: re.Match) -> str:
        if match.group("comment") is not None:
            return ""
        if match.group("literal") is not None:
            key = f"{prefix}{len(literals)}END"
            literals[key] = match[0]
            return key
        return match[0]

    return TEX_TOKENS.sub(replace, text), literals


def restore_literals(text: str, literals: dict[str, str]) -> str:
    for key, value in literals.items():
        text = text.replace(key, value)
    return text


def uncomment(text: str) -> str:
    text, literals = prepare_tex(text)
    return restore_literals(text, literals)


def flatten(path: Path, sources: set[Path], stack: tuple[Path, ...] = ()) -> str:
    path = inside(ROOT, str(path))
    if path in stack:
        raise ValueError(f"Cyclic TeX include: {path.relative_to(ROOT)}")
    sources.add(path)
    text, literals = prepare_tex(path.read_text(encoding="utf-8"))
    if r"\begin{document}" in text:
        text = text.split(r"\begin{document}", 1)[1].rsplit(r"\end{document}", 1)[0]

    def include(match: re.Match) -> str:
        name = match[1]
        if "\\" in name:
            raise ValueError(f"Dynamic TeX include needs a Word adapter: {name}")
        if not Path(name).suffix:
            name += ".tex"
        candidates = [(ROOT / name).resolve(), (path.parent / name).resolve()]
        allowed = [candidate for candidate in candidates if candidate.is_relative_to(ROOT.resolve())]
        if not allowed:
            raise ValueError(f"Path is outside the project: {name}")
        target = next((candidate for candidate in allowed if candidate.is_file()), allowed[-1])
        return flatten(target, sources, (*stack, path))

    return restore_literals(INCLUDE.sub(include, text), literals)


def nodes(value):
    if isinstance(value, dict):
        if "t" in value:
            yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


def validate_ast(ast: dict, sources: set[Path]) -> None:
    """Fail on unsupported TeX instead of silently omitting manuscript content."""
    def visit(value):
        if isinstance(value, dict):
            # Raw LaTeX inside a parsed citation is the fallback display, not lost text.
            if value.get("t") == "Cite":
                visit(value["c"][0])
                return
            if value.get("t") in ("RawInline", "RawBlock"):
                raise ValueError(f"Unsupported Word content: {value['c']}. Add an adapter in paper/setup/word.tex.")
            if value.get("t") == "Image":
                target = value["c"][2][0]
                path = inside(ROOT, target)
                if path.suffix.lower() not in (".png", ".jpg", ".jpeg") or not path.is_file():
                    raise ValueError(f"Word figures require local PNG/JPEG exports: {target}")
                sources.add(path)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(ast)


def number_references(ast: dict) -> None:
    """Give supported cross-references visible targets in the Word review copy."""
    targets = {}
    sections = [0] * 6
    counts = {"Figure": 0, "Table": 0}
    for node in nodes(ast["blocks"]):
        kind = node.get("t")
        if kind == "Header":
            level, attr, title = node["c"]
            if "unnumbered" in attr[1]:
                continue
            sections[level - 1] += 1
            sections[level:] = [0] * (6 - level)
            targets[attr[0]] = ("Section", ".".join(map(str, sections[:level])))
        elif kind in counts:
            counts[kind] += 1
            attr, caption = node["c"][:2]
            targets[attr[0]] = (kind, str(counts[kind]))
            blocks = caption[1]
            if blocks and blocks[0]["t"] in ("Plain", "Para"):
                blocks[0]["c"][:0] = [{"t": "Str", "c": f"{kind} {counts[kind]}."}, {"t": "Space"}]
    for node in nodes(ast):
        if node.get("t") != "Link":
            continue
        attributes = dict(node["c"][0][2])
        if "reference" not in attributes:
            continue
        key = attributes["reference"]
        mode = attributes.get("reference-type", "ref")
        if key not in targets or mode not in ("ref", "ref+label"):
            raise ValueError(f"Word cross-reference needs an adapter: {mode} {{{key}}}")
        label, number = targets[key]
        node["c"][1] = [{"t": "Str", "c": f"{label} {number}" if mode == "ref+label" else number}]


def element(parent, tag: str, **attrs):
    node = parent.find(f"w:{tag}", NS)
    if node is None:
        node = ET.SubElement(parent, f"{{{W}}}{tag}")
    for key, value in attrs.items():
        node.set(f"{{{W}}}{key}", str(value))
    return node


def serialize_xml(root, original: bytes) -> bytes:
    # Preserve namespace declarations referenced only by mc:Ignorable attributes.
    namespaces = dict(item for _, item in ET.iterparse(io.BytesIO(original), events=("start-ns",)))
    for prefix, uri in namespaces.items():
        if not re.fullmatch(r"ns\d+", prefix):
            ET.register_namespace(prefix, uri)
    text = ET.tostring(root, encoding="unicode")
    opening = text.split(">", 1)[0]
    for prefix, uri in namespaces.items():
        key = "xmlns:" + prefix if prefix else "xmlns"
        if f'{key}="' not in opening:
            text = text.replace(">", f' {key}="{uri}">', 1)
    return ('<?xml version="1.0" encoding="utf-8"?>\n' + text).encode("utf-8")


def style_docx(path: Path) -> None:
    """Patch the OOXML parts only; preserve math, bookmarks, citations, and relationships."""
    with ZipFile(path) as archive:
        parts = {info.filename: archive.read(info) for info in archive.infolist()}
    styles = ET.fromstring(parts["word/styles.xml"])
    for style in styles.findall("w:style", NS):
        name = style.get(f"{{{W}}}styleId", "")
        if style.get(f"{{{W}}}type") != "paragraph":
            continue
        props, runs = element(style, "pPr"), element(style, "rPr")
        fonts = element(runs, "rFonts", ascii="Times New Roman", hAnsi="Times New Roman", cs="Times New Roman")
        for key in list(fonts.attrib):
            if "theme" in key.lower():
                del fonts.attrib[key]
        color = element(runs, "color", val="000000")
        for key in list(color.attrib):
            if key != f"{{{W}}}val":
                del color.attrib[key]
        element(runs, "sz", val=24)
        element(runs, "szCs", val=24)
        element(props, "spacing", after=120, line=276, lineRule="auto")
        element(props, "widowControl")
        if name in ("BodyText", "FirstParagraph", "Normal"):
            element(props, "ind", firstLine=0)
        if name in ("Author", "Date"):
            element(runs, "b", val=0)
        if name == "Title" or name.startswith("Heading"):
            element(runs, "sz", val=36 if name == "Title" else 28 if name == "Heading1" else 24)
            element(runs, "szCs", val=36 if name == "Title" else 28 if name == "Heading1" else 24)
            element(runs, "b")
            element(props, "keepNext")
            element(props, "spacing", before=240, after=120)
            borders = props.find("w:pBdr", NS)
            if borders is not None:
                props.remove(borders)
        if name in ("Caption", "TableCaption", "ImageCaption"):
            element(runs, "sz", val=22)
            element(props, "keepNext", val=0 if name == "ImageCaption" else 1)
    parts["word/styles.xml"] = serialize_xml(styles, parts["word/styles.xml"])
    document = ET.fromstring(parts["word/document.xml"])
    for section in document.findall(".//w:sectPr", NS):
        element(section, "pgSz", w=12240, h=15840)
        element(section, "pgMar", top=1440, bottom=1440, left=1440, right=1440)
    for table in document.findall(".//w:tbl", NS):
        props = element(table, "tblPr")
        borders = element(props, "tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            element(borders, edge, val="single", sz=4, color="D9D9D9")
        margins = element(props, "tblCellMar")
        for edge in ("top", "bottom", "left", "right"):
            element(margins, edge, w=100, type="dxa")
        for cell in table.findall(".//w:tc", NS):
            element(element(cell, "tcPr"), "vAlign", val="center")
        for row in table.findall("w:tr", NS):
            if row.find("w:trPr/w:tblHeader", NS) is not None:
                for cell in row.findall("w:tc", NS):
                    element(element(cell, "tcPr"), "shd", fill="EDEDED")
    parts["word/document.xml"] = serialize_xml(document, parts["word/document.xml"])
    settings = ET.fromstring(parts["word/settings.xml"])
    element(settings, "trackRevisions", val="true")
    parts["word/settings.xml"] = serialize_xml(settings, parts["word/settings.xml"])
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, data in parts.items():
            archive.writestr(name, data)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def markdown(docx: Path, mode: str) -> str:
    return run_pandoc([str(docx), "-f", "docx", "-t", "markdown", "--standalone", "--wrap=none", f"--track-changes={mode}", "--sandbox"])


def export_bundle(output: Path) -> None:
    check_contributions()
    if output.exists():
        raise ValueError("Choose a new output directory; review baselines are immutable")
    sources: set[Path] = set()
    body, literals = prepare_tex(flatten(ROOT / "main.tex", sources))
    body = re.sub(r"(\\bibliography\{[^{}]+\})", r"\1\n\\section*{References}\\label{word-references}", body)
    body = restore_literals(body, literals)
    preamble = "\n".join(flatten(ROOT / name, sources) for name in (
        "paper/setup/metadata.tex", "paper/setup/contributions.tex", "paper/setup/word.tex"))
    text = ("\\documentclass{article}\n" + preamble
            + "\n\\title{\\papertitle}\n\\author{\\paperauthors\\\\ \\paperaffiliations"
            + "\\\\ Correspondence: \\correspondingauthor{} (\\correspondingemail)}\n\\date{\\paperdate}\n"
            + "\\begin{document}\n" + body + "\n\\end{document}\n")
    ast = json.loads(run_pandoc(["-f", "latex", "-t", "json", "--standalone"], text))
    validate_ast(ast, sources)
    # Use the actual bibliography location in main.tex; guard against external files.
    bibliography = ast["meta"].get("bibliography", {})
    for item in nodes(bibliography):
        if item.get("t") == "Str":
            sources.add(inside(ROOT, item["c"]))
    sources.add(ROOT / "project/contributors.json")
    blocks = []
    for block in ast["blocks"]:
        blocks.append(block)
        if block["t"] == "Header" and block["c"][1][0] == "word-references":
            block["c"][1][1].append("unnumbered")
            blocks.append({"t": "Div", "c": [["refs", [], []], []]})
    ast["blocks"] = blocks
    number_references(ast)
    csl = ROOT / "tools/word/numeric.csl"
    sources.add(csl)
    with tempfile.TemporaryDirectory(prefix="word-export-") as temporary:
        stage = Path(temporary)
        docx = stage / "manuscript.docx"
        run_pandoc(["-f", "json", "-t", "docx", "--standalone", "--citeproc", "--number-sections", "--csl", str(csl),
                    "-o", str(docx)], json.dumps(ast))
        style_docx(docx)
        baseline = stage / "baseline.md"
        baseline.write_text(markdown(docx, "accept"), encoding="utf-8")
        snapshot = stage / "sources"
        hashes = {}
        for source in sorted(sources):
            name = source.relative_to(ROOT).as_posix()
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            hashes[name] = sha(source)
        write_json(stage / "manifest.json", {
            "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
            "pandoc_version": run_pandoc(["--version"]).splitlines()[0],
            "docx_sha256": sha(docx), "baseline_sha256": sha(baseline), "sources": hashes,
        })
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(stage, output)
    print(f"Word review copy: {output / 'manuscript.docx'}")
    print("Keep the complete bundle locally. Send only a copy of manuscript.docx; return edits with Track Changes enabled.")


def xml_text(node) -> str:
    return "".join(part.text or "" for part in node.iter()
                   if part.tag in (f"{{{W}}}t", f"{{{W}}}delText"))


def review_annotations(docx: Path) -> list[dict]:
    """Retain all revision/comment records, including changes Pandoc may not interpret."""
    records = []
    with ZipFile(docx) as archive:
        if len(archive.infolist()) > 10000 or sum(i.file_size for i in archive.infolist()) > MAX_DOCX_BYTES:
            raise ValueError("DOCX exceeds the review size limit")
        for info in archive.infolist():
            if not info.filename.startswith("word/") or not info.filename.endswith(".xml"):
                continue
            root = ET.fromstring(archive.read(info))
            parents = {child: parent for parent in root.iter() for child in parent}
            for node in root.iter():
                tag = node.tag.removeprefix(f"{{{W}}}")
                if tag not in ("ins", "del", "moveFrom", "moveTo", "comment", "commentRangeStart", "commentReference",
                               "cellIns", "cellDel", "cellMerge") and not tag.endswith("Change"):
                    continue
                context = node
                while context in parents and context.tag != f"{{{W}}}p":
                    context = parents[context]
                records.append({
                    "part": info.filename, "kind": tag,
                    "attributes": {key.removeprefix(f"{{{W}}}"): val for key, val in node.attrib.items()},
                    "text": xml_text(node), "paragraph": xml_text(context) if context.tag == f"{{{W}}}p" else "",
                    "xml": ET.tostring(node, encoding="unicode"),
                })
    return records


def import_review(reviewed: Path, baseline: Path, output: Path) -> None:
    if output.exists():
        raise ValueError("Choose a new output directory; previous review extractions are preserved")
    manifest = json.loads((baseline / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported baseline manifest")
    for name, key in (("manuscript.docx", "docx_sha256"), ("baseline.md", "baseline_sha256")):
        if sha(baseline / name) != manifest[key]:
            raise ValueError(f"Baseline {name} was modified; use the original export bundle")
    drift = []
    for name, expected in manifest["sources"].items():
        snapshot = inside(baseline / "sources", name)
        if sha(snapshot) != expected:
            raise ValueError(f"Baseline source snapshot was modified: {name}")
        current = inside(ROOT, name)
        if not current.is_file() or sha(current) != expected:
            drift.append(name)
    annotations = review_annotations(reviewed)
    def part_hashes(path):
        with ZipFile(path) as archive:
            return {name: hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist()}
    before_parts, after_parts = part_hashes(baseline / "manuscript.docx"), part_hashes(reviewed)
    changed_parts = sorted(name for name in before_parts.keys() | after_parts.keys()
                           if before_parts.get(name) != after_parts.get(name))
    accepted, rejected, marked = (markdown(reviewed, mode) for mode in ("accept", "reject", "all"))
    original = (baseline / "baseline.md").read_text(encoding="utf-8")
    version = run_pandoc(["--version"]).splitlines()[0]
    with tempfile.TemporaryDirectory(prefix="word-review-") as temporary:
        stage = Path(temporary)
        shutil.copy2(reviewed, stage / "reviewed.docx")
        for name, content in (("accepted.md", accepted), ("rejected.md", rejected), ("marked.md", marked)):
            (stage / name).write_text(content, encoding="utf-8")
        for name, content in (("changes.diff", accepted), ("untracked.diff", rejected)):
            diff = difflib.unified_diff(original.splitlines(True), content.splitlines(True),
                                        fromfile="exported baseline", tofile=name.removesuffix(".diff"))
            (stage / name).write_text("".join(diff), encoding="utf-8")
        write_json(stage / "annotations.json", annotations)
        write_json(stage / "review.json", {
            "schema_version": 1, "baseline": str(baseline), "reviewed_sha256": sha(reviewed),
            "source_drift": drift, "pandoc_version": version,
            "baseline_pandoc_version": manifest["pandoc_version"],
            "conversion_version_changed": version != manifest["pandoc_version"],
            "untracked_or_structural_differences": rejected != original,
            "annotation_records": len(annotations),
            "changed_docx_parts": changed_parts,
            "media_changes": [name for name in changed_parts if name.startswith("word/media/")],
            "requires_manual_reconciliation": True,
        })
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(stage, output)
    print(f"Review extracted to {output}; LaTeX sources were not changed.")
    print(f"Source files changed since export: {len(drift)}. Reconcile using tools/skills/paper-word-review/SKILL.md.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export")
    review = sub.add_parser("import")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    export.add_argument("--output", type=Path, default=ROOT / "output/word" / stamp)
    review.add_argument("--reviewed", type=Path, required=True)
    review.add_argument("--baseline", type=Path, required=True)
    review.add_argument("--output", type=Path, default=ROOT / "output/word-reviews" / stamp)
    args = parser.parse_args()
    try:
        if not shutil.which("pandoc"):
            raise ValueError("Install Pandoc 3.1 or newer for the optional Word workflow")
        version = re.search(r"pandoc (\d+)\.(\d+)", run_pandoc(["--version"]))
        if not version or tuple(map(int, version.groups())) < (3, 1):
            raise ValueError("Pandoc 3.1 or newer is required")
        if args.command == "export":
            export_bundle(args.output.resolve())
        else:
            import_review(args.reviewed.resolve(), args.baseline.resolve(), args.output.resolve())
    except (ValueError, OSError, KeyError, ET.ParseError, BadZipFile, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"ERROR: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
