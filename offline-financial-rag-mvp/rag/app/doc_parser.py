
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List
from pypdf import PdfReader

from .config import USE_DOCLING, DOCLING_PREFER


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def chunk_text(text: str, max_chars: int = 1800, overlap: int = 250) -> List[str]:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + max_chars)
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start = max(0, end - overlap)

    return chunks


def parse_with_docling(pdf_path: Path) -> List[Dict]:
    """
    Optional Docling parser.
    If Docling import/conversion fails for any reason, return [] so that
    the caller can safely fall back to PyPDF.
    """
    try:
        from docling.document_converter import DocumentConverter
    except Exception as e:
        print(f"[WARN] Docling import failed for {pdf_path.name}: {e}")
        return []

    try:
        print(f"[INFO] Trying Docling parser for {pdf_path.name} ...")
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))

        markdown = result.document.export_to_markdown()
        out: List[Dict] = []

        for idx, chunk in enumerate(chunk_text(markdown)):
            out.append(
                {
                    "page_no": None,
                    "section": "Docling Extract",
                    "chunk_text": chunk,
                    "chunk_type": "text",
                    "table_markdown": None,
                    "metadata": {
                        "extractor": "docling",
                        "source_format": "markdown",
                        "chunk_index": idx,
                    },
                }
            )

        print(f"[INFO] Docling succeeded for {pdf_path.name} with {len(out)} chunks")
        return out

    except Exception as e:
        print(f"[WARN] Docling parsing failed for {pdf_path.name}: {e}")
        return []


def parse_with_pypdf(pdf_path: Path) -> List[Dict]:
    """
    Lightweight fallback / default parser using text extraction only.
    Suitable for text-based annual reports and avoids OCR-heavy memory usage.
    """
    print(f"[INFO] Using PyPDF parser for {pdf_path.name} ...")
    reader = PdfReader(str(pdf_path))
    out: List[Dict] = []

    for page_no, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as e:
            print(f"[WARN] Failed extracting text from page {page_no} of {pdf_path.name}: {e}")
            text = ""

        chunks = chunk_text(text)
        for idx, chunk in enumerate(chunks):
            out.append(
                {
                    "page_no": page_no,
                    "section": f"Page {page_no}",
                    "chunk_text": chunk,
                    "chunk_type": "text",
                    "table_markdown": None,
                    "metadata": {
                        "extractor": "pypdf",
                        "page_chunk_index": idx,
                    },
                }
            )

    print(f"[INFO] PyPDF extracted {len(out)} chunks for {pdf_path.name}")
    return out


def parse_pdf(pdf_path: Path) -> Dict:
    """
    Parsing strategy:
    1. Default to PyPDF (stable, low memory)
    2. Use Docling only if USE_DOCLING=true
    3. If DOCLING_PREFER=true, try Docling first
    4. If Docling fails, automatically fall back to PyPDF
    """
    parser = "pypdf"
    chunks: List[Dict] = []

    if USE_DOCLING and DOCLING_PREFER:
        docling_chunks = parse_with_docling(pdf_path)
        if docling_chunks:
            chunks = docling_chunks
            parser = "docling"
        else:
            chunks = parse_with_pypdf(pdf_path)
            parser = "pypdf"

    elif USE_DOCLING and not DOCLING_PREFER:
        # Default path still uses PyPDF first for stability
        chunks = parse_with_pypdf(pdf_path)
        parser = "pypdf"

        # Optional future enhancement:
        # selectively invoke Docling only for scanned / image-only PDFs
        # For MVP, keep PyPDF as the safer default.

    else:
        chunks = parse_with_pypdf(pdf_path)
        parser = "pypdf"

    return {
        "file_name": pdf_path.name,
        "file_path": str(pdf_path.resolve()),
        "title": pdf_path.stem,
        "company_name": pdf_path.stem.split("_")[0] if "_" in pdf_path.stem else pdf_path.stem,
        "fiscal_year": None,
        "checksum": sha256_file(pdf_path),
        "parser": parser,
        "chunks": chunks,
    }