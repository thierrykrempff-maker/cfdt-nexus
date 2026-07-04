#!/usr/bin/env python
"""
Bible Accords Sarralbe V1.

Local-only pipeline for private agreements:
- scan
- extract
- index
- search
- test
- missing

No document is copied into Git. Outputs are written under local-index/agreements/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
LOCAL_ROOT = ROOT / "local-index" / "agreements"
STATE_DIR = LOCAL_ROOT / "state"
TEXT_DIR = LOCAL_ROOT / "text"
INDEX_DIR = LOCAL_ROOT / "index"
REPORT_DIR = LOCAL_ROOT / "reports"
SEARCH_DIR = LOCAL_ROOT / "search"
TEST_DIR = LOCAL_ROOT / "tests"

MIN_TEXT_CHARS = 800
MIN_PAGE_TEXT_CHARS = 20
MAX_CHUNK_CHARS = 2400
CHUNK_OVERLAP_CHARS = 240

DOCUMENT_TYPES = [
    ("avenant", [r"\bavenant\b", r"\bmodification\b"]),
    ("règlement intérieur", [r"reglement interieur", r"règlement intérieur"]),
    ("protocole", [r"\bprotocole\b", r"\bpap\b", r"vote electronique", r"vote électronique"]),
    ("décision unilatérale", [r"decision unilaterale", r"décision unilatérale", r"\bdue\b"]),
    ("accord entreprise", [r"\baccord\b"]),
    ("note collective", [r"\bnote\b", r"information collective"]),
]

TOPIC_RULES = [
    ("rémunération", [r"remuneration", r"rémunération", r"salaire", r"salaires"]),
    ("primes", [r"\bprime\b", r"\bprimes\b", r"\bppv\b", r"partage de la valeur"]),
    ("intéressement", [r"interessement", r"intéressement"]),
    ("participation", [r"participation"]),
    ("épargne salariale", [r"epargne", r"épargne", r"\bpereco\b", r"\bpee\b", r"\bcet\b"]),
    ("temps de travail", [r"temps de travail", r"duree du travail", r"durée du travail", r"horaire", r"horaires"]),
    ("5x8", [r"\b5x8\b", r"equipes postees", r"équipes postées"]),
    ("travail posté", [r"travail poste", r"travail posté", r"\bposte\b", r"\bpostes\b"]),
    ("travail de nuit", [r"travail de nuit", r"\bnuit\b"]),
    ("repos", [r"\brepos\b", r"repos quotidien", r"repos hebdomadaire"]),
    ("congés", [r"conges", r"congés", r"conge", r"congé"]),
    ("astreinte", [r"astreinte"]),
    ("classification", [r"classification", r"coefficient", r"classement"]),
    ("emploi", [r"\bemploi\b", r"emplois", r"effectif", r"effectifs"]),
    ("compétences", [r"competence", r"compétence", r"\bgepp\b", r"\bgpec\b"]),
    ("formation", [r"formation"]),
    ("égalité professionnelle", [r"egalite professionnelle", r"égalité professionnelle"]),
    ("télétravail", [r"teletravail", r"télétravail"]),
    ("santé", [r"sante", r"santé", r"maladie", r"medical", r"médical"]),
    ("sécurité", [r"securite", r"sécurité", r"prevention", r"prévention", r"risque"]),
    ("conditions de travail", [r"conditions de travail", r"rps", r"psychosocial"]),
    ("fin de carrière", [r"fin de carriere", r"fin de carrière", r"retraite"]),
    ("handicap", [r"handicap"]),
    ("droit syndical", [r"droit syndical", r"delegue syndical", r"délégué syndical", r"section syndicale"]),
    ("CSE", [r"\bcse\b", r"comite social", r"comité social"]),
    ("dialogue social", [r"dialogue social", r"negociation", r"négociation"]),
    ("disciplinaire", [r"disciplinaire", r"sanction", r"mise a pied", r"mise à pied"]),
]

BUSINESS_TESTS = [
    "repos entre deux postes",
    "astreinte",
    "prime de nuit",
    "majoration dimanche",
    "durée du travail",
    "heures supplémentaires",
    "congé ancienneté",
    "départ retraite",
    "classification",
    "procédure disciplinaire",
    "sanction",
    "sécurité",
    "droit syndical",
]

STOPWORDS = {
    "a",
    "au",
    "aux",
    "avec",
    "ce",
    "ces",
    "dans",
    "de",
    "des",
    "du",
    "en",
    "et",
    "la",
    "le",
    "les",
    "l",
    "un",
    "une",
    "pour",
    "par",
    "sur",
    "ou",
    "d",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dirs() -> None:
    for directory in [STATE_DIR, TEXT_DIR, INDEX_DIR, REPORT_DIR, SEARCH_DIR, TEST_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return without_marks.replace("æ", "ae").replace("œ", "oe").lower()


def tokenize(value: str) -> list[str]:
    tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]{2,}", normalize(value))
    return [token for token in tokens if token not in STOPWORDS]


def source_path_from_args(args: argparse.Namespace) -> Path:
    source = args.source or os.environ.get("CFDT_NEXUS_CORPUS_PATH")
    if not source:
        raise SystemExit(
            "Source corpus manquante. Utiliser --source ou la variable CFDT_NEXUS_CORPUS_PATH."
        )
    path = Path(source).expanduser()
    if not path.exists() or not path.is_dir():
        raise SystemExit("Le chemin source n'est pas accessible ou n'est pas un dossier.")
    return path


def relative_to_source(path: Path, source: Path) -> str:
    return str(path.relative_to(source)).replace("\\", "/")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def doc_id_for_sha(sha256: str) -> str:
    return f"doc_{sha256[:16]}"


def match_rules(text: str, rules: list[tuple[str, list[str]]], sort_by_score: bool = True) -> list[str]:
    haystack = normalize(text)
    matches = []
    for order, (label, patterns) in enumerate(rules):
        count = 0
        first_index = None
        for pattern in patterns:
            for match in re.finditer(pattern, haystack, flags=re.IGNORECASE):
                count += 1
                first_index = match.start() if first_index is None else min(first_index, match.start())
        if count:
            matches.append({"label": label, "count": count, "first_index": first_index or 0, "order": order})
    if sort_by_score:
        matches.sort(key=lambda item: (-item["count"], item["first_index"], item["order"]))
    return [item["label"] for item in matches]


def classify_document(relative_path: str, text_sample: str = "") -> dict[str, Any]:
    combined = f"{relative_path}\n{text_sample[:6000]}"
    doc_types = match_rules(combined, DOCUMENT_TYPES, sort_by_score=False)
    topics = match_rules(combined, TOPIC_RULES)

    if len(doc_types) == 1:
        document_type = doc_types[0]
        classification_note = "Classement V1 déterministe à valider humainement."
    elif len(doc_types) > 1:
        document_type = doc_types[0]
        classification_note = "Plusieurs types possibles détectés. Type prioritaire retenu, validation humaine nécessaire."
    else:
        document_type = "autre document collectif"
        classification_note = "Aucun type spécifique détecté avec confiance."

    primary_topic = topics[0] if topics else "autres"
    secondary_topics = topics[1:] if len(topics) > 1 else []

    return {
        "document_type": document_type,
        "primary_topic": primary_topic,
        "secondary_topics": secondary_topics,
        "classification_note": classification_note,
    }


def inventory_paths() -> tuple[Path, Path]:
    return STATE_DIR / "inventory.private.json", STATE_DIR / "previous-inventory.private.json"


def scan_corpus(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    source = source_path_from_args(args)
    current_path, previous_path = inventory_paths()
    previous_inventory = load_json(current_path, {"documents": []})
    previous_by_rel = {item["relative_path"]: item for item in previous_inventory.get("documents", [])}
    current_docs = []
    seen_sha = defaultdict(list)
    checked_at = now_iso()

    extensions = {".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt"}
    for file_path in sorted(source.rglob("*")):
        if not file_path.is_file():
            continue
        extension = file_path.suffix.lower() or "[sans extension]"
        if extension not in extensions:
            continue

        relative_path = relative_to_source(file_path, source)
        sha256 = file_sha256(file_path)
        document_id = doc_id_for_sha(sha256)
        previous = previous_by_rel.get(relative_path)
        if previous is None:
            change_status = "NEW"
        elif previous.get("sha256") != sha256:
            change_status = "MODIFIED"
        else:
            change_status = "UNCHANGED"

        classification = classify_document(relative_path)
        item = {
            "document_id": document_id,
            "filename": file_path.name,
            "extension": extension,
            "relative_path": relative_path,
            "file_size": file_path.stat().st_size,
            "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat(),
            "sha256": sha256,
            "change_status": change_status,
            "extraction_status": previous.get("extraction_status", "PENDING") if previous else "PENDING",
            "ocr_required": previous.get("ocr_required", False) if previous else False,
            "document_type": classification["document_type"],
            "primary_topic": classification["primary_topic"],
            "secondary_topics": classification["secondary_topics"],
            "classification_note": classification["classification_note"],
            "confidentiality_level": "private",
            "indexed_at": previous.get("indexed_at") if previous else None,
            "last_checked_at": checked_at,
        }
        current_docs.append(item)
        seen_sha[sha256].append(item)

    for items in seen_sha.values():
        if len(items) > 1:
            for item in items:
                item["change_status"] = "DUPLICATE_EXACT"

    current_rel = {item["relative_path"] for item in current_docs}
    for previous in previous_inventory.get("documents", []):
        if previous.get("relative_path") not in current_rel:
            missing = dict(previous)
            missing["change_status"] = "MISSING"
            missing["last_checked_at"] = checked_at
            current_docs.append(missing)

    if current_path.exists():
        previous_path.write_text(current_path.read_text(encoding="utf-8"), encoding="utf-8")

    summary = build_quality_summary(current_docs)
    inventory = {
        "generated_at": checked_at,
        "source_path_stored": False,
        "source_label": "private-local-corpus",
        "documents": current_docs,
        "summary": summary,
        "security_notice": "Private local inventory. Do not commit.",
    }
    write_json(current_path, inventory)
    write_json(REPORT_DIR / f"scan-summary-{safe_stamp()}.private.json", summary)
    print_scan_summary(summary)
    return inventory


def safe_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def build_quality_summary(documents: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_documents": len([d for d in documents if d.get("change_status") != "MISSING"]),
        "new": count_status(documents, "NEW"),
        "modified": count_status(documents, "MODIFIED"),
        "unchanged": count_status(documents, "UNCHANGED"),
        "missing": count_status(documents, "MISSING"),
        "duplicate_exact": count_status(documents, "DUPLICATE_EXACT"),
        "extraction_ok": count_extraction(documents, "EXTRACTION_OK"),
        "extraction_to_verify": count_extraction(documents, "EXTRACTION_A_VERIFIER"),
        "ocr_required": sum(1 for d in documents if d.get("ocr_required")),
        "errors": count_extraction(documents, "ERROR"),
        "classified": sum(1 for d in documents if d.get("document_type") not in {"à classer"}),
        "to_classify_manually": sum(1 for d in documents if d.get("document_type") == "à classer"),
        "by_extension": Counter(d.get("extension") for d in documents if d.get("change_status") != "MISSING"),
        "by_topic": Counter(d.get("primary_topic") for d in documents if d.get("change_status") != "MISSING"),
    }


def count_status(documents: list[dict[str, Any]], status: str) -> int:
    return sum(1 for item in documents if item.get("change_status") == status)


def count_extraction(documents: list[dict[str, Any]], status: str) -> int:
    return sum(1 for item in documents if item.get("extraction_status") == status)


def print_scan_summary(summary: dict[str, Any]) -> None:
    print(f"Documents détectés: {summary['total_documents']}")
    print(f"NEW: {summary['new']} | MODIFIED: {summary['modified']} | UNCHANGED: {summary['unchanged']} | MISSING: {summary['missing']}")
    print(f"DUPLICATE_EXACT: {summary['duplicate_exact']}")


def extract_pdf(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(str(path)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append({"page": index, "text": text})
    except Exception as error:  # pragma: no cover - local fallback
        errors.append(f"pdfplumber: {error}")
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(path))
            pages = []
            for index, page in enumerate(reader.pages, start=1):
                pages.append({"page": index, "text": page.extract_text() or ""})
        except Exception as fallback_error:
            errors.append(f"pypdf: {fallback_error}")

    diagnostics = extraction_diagnostics(pages, errors, ocr_possible=True)
    return pages, diagnostics


def extract_docx(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        import docx  # type: ignore

        document = docx.Document(str(path))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
        pages = [{"page": None, "text": text}]
        return pages, extraction_diagnostics(pages, [], ocr_possible=False)
    except Exception as error:
        return [], extraction_diagnostics([], [str(error)], ocr_possible=False)


def extract_txt(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    for encoding in ["utf-8", "cp1252", "latin-1"]:
        try:
            pages = [{"page": None, "text": path.read_text(encoding=encoding)}]
            return pages, extraction_diagnostics(pages, [], ocr_possible=False)
        except UnicodeDecodeError:
            continue
    return [], extraction_diagnostics([], ["encoding unsupported"], ocr_possible=False)


def extraction_diagnostics(pages: list[dict[str, Any]], errors: list[str], ocr_possible: bool) -> dict[str, Any]:
    text = "\n".join(page.get("text", "") for page in pages)
    chars = len(text.strip())
    empty_pages = sum(1 for page in pages if len(page.get("text", "").strip()) < MIN_PAGE_TEXT_CHARS)
    weird = len(re.findall(r"[�□■]", text))
    weird_ratio = weird / max(chars, 1)

    if errors and not chars:
        status = "ERROR"
        ocr_required = False
    elif chars < MIN_TEXT_CHARS and ocr_possible:
        status = "OCR_REQUIRED"
        ocr_required = True
    elif chars < MIN_TEXT_CHARS:
        status = "EXTRACTION_A_VERIFIER"
        ocr_required = False
    elif weird_ratio > 0.02 or empty_pages > max(2, len(pages) // 2):
        status = "EXTRACTION_A_VERIFIER"
        ocr_required = False
    else:
        status = "EXTRACTION_OK"
        ocr_required = False

    return {
        "status": status,
        "ocr_required": ocr_required,
        "char_count": chars,
        "page_count": len(pages),
        "empty_or_low_text_pages": empty_pages,
        "weird_char_ratio": weird_ratio,
        "errors": errors,
    }


def extract_documents(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    source = source_path_from_args(args)
    inventory_path, _ = inventory_paths()
    inventory = load_json(inventory_path, None)
    if inventory is None:
        inventory = scan_corpus(args)

    report_rows = []
    changed = 0
    for doc in inventory["documents"]:
        if doc.get("change_status") == "MISSING":
            continue
        if doc.get("extension") not in {".pdf", ".docx", ".txt"}:
            doc["extraction_status"] = "UNSUPPORTED"
            report_rows.append(report_doc(doc, "UNSUPPORTED", 0, 0))
            continue

        output_path = text_output_path(doc["document_id"])
        must_extract = args.force or doc.get("change_status") in {"NEW", "MODIFIED", "DUPLICATE_EXACT"} or not output_path.exists()
        if not must_extract:
            report_rows.append(report_doc(doc, doc.get("extraction_status", "PENDING"), None, None))
            continue

        file_path = source / doc["relative_path"]
        pages: list[dict[str, Any]]
        diagnostics: dict[str, Any]
        if doc["extension"] == ".pdf":
            pages, diagnostics = extract_pdf(file_path)
        elif doc["extension"] == ".docx":
            pages, diagnostics = extract_docx(file_path)
        else:
            pages, diagnostics = extract_txt(file_path)

        full_text = "\n\n".join(page.get("text", "") for page in pages).strip()
        classification = classify_document(doc["relative_path"], full_text[:8000])
        doc.update(classification)
        doc["extraction_status"] = diagnostics["status"]
        doc["ocr_required"] = diagnostics["ocr_required"]
        doc["last_extracted_at"] = now_iso()
        doc["extraction_diagnostics"] = diagnostics

        extracted = {
            "document_id": doc["document_id"],
            "filename": doc["filename"],
            "relative_path": doc["relative_path"],
            "sha256": doc["sha256"],
            "extracted_at": now_iso(),
            "pages": pages,
            "full_text": full_text,
            "diagnostics": diagnostics,
            "security_notice": "Private extracted text. Do not commit.",
        }
        write_json(output_path, extracted)
        report_rows.append(report_doc(doc, diagnostics["status"], diagnostics["char_count"], diagnostics["page_count"]))
        changed += 1

    inventory["summary"] = build_quality_summary(inventory["documents"])
    write_json(inventory_path, inventory)
    report = {
        "generated_at": now_iso(),
        "changed_or_extracted": changed,
        "rows": report_rows,
        "summary": inventory["summary"],
        "security_notice": "Private extraction report. Do not commit.",
    }
    write_json(REPORT_DIR / f"extraction-report-{safe_stamp()}.private.json", report)
    print(f"Documents extraits ou mis à jour: {changed}")
    print(f"EXTRACTION_OK: {inventory['summary']['extraction_ok']} | OCR_REQUIRED: {inventory['summary']['ocr_required']} | ERREUR: {inventory['summary']['errors']}")
    return report


def text_output_path(document_id: str) -> Path:
    return TEXT_DIR / f"{document_id}.private.json"


def report_doc(doc: dict[str, Any], status: str, chars: int | None, pages: int | None) -> dict[str, Any]:
    return {
        "document_id": doc.get("document_id"),
        "extension": doc.get("extension"),
        "change_status": doc.get("change_status"),
        "extraction_status": status,
        "ocr_required": doc.get("ocr_required", False),
        "char_count": chars,
        "page_count": pages,
        "document_type": doc.get("document_type"),
        "primary_topic": doc.get("primary_topic"),
    }


def find_section_or_article(line: str) -> tuple[str | None, str | None]:
    text = line.strip()
    article_match = re.match(r"^(article\s+[0-9ivxlcdm\-\.]+)", normalize(text), flags=re.IGNORECASE)
    if article_match:
        return None, text[:120]
    section_match = re.match(
        r"^((titre|chapitre|annexe|préambule|preambule|section)\s+[^:]{0,80})",
        text,
        flags=re.IGNORECASE,
    )
    if section_match:
        return text[:160], None
    return None, None


def chunk_text(extracted: dict[str, Any], metadata: dict[str, Any]) -> list[dict[str, Any]]:
    chunks = []
    chunk_number = 1
    current_section: str | None = None
    current_article: str | None = None

    for page in extracted.get("pages", []):
        page_number = page.get("page")
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\r\n\s*\r\n", page.get("text", "")) if p.strip()]
        buffer: list[str] = []

        def flush() -> None:
            nonlocal chunk_number, buffer
            if not buffer:
                return
            text = "\n\n".join(buffer).strip()
            if len(text) < 30:
                buffer = []
                return
            chunks.append(
                {
                    "chunk_id": f"{metadata['document_id']}_chunk_{chunk_number:05d}",
                    "document_id": metadata["document_id"],
                    "filename": metadata["filename"],
                    "relative_path": metadata["relative_path"],
                    "chunk_number": chunk_number,
                    "page": page_number,
                    "section": current_section,
                    "article": current_article,
                    "document_type": metadata.get("document_type"),
                    "primary_topic": metadata.get("primary_topic"),
                    "secondary_topics": metadata.get("secondary_topics", []),
                    "text": text,
                }
            )
            chunk_number += 1
            if len(text) > CHUNK_OVERLAP_CHARS:
                buffer = [text[-CHUNK_OVERLAP_CHARS:]]
            else:
                buffer = []

        for paragraph in paragraphs:
            section, article = find_section_or_article(paragraph.splitlines()[0])
            if section:
                flush()
                current_section = section
                current_article = None
            if article:
                flush()
                current_article = article

            candidate = "\n\n".join(buffer + [paragraph])
            if len(candidate) > MAX_CHUNK_CHARS:
                flush()
            buffer.append(paragraph)

        flush()
    return chunks


def build_index(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    inventory_path, _ = inventory_paths()
    inventory = load_json(inventory_path, None)
    if inventory is None:
        raise SystemExit("Aucun inventaire local. Lancer d'abord update ou scan.")

    docs_by_id = {doc["document_id"]: doc for doc in inventory.get("documents", [])}
    all_chunks: list[dict[str, Any]] = []
    relations = []

    for doc in inventory.get("documents", []):
        if doc.get("change_status") == "MISSING" or doc.get("extraction_status") not in {"EXTRACTION_OK", "EXTRACTION_A_VERIFIER"}:
            continue
        extracted_path = text_output_path(doc["document_id"])
        if not extracted_path.exists():
            continue
        extracted = load_json(extracted_path, {})
        chunks = chunk_text(extracted, doc)
        all_chunks.extend(chunks)
        doc["indexed_at"] = now_iso()

    token_index: dict[str, dict[str, int]] = defaultdict(dict)
    for chunk in all_chunks:
        counts = Counter(tokenize(chunk["text"]))
        for token, count in counts.items():
            token_index[token][chunk["chunk_id"]] = count

    relations = detect_potential_relations(inventory.get("documents", []))
    write_jsonl(INDEX_DIR / "chunks.private.jsonl", all_chunks)
    write_json(INDEX_DIR / "lexical-index.private.json", token_index)
    write_json(INDEX_DIR / "relations.private.json", relations)
    inventory["summary"] = build_quality_summary(inventory["documents"])
    inventory["summary"]["chunks"] = len(all_chunks)
    inventory["summary"]["potential_relations"] = len(relations)
    write_json(inventory_path, inventory)

    report = {
        "generated_at": now_iso(),
        "indexed_documents": len({chunk["document_id"] for chunk in all_chunks}),
        "chunks": len(all_chunks),
        "potential_relations": len(relations),
        "security_notice": "Private index report. Do not commit.",
    }
    write_json(REPORT_DIR / f"index-report-{safe_stamp()}.private.json", report)
    print(f"Documents indexés: {report['indexed_documents']} | Chunks: {report['chunks']} | Relations potentielles: {report['potential_relations']}")
    return report


def detect_potential_relations(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active = [d for d in documents if d.get("change_status") != "MISSING"]
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for doc in active:
        by_topic[doc.get("primary_topic", "autres")].append(doc)

    relations = []
    for doc in active:
        text = normalize(f"{doc.get('filename', '')} {doc.get('document_type', '')}")
        if "avenant" not in text and "modification" not in text:
            continue
        for candidate in by_topic.get(doc.get("primary_topic", "autres"), []):
            if candidate["document_id"] == doc["document_id"]:
                continue
            relations.append(
                {
                    "source_document_id": doc["document_id"],
                    "target_document_id": candidate["document_id"],
                    "relation_type": "RELATION POTENTIELLE - A VERIFIER",
                    "reason": "Document de type avenant/modification et thème commun.",
                    "validated": False,
                }
            )
    return relations


def score_chunk(chunk: dict[str, Any], query_tokens: list[str], exact_query: str) -> float:
    text = normalize(chunk["text"])
    score = 0.0
    if exact_query and normalize(exact_query) in text:
        score += 20
    counts = Counter(tokenize(chunk["text"]))
    for token in query_tokens:
        if token in counts:
            score += 5 + min(counts[token], 5)
    if score > 0 and chunk.get("article"):
        score += 1
    return score


def search_index(args: argparse.Namespace, save: bool = True, quiet: bool = False) -> dict[str, Any]:
    ensure_dirs()
    chunks = read_jsonl(INDEX_DIR / "chunks.private.jsonl")
    if not chunks:
        raise SystemExit("Aucun index local. Lancer update ou index.")

    query = args.query or ""
    query_tokens = tokenize(query)
    if not query_tokens:
        raise SystemExit("Requête vide.")

    results = []
    for chunk in chunks:
        if args.theme and args.theme != chunk.get("primary_topic") and args.theme not in chunk.get("secondary_topics", []):
            continue
        if args.doc_type and args.doc_type != chunk.get("document_type"):
            continue
        if args.document_id and args.document_id != chunk.get("document_id"):
            continue
        score = score_chunk(chunk, query_tokens, query)
        if score <= 0:
            continue
        results.append((score, chunk))

    results.sort(key=lambda item: item[0], reverse=True)
    selected = results[: args.limit]
    sources = [format_source(score, chunk, query_tokens) for score, chunk in selected]
    confidence = "fort" if selected and selected[0][0] >= 35 else "moyen" if selected else "faible"
    response = {
        "question": query,
        "provisional_answer": "Recherche documentaire locale uniquement. Les passages ci-dessous doivent être analysés juridiquement avant conclusion.",
        "confidence_level": confidence,
        "sources_used": sources,
        "points_to_verify": [
            "Vérifier si le document est toujours applicable.",
            "Vérifier s'il existe un avenant ou un texte plus récent.",
            "Croiser avec la convention collective, la loi et la jurisprudence si nécessaire.",
        ],
        "possible_conflicts": [],
        "potentially_linked_newer_document": [],
        "recommended_human_action": "Relire les sources citées et valider la portée avant utilisation.",
        "security_notice": "Private search result. Do not commit.",
    }
    if save:
        write_json(SEARCH_DIR / f"search-{safe_stamp()}.private.json", response)
    if not quiet:
        print_search_response(response)
    return response


def format_source(score: float, chunk: dict[str, Any], query_tokens: list[str]) -> dict[str, Any]:
    text = chunk["text"]
    excerpt = best_excerpt(text, query_tokens)
    return {
        "document": chunk["filename"],
        "document_id": chunk["document_id"],
        "page": chunk.get("page"),
        "article_or_section": chunk.get("article") or chunk.get("section"),
        "location": citation_location(chunk),
        "excerpt": excerpt,
        "match_score": round(score, 2),
        "chunk_id": chunk["chunk_id"],
    }


def citation_location(chunk: dict[str, Any]) -> str:
    parts = []
    if chunk.get("page"):
        parts.append(f"Page {chunk['page']}")
    if chunk.get("article"):
        parts.append(chunk["article"])
    elif chunk.get("section"):
        parts.append(chunk["section"])
    return " - ".join(parts) if parts else "LOCALISATION NON DÉTERMINÉE"


def best_excerpt(text: str, query_tokens: list[str], length: int = 480) -> str:
    normalized = normalize(text)
    positions = [normalized.find(token) for token in query_tokens if normalized.find(token) >= 0]
    start = max(min(positions) - length // 3, 0) if positions else 0
    excerpt = text[start : start + length].strip()
    excerpt = re.sub(r"\s+", " ", excerpt)
    if start > 0:
        excerpt = "..." + excerpt
    if start + length < len(text):
        excerpt += "..."
    return excerpt


def print_search_response(response: dict[str, Any]) -> None:
    print(f"QUESTION: {response['question']}")
    print(f"NIVEAU DE CONFIANCE: {response['confidence_level']}")
    print(f"SOURCES TROUVÉES: {len(response['sources_used'])}")
    for source in response["sources_used"][:5]:
        print(f"- {source['document']} | {source['location']} | score {source['match_score']}")


def run_update(args: argparse.Namespace) -> None:
    scan_corpus(args)
    extract_documents(args)
    build_index(args)


def run_tests(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    rows = []
    for query in BUSINESS_TESTS:
        test_args = argparse.Namespace(query=query, limit=5, theme=None, doc_type=None, document_id=None)
        try:
            response = search_index(test_args, save=False, quiet=True)
            rows.append(
                {
                    "query": query,
                    "result_count": len(response["sources_used"]),
                    "confidence_level": response["confidence_level"],
                    "has_citation": any(item.get("excerpt") for item in response["sources_used"]),
                    "has_page": any(item.get("page") for item in response["sources_used"]),
                    "has_article_or_section": any(item.get("article_or_section") for item in response["sources_used"]),
                }
            )
        except SystemExit:
            rows.append({"query": query, "result_count": 0, "confidence_level": "faible", "has_citation": False, "has_page": False, "has_article_or_section": False})
    report = {
        "generated_at": now_iso(),
        "tests": rows,
        "coverage": {
            "queries": len(rows),
            "queries_with_results": sum(1 for row in rows if row["result_count"] > 0),
            "queries_with_page": sum(1 for row in rows if row["has_page"]),
            "queries_with_article_or_section": sum(1 for row in rows if row["has_article_or_section"]),
        },
        "security_notice": "Private business test report. Do not commit.",
    }
    write_json(TEST_DIR / f"business-tests-{safe_stamp()}.private.json", report)
    print(f"Tests métier: {report['coverage']['queries']} | Avec résultats: {report['coverage']['queries_with_results']} | Avec page: {report['coverage']['queries_with_page']}")
    return report


def run_missing(args: argparse.Namespace) -> dict[str, Any]:
    query = args.query or "situation à préciser"
    response = {
        "question": query,
        "before_continuing_request": [
            "Décrire précisément les faits ou le sujet CSE.",
            "Indiquer les dates exactes utiles.",
            "Joindre le document de direction si un texte est cité.",
            "Vérifier si un accord ou avenant local plus récent existe.",
            "Préciser si le sujet relève aussi de la convention collective, du Code du travail ou d'une source institutionnelle.",
        ],
        "human_controls": ["correction humaine", "non applicable", "ajout d'une note terrain", "validation document suffisant"],
        "security_notice": "Private missing-information helper. Do not commit.",
    }
    write_json(SEARCH_DIR / f"missing-{safe_stamp()}.private.json", response)
    print("AVANT DE POURSUIVRE, DEMANDER EN PRIORITÉ :")
    for item in response["before_continuing_request"]:
        print(f"- {item}")
    return response


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bible Accords Sarralbe V1 - local secure pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    for command in ["scan", "extract", "index", "update"]:
        p = sub.add_parser(command)
        p.add_argument("--source", help="Chemin local privé du corpus. Sinon CFDT_NEXUS_CORPUS_PATH.")
        p.add_argument("--force", action="store_true", help="Retraiter même si inchangé.")

    p_search = sub.add_parser("search")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--limit", type=int, default=8)
    p_search.add_argument("--theme")
    p_search.add_argument("--doc-type")
    p_search.add_argument("--document-id")

    p_test = sub.add_parser("test")
    p_test.add_argument("--limit", type=int, default=5)

    p_missing = sub.add_parser("missing")
    p_missing.add_argument("--query", required=True)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    ensure_dirs()
    if args.command == "scan":
        scan_corpus(args)
    elif args.command == "extract":
        extract_documents(args)
    elif args.command == "index":
        build_index(args)
    elif args.command == "update":
        run_update(args)
    elif args.command == "search":
        search_index(args)
    elif args.command == "test":
        run_tests(args)
    elif args.command == "missing":
        run_missing(args)
    else:
        raise SystemExit(f"Commande inconnue: {args.command}")


if __name__ == "__main__":
    main()
