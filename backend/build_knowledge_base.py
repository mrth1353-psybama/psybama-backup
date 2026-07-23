"""
Build the RAG knowledge base index for Psybama.

Usage:
    py backend/build_knowledge_base.py

Place your PDF/DOCX/TXT files in the knowledge_base/ directory first.
Generates knowledge_base/index.json with text chunks (no API needed).
Re-run this script whenever you add or update documents.
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / 'knowledge_base'
INDEX_FILE = KNOWLEDGE_BASE_DIR / 'index.json'

CHUNK_SIZE = 400
CHUNK_OVERLAP = 100


def extract_pdf(path: Path) -> str:
    try:
        import pdfplumber
        from bidi.algorithm import get_display
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                # PDFs with RTL (Persian/Arabic) content extract in visual glyph
                # order, not logical reading order — bidi reorders each line.
                fixed_lines = [get_display(line, base_dir='L') for line in text.split('\n')]
                pages.append('\n'.join(fixed_lines))
        return '\n'.join(pages)
    except ImportError:
        print('  ERROR: pdfplumber/python-bidi not installed. Run: pip install pdfplumber python-bidi')
        return ''
    except Exception as e:
        print(f'  ERROR reading PDF: {e}')
        return ''


def extract_docx(path: Path) -> str:
    try:
        from docx import Document
        doc = Document(str(path))
        return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        print('  ERROR: python-docx not installed. Run: pip install python-docx')
        return ''
    except Exception as e:
        print(f'  ERROR reading DOCX: {e}')
        return ''


def extract_txt(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def chunk_text(text: str, source: str) -> list:
    text = ' '.join(text.split())
    chunks = []
    start = 0
    while start < len(text):
        piece = text[start: start + CHUNK_SIZE]
        if piece.strip():
            chunks.append({'text': piece, 'source': source})
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def main():
    supported_exts = {'.pdf', '.docx', '.txt'}
    files = [
        f for f in KNOWLEDGE_BASE_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in supported_exts
    ]

    if not files:
        print(f'No documents found in {KNOWLEDGE_BASE_DIR}')
        print('Place your PDF/DOCX/TXT files there and run again.')
        sys.exit(0)

    print(f'Found {len(files)} document(s):')
    for f in files:
        print(f'  - {f.name}')
    print()

    all_chunks = []
    for file in sorted(files):
        print(f'Processing: {file.name}')
        ext = file.suffix.lower()
        if ext == '.pdf':
            text = extract_pdf(file)
        elif ext == '.docx':
            text = extract_docx(file)
        else:
            text = extract_txt(file)

        if not text.strip():
            print('  Warning: No text extracted — skipping.')
            continue

        chunks = chunk_text(text, file.name)
        print(f'  -> {len(chunks)} chunks')
        all_chunks.extend(chunks)

    if not all_chunks:
        print('No chunks created. Check your documents.')
        sys.exit(1)

    INDEX_FILE.write_text(
        json.dumps({'chunks': all_chunks}, ensure_ascii=False),
        encoding='utf-8',
    )

    total = len(all_chunks)
    print(f'\nDone — {total} chunks saved to index.json')
    print('No API key needed. RAG is ready.')


if __name__ == '__main__':
    main()
