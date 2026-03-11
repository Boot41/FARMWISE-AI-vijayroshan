from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

DOCS_DIR = Path(__file__).resolve().parent / "docs"
INDEX_PATH = DOCS_DIR / "index.json"
MAX_CHUNK_CHARS = 1200
TARGET_CHUNK_CHARS = 900
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "with",
}


@dataclass
class Section:
    heading_path: list[str]
    text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build markdown files from PDFs and regenerate a retrieval index.",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=DOCS_DIR,
        help="Directory containing the document corpus.",
    )
    parser.add_argument(
        "--force-md",
        action="store_true",
        help="Regenerate markdown files even when they already exist.",
    )
    return parser.parse_args()


def run_pdftotext(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def clean_extracted_text(text: str) -> str:
    text = text.replace("\x0c", "\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def prettify_stem(stem: str) -> str:
    return stem.replace("_", " ").replace("-", " ").strip().title()


def pick_title(raw_text: str, fallback: str) -> str:
    for line in raw_text.splitlines():
        candidate = re.sub(r"\s+", " ", line).strip(" -\t")
        if len(candidate) < 4:
            continue
        if re.fullmatch(r"[\d\W_]+", candidate):
            continue
        return candidate
    return fallback


def render_markdown(pdf_path: Path, raw_text: str) -> str:
    title = pick_title(raw_text, prettify_stem(pdf_path.stem))
    body = clean_extracted_text(raw_text)
    lines = body.splitlines()
    if lines and lines[0].strip() == title:
        lines = lines[1:]
    body = "\n".join(lines).strip()
    return f"# {title}\n\n_Source PDF: `{pdf_path.name}`_\n\n{body}\n"


def ensure_markdown_from_pdfs(docs_dir: Path, force_md: bool) -> list[Path]:
    generated: list[Path] = []
    for pdf_path in sorted(docs_dir.rglob("*.pdf")):
        md_path = pdf_path.with_suffix(".md")
        if md_path.exists() and not force_md:
            continue
        raw_text = run_pdftotext(pdf_path)
        markdown = render_markdown(pdf_path, raw_text)
        md_path.write_text(markdown, encoding="utf-8")
        generated.append(md_path)
    return generated


def normalize_markdown(md_text: str) -> str:
    md_text = md_text.replace("\r\n", "\n").replace("\r", "\n")
    md_text = re.sub(r"\n{3,}", "\n\n", md_text)
    return md_text.strip()


def iter_sections(md_text: str) -> Iterable[Section]:
    heading_path: list[str] = []
    buffer: list[str] = []

    def flush() -> Section | None:
        text = "\n".join(buffer).strip()
        if not text:
            return None
        return Section(heading_path=heading_path.copy(), text=text)

    for raw_line in normalize_markdown(md_text).splitlines():
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", raw_line.strip())
        if heading_match:
            section = flush()
            if section is not None:
                yield section
            buffer.clear()
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            heading_path[:] = heading_path[: level - 1]
            heading_path.append(title)
            continue
        buffer.append(raw_line.rstrip())

    section = flush()
    if section is not None:
        yield section


def split_section_text(text: str, target_chars: int, max_chars: int) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                proposal = sentence if not current else f"{current} {sentence}"
                if len(proposal) > max_chars and current:
                    chunks.append(current.strip())
                    current = sentence
                else:
                    current = proposal
            continue

        proposal = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(proposal) > max_chars and current:
            chunks.append(current.strip())
            current = paragraph
            continue
        current = proposal
        if len(current) >= target_chars:
            chunks.append(current.strip())
            current = ""

    if current.strip():
        chunks.append(current.strip())

    return chunks


def extract_keywords(text: str, limit: int = 12) -> list[str]:
    counts: dict[str, int] = {}
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower()):
        if token in STOPWORDS:
            continue
        counts[token] = counts.get(token, 0) + 1

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _ in ranked[:limit]]


def build_index(docs_dir: Path) -> dict[str, object]:
    documents: list[dict[str, object]] = []
    chunks: list[dict[str, object]] = []

    for md_path in sorted(docs_dir.rglob("*.md")):
        relative_path = md_path.relative_to(docs_dir).as_posix()
        if relative_path == "index.md":
            continue

        text = normalize_markdown(md_path.read_text(encoding="utf-8"))
        lines = text.splitlines()
        title = md_path.stem
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        category = md_path.parent.relative_to(docs_dir).as_posix() or "root"
        source_pdf = md_path.with_suffix(".pdf")
        source_pdf_path = (
            source_pdf.relative_to(docs_dir).as_posix() if source_pdf.exists() else None
        )
        document_id = relative_path.replace("/", "__").removesuffix(".md")

        documents.append(
            {
                "id": document_id,
                "title": title,
                "path": relative_path,
                "category": category,
                "source_pdf": source_pdf_path,
                "word_count": len(text.split()),
                "char_count": len(text),
                "keywords": extract_keywords(text),
            }
        )

        for section_index, section in enumerate(iter_sections(text), start=1):
            section_chunks = split_section_text(
                section.text,
                target_chars=TARGET_CHUNK_CHARS,
                max_chars=MAX_CHUNK_CHARS,
            )
            for chunk_index, chunk_text in enumerate(section_chunks, start=1):
                chunk_id = f"{document_id}::s{section_index:03d}::c{chunk_index:03d}"
                chunks.append(
                    {
                        "id": chunk_id,
                        "document_id": document_id,
                        "path": relative_path,
                        "category": category,
                        "title": title,
                        "heading_path": section.heading_path,
                        "text": chunk_text,
                        "word_count": len(chunk_text.split()),
                        "char_count": len(chunk_text),
                        "keywords": extract_keywords(chunk_text),
                        "source_pdf": source_pdf_path,
                    }
                )

    return {
        "version": 1,
        "docs_dir": docs_dir.as_posix(),
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "documents": documents,
        "chunks": chunks,
    }


def main() -> None:
    args = parse_args()
    docs_dir = args.docs_dir.resolve()
    generated = ensure_markdown_from_pdfs(docs_dir, force_md=args.force_md)
    index = build_index(docs_dir)
    index_path = docs_dir / "index.json"
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Docs directory: {docs_dir}")
    print(f"Markdown files generated: {len(generated)}")
    print(f"Index written to: {index_path}")
    print(f"Documents indexed: {index['document_count']}")
    print(f"Chunks indexed: {index['chunk_count']}")


if __name__ == "__main__":
    main()
