#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

"""Shared, standard-library helpers for the source-first reference workflow."""

from __future__ import annotations

import html
import io
import re
import tarfile
import unicodedata
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_DIR = PROJECT_ROOT / "research" / "literature"
BIB_PATH = PROJECT_ROOT / "references.bib"
INVENTORY_PATH = PROJECT_ROOT / "project" / "notes" / "06_reference_inventory.md"
USER_AGENT = "scientific-paper-template/1.0 (source-first reference workflow)"
PMC_S3_BUCKET = "https://pmc-oa-opendata.s3.amazonaws.com"
STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "for",
    "from",
    "in",
    "of",
    "on",
    "the",
    "to",
    "with",
}


@dataclass
class Citation:
    entry_type: str = "article"
    key: str = ""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: str = ""
    journal: str = ""
    volume: str = ""
    number: str = ""
    pages: str = ""
    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    url: str = ""
    abstract: str = ""
    publisher: str = ""
    raw_bib: str = ""


def http_get(url: str, accept: str | None = None, timeout: int = 30) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def clean(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" .;\n\t")


def ascii_token(value: str) -> str:
    value = re.sub(r"\\[A-Za-z]+\s*\{([^{}]*)\}", r"\1", value)
    value = value.replace("{", "").replace("}", "")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^A-Za-z0-9]", "", value)


def derive_key(citation: Citation) -> str:
    author = citation.authors[0] if citation.authors else "unknown"
    if "," in author:
        surname = author.split(",", 1)[0]
    else:
        surname = author.split()[0] if author.split() else "unknown"
    surname = ascii_token(surname).lower() or "unknown"
    year_match = re.search(r"(?:19|20)\d{2}", citation.year)
    year = year_match.group(0) if year_match else "0000"
    title_words = [ascii_token(word).lower() for word in re.findall(r"[A-Za-z0-9'{}\\-]+", citation.title)]
    descriptor = next((word for word in title_words if word and word not in STOPWORDS), "work")
    return f"{surname}{year}{descriptor}"


def medline_fields(text: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    current = ""
    for raw_line in text.splitlines():
        match = re.match(r"^([A-Z0-9]{2,4})\s*-\s*(.*)$", raw_line)
        if match:
            current = match.group(1)
            fields.setdefault(current, []).append(match.group(2).strip())
        elif current and raw_line.startswith("      "):
            fields[current][-1] = f"{fields[current][-1]} {raw_line.strip()}"
    return fields


def parse_nbib(text: str) -> Citation:
    fields = medline_fields(text)
    aids = fields.get("AID", []) + fields.get("LID", [])
    doi = next((re.sub(r"\s*\[doi\]\s*$", "", item) for item in aids if "[doi]" in item.lower()), "")
    pmcid = next((item for item in fields.get("PMC", []) if item.upper().startswith("PMC")), "")
    if not pmcid:
        pmcid = next((item for item in fields.get("AID", []) if item.upper().startswith("PMC")), "")
    date = next(iter(fields.get("DP", [])), "")
    year_match = re.search(r"(?:19|20)\d{2}", date)
    authors = fields.get("FAU") or fields.get("AU") or []
    return Citation(
        entry_type="article",
        title=clean(" ".join(fields.get("TI", []))),
        authors=[clean(author) for author in authors],
        year=year_match.group(0) if year_match else "",
        journal=clean(next(iter(fields.get("JT", []) or fields.get("TA", [])), "")),
        volume=clean(next(iter(fields.get("VI", [])), "")),
        number=clean(next(iter(fields.get("IP", [])), "")),
        pages=clean(next(iter(fields.get("PG", [])), "")),
        doi=clean(doi),
        pmid=clean(next(iter(fields.get("PMID", [])), "")),
        pmcid=clean(pmcid),
        abstract=clean(" ".join(fields.get("AB", []))),
    )


def ris_fields(text: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for raw_line in text.splitlines():
        match = re.match(r"^([A-Z0-9]{2})  - (.*)$", raw_line)
        if match:
            fields.setdefault(match.group(1), []).append(match.group(2).strip())
    return fields


def parse_ris(text: str) -> Citation:
    fields = ris_fields(text)
    year_source = next(iter(fields.get("PY", []) or fields.get("Y1", [])), "")
    year_match = re.search(r"(?:19|20)\d{2}", year_source)
    start = next(iter(fields.get("SP", [])), "")
    end = next(iter(fields.get("EP", [])), "")
    pages = f"{start}--{end}" if start and end else start
    return Citation(
        entry_type="article",
        title=clean(next(iter(fields.get("TI", []) or fields.get("T1", [])), "")),
        authors=[clean(author) for author in fields.get("AU", [])],
        year=year_match.group(0) if year_match else "",
        journal=clean(next(iter(fields.get("JF", []) or fields.get("JO", []) or fields.get("T2", [])), "")),
        volume=clean(next(iter(fields.get("VL", [])), "")),
        number=clean(next(iter(fields.get("IS", [])), "")),
        pages=clean(pages),
        doi=clean(next(iter(fields.get("DO", [])), "")),
        url=clean(next(iter(fields.get("UR", [])), "")),
        abstract=clean(" ".join(fields.get("AB", []))),
    )


def split_bib_entries(text: str) -> list[str]:
    entries: list[str] = []
    index = 0
    while True:
        match = re.search(r"@[A-Za-z]+\s*[({]", text[index:])
        if not match:
            break
        start = index + match.start()
        opener_index = index + match.end() - 1
        opener = text[opener_index]
        closer = "}" if opener == "{" else ")"
        depth = 0
        quoted = False
        escaped = False
        end = len(text)
        for position in range(opener_index, len(text)):
            character = text[position]
            if escaped:
                escaped = False
                continue
            if character == "\\":
                escaped = True
                continue
            if character == '"':
                quoted = not quoted
            if quoted:
                continue
            if character == opener:
                depth += 1
            elif character == closer:
                depth -= 1
                if depth == 0:
                    end = position + 1
                    break
        entries.append(text[start:end].strip())
        index = end
    return entries


def bib_field(entry: str, name: str) -> str:
    match = re.search(rf"(?ims)(?:^|,)\s*{re.escape(name)}\s*=\s*", entry)
    if not match:
        return ""
    position = match.end()
    if position >= len(entry):
        return ""
    opener = entry[position]
    if opener in "{\"":
        closer = "}" if opener == "{" else '"'
        depth = 0
        escaped = False
        value_start = position + 1
        for cursor in range(value_start, len(entry)):
            character = entry[cursor]
            if escaped:
                escaped = False
                continue
            if character == "\\":
                escaped = True
                continue
            if opener == "{" and character == "{":
                depth += 1
            elif character == closer:
                if depth == 0:
                    return entry[value_start:cursor].strip()
                depth -= 1
    return clean(entry[position:].split(",", 1)[0])


def parse_bib(text: str) -> Citation:
    entries = split_bib_entries(text)
    if not entries:
        raise ValueError("No BibTeX entry found")
    entry = entries[0]
    head = re.match(r"@([A-Za-z]+)\s*[({]\s*([^,]+),", entry)
    if not head:
        raise ValueError("Could not parse the BibTeX entry header")
    author_value = bib_field(entry, "author")
    return Citation(
        entry_type=head.group(1).lower(),
        key=clean(head.group(2)),
        title=clean(bib_field(entry, "title")),
        authors=[clean(author) for author in re.split(r"\s+and\s+", author_value) if clean(author)],
        year=clean(bib_field(entry, "year")),
        journal=clean(bib_field(entry, "journal") or bib_field(entry, "booktitle")),
        volume=clean(bib_field(entry, "volume")),
        number=clean(bib_field(entry, "number")),
        pages=clean(bib_field(entry, "pages")),
        doi=clean(bib_field(entry, "doi")),
        pmid=clean(bib_field(entry, "pmid")),
        pmcid=clean(bib_field(entry, "pmcid")),
        url=clean(bib_field(entry, "url")),
        abstract=clean(bib_field(entry, "abstract")),
        publisher=clean(bib_field(entry, "publisher")),
        raw_bib=entry,
    )


def parse_citation(path: Path) -> Citation:
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()
    if suffix == ".nbib":
        return parse_nbib(text)
    if suffix == ".ris":
        return parse_ris(text)
    if suffix == ".bib":
        return parse_bib(text)
    raise ValueError(f"Unsupported citation format: {path.name}")


def choose_citation_file(folder: Path) -> Path | None:
    for name in ("citation.nbib", "citation.ris", "citation.bib"):
        candidate = folder / name
        if candidate.exists():
            return candidate
    return None


def brace(value: str) -> str:
    value = value.replace("\n", " ").strip()
    for character in ("&", "%", "_", "#"):
        value = re.sub(rf"(?<!\\){re.escape(character)}", rf"\\{character}", value)
    return value


def markdown_display(value: str) -> str:
    """Remove BibTeX case-protection braces from generated Markdown text."""
    return value.replace("{", "").replace("}", "")


def citation_to_bib(citation: Citation, key: str) -> str:
    if citation.raw_bib:
        return re.sub(
            r"(?is)^(@[A-Za-z]+\s*[({]\s*)[^,]+,",
            rf"\g<1>{key},",
            citation.raw_bib.strip(),
            count=1,
        )
    fields: list[tuple[str, str]] = []
    if citation.authors:
        fields.append(("author", " and ".join(citation.authors)))
    for name, value in (
        ("title", citation.title),
        ("journal", citation.journal),
        ("year", citation.year),
        ("volume", citation.volume),
        ("number", citation.number),
        ("pages", citation.pages),
        ("doi", citation.doi),
        ("pmcid", citation.pmcid),
        ("pmid", citation.pmid),
        ("publisher", citation.publisher),
        ("url", citation.url),
    ):
        if value:
            fields.append((name, value))
    if not citation.title or not citation.year:
        raise ValueError(f"Citation {key} is missing a title or year")
    body = ",\n".join(f"  {name} = {{{brace(value)}}}" for name, value in fields)
    return f"@{citation.entry_type or 'article'}{{{key},\n{body}\n}}"


def abstract_markdown(citation: Citation, key: str, source_name: str) -> str:
    title = markdown_display(citation.title or key)
    authors = "; ".join(citation.authors) if citation.authors else "Not available in citation export"
    abstract = citation.abstract or "Abstract not available in the citation export."
    identifiers = []
    if citation.doi:
        identifiers.append(f"DOI: `{citation.doi}`")
    if citation.pmid:
        identifiers.append(f"PMID: `{citation.pmid}`")
    if citation.pmcid:
        identifiers.append(f"PMCID: `{citation.pmcid}`")
    identifier_text = "; ".join(identifiers) or "No persistent identifier found in citation export."
    return (
        f"# {title}\n\n"
        f"- Citation key: `{key}`\n"
        f"- Authors: {authors}\n"
        f"- Venue: {citation.journal or 'Not available'}\n"
        f"- Year: {citation.year or 'Not available'}\n"
        f"- Identifiers: {identifier_text}\n"
        f"- Metadata source: `{source_name}`\n\n"
        "## Abstract\n\n"
        f"{abstract}\n"
    )


def write_abstract(folder: Path, citation: Citation, key: str, source_name: str) -> None:
    (folder / "abstract.md").write_text(
        abstract_markdown(citation, key, source_name), encoding="utf-8"
    )


def claims_markdown(citation: Citation, key: str) -> str:
    title = markdown_display(citation.title or key)
    return (
        "<!--\n\n"
        "This source file is part of a scientific paper repository based on the Scientific Paper Template\n\n"
        "SPDX-" "FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)\n\n"
        "SPDX-" "License-Identifier: MIT\n\n"
        "-->\n\n"
        f"# Claim Notes for {title}\n\n"
        f"- Citation key: `{key}`\n\n"
        "## Verified manuscript support\n\n"
        "- TODO: Record the exact manuscript claim and the page, section, table, or figure that supports it.\n\n"
        "## Scope and limitations\n\n"
        "- TODO: Record the population or system, design, denominator, setting, and limitations relevant to reuse of this source.\n"
    )


def ensure_claims(folder: Path, citation: Citation, key: str) -> None:
    path = folder / "claims.md"
    if not path.exists():
        path.write_text(claims_markdown(citation, key), encoding="utf-8")


def validate_pdf(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 100:
        return False
    with path.open("rb") as handle:
        return handle.read(5) == b"%PDF-"


def pmc_open_access_link(pmcid: str, timeout: int = 30) -> tuple[str, str]:
    normalized = pmcid.upper()
    if not normalized.startswith("PMC"):
        normalized = f"PMC{normalized}"
    xml_bytes = http_get(
        f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={normalized}",
        timeout=timeout,
    )
    root = ET.fromstring(xml_bytes)
    links = root.findall(".//link")
    for preferred_format in ("pdf", "tgz"):
        for link in links:
            if link.attrib.get("format") != preferred_format or not link.attrib.get("href"):
                continue
            href = link.attrib["href"]
            if href.startswith("ftp://"):
                href = "https://" + href[len("ftp://") :]
            return preferred_format, href
    return "", ""


def pmc_pdf_url(pmcid: str, timeout: int = 30) -> str:
    """Return a direct PDF URL when PMC exposes one; archives require download_pmc_pdf."""
    format_name, url = pmc_open_access_link(pmcid, timeout=timeout)
    return url if format_name == "pdf" else ""


def pmc_s3_pdf_url(pmcid: str, timeout: int = 30) -> str:
    """Find the current article PDF in PMC's unsigned open-data S3 bucket."""
    normalized = pmcid.upper()
    if not normalized.startswith("PMC"):
        normalized = f"PMC{normalized}"
    query = urllib.parse.urlencode(
        {"list-type": "2", "prefix": f"{normalized}.", "delimiter": "/"}
    )
    root = ET.fromstring(http_get(f"{PMC_S3_BUCKET}/?{query}", timeout=timeout))
    prefixes = [element.text for element in root.findall(".//{*}CommonPrefixes/{*}Prefix") if element.text]
    if not prefixes:
        return ""
    prefix = sorted(prefixes)[-1]
    detail_query = urllib.parse.urlencode({"list-type": "2", "prefix": prefix})
    detail_root = ET.fromstring(http_get(f"{PMC_S3_BUCKET}/?{detail_query}", timeout=timeout))
    keys = [element.text for element in detail_root.findall(".//{*}Contents/{*}Key") if element.text]
    pdf_keys = [key for key in keys if key.lower().endswith(".pdf")]
    if not pdf_keys:
        return ""
    return f"{PMC_S3_BUCKET}/{urllib.parse.quote(sorted(pdf_keys)[-1], safe='/')}"


def download_pdf(url: str, destination: Path, timeout: int = 60) -> None:
    content = http_get(url, accept="application/pdf", timeout=timeout)
    destination.write_bytes(content)
    if not validate_pdf(destination):
        destination.unlink(missing_ok=True)
        raise ValueError(f"Downloaded content from {url} is not a valid PDF")


def extract_pdf_from_oa_archive(content: bytes) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as archive:
        candidates = [member for member in archive.getmembers() if member.isfile() and member.name.lower().endswith(".pdf")]
        if not candidates:
            raise ValueError("PMC open-access archive contains no PDF")
        member = max(candidates, key=lambda item: item.size)
        extracted = archive.extractfile(member)
        if extracted is None:
            raise ValueError("Could not read the PDF from the PMC open-access archive")
        pdf_bytes = extracted.read()
    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("PMC archive member is not a valid PDF")
    return pdf_bytes


def download_pmc_pdf(pmcid: str, destination: Path, timeout: int = 60) -> None:
    s3_url = pmc_s3_pdf_url(pmcid, timeout=timeout)
    if s3_url:
        download_pdf(s3_url, destination, timeout=timeout)
        return
    format_name, url = pmc_open_access_link(pmcid, timeout=timeout)
    if not url:
        raise ValueError(f"No PMC open-access package is available for {pmcid}")
    if format_name == "pdf":
        download_pdf(url, destination, timeout=timeout)
        return
    try:
        content = http_get(url, timeout=timeout)
    except urllib.error.HTTPError as error:
        if error.code != 404 or "/pub/pmc/oa_package/" not in url:
            raise
        transition_url = url.replace("/pub/pmc/oa_package/", "/pub/pmc/deprecated/oa_package/")
        content = http_get(transition_url, timeout=timeout)
    destination.write_bytes(extract_pdf_from_oa_archive(content))
    if not validate_pdf(destination):
        destination.unlink(missing_ok=True)
        raise ValueError(f"PMC open-access package for {pmcid} did not yield a valid PDF")


def all_reference_folders() -> list[Path]:
    if not REFERENCES_DIR.exists():
        return []
    return sorted(folder for folder in REFERENCES_DIR.iterdir() if folder.is_dir() and not folder.name.startswith("."))


def generated_bibliography() -> tuple[str, list[str]]:
    entries: list[str] = []
    problems: list[str] = []
    dois: dict[str, str] = {}
    for folder in all_reference_folders():
        citation_file = choose_citation_file(folder)
        if not citation_file:
            problems.append(f"{folder.name}: missing citation.bib, citation.nbib, or citation.ris")
            continue
        try:
            citation = parse_citation(citation_file)
            entry = citation_to_bib(citation, folder.name)
        except (OSError, ValueError) as error:
            problems.append(f"{folder.name}: {error}")
            continue
        if citation.doi:
            normalized_doi = citation.doi.lower().removeprefix("https://doi.org/")
            if normalized_doi in dois:
                problems.append(f"{folder.name}: duplicate DOI also used by {dois[normalized_doi]}")
            else:
                dois[normalized_doi] = folder.name
        entries.append(entry)
    header = (
        "% Generated by tools/scripts/regenerate_bib_from_references.py.\n"
        "% Add and correct metadata in research/literature/<citation-key>/citation.* instead.\n"
    )
    body = "\n\n".join(entries)
    if not body:
        return header, problems
    return f"{header}\n{body}\n", problems


def bib_keys(text: str) -> set[str]:
    return {match.group(1).strip() for match in re.finditer(r"@[A-Za-z]+\s*[({]\s*([^,]+),", text)}
