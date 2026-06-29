"""
RAG handler using BM25 keyword search (no external API needed).

Documents are indexed offline via build_knowledge_base.py.
At startup, the index is loaded and BM25 is built in memory.
"""

import json
from pathlib import Path

KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent / 'knowledge_base'
INDEX_FILE = KNOWLEDGE_BASE_DIR / 'index.json'

_chunks: list = []
_bm25 = None


def _tokenize(text: str) -> list:
    return text.split()


def get_relevant_context(query: str, top_k: int = 3) -> str:
    if _bm25 is None or not _chunks:
        return ''

    tokens = _tokenize(query)
    scores = _bm25.get_scores(tokens)

    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results = []
    for i in ranked:
        if scores[i] > 0:
            results.append(f"[منبع: {_chunks[i]['source']}]\n{_chunks[i]['text']}")

    return '\n\n---\n\n'.join(results)


def load_knowledge_base():
    global _chunks, _bm25

    if not INDEX_FILE.exists():
        print('[RAG] No index found — RAG inactive. Run: py backend/build_knowledge_base.py')
        return

    try:
        from rank_bm25 import BM25Okapi
        data = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
        _chunks = data.get('chunks', [])
        tokenized = [_tokenize(c['text']) for c in _chunks]
        _bm25 = BM25Okapi(tokenized)
        print(f'[RAG] Loaded {len(_chunks)} chunks — BM25 ready.')
    except ImportError:
        print('[RAG] rank_bm25 not installed. Run: pip install rank_bm25')
    except Exception as e:
        print(f'[RAG] Failed to load index: {e}')
