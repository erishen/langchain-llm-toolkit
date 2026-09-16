"""Build a personal-profile vector store for the local RAG API.

Reads a curated markdown subset from a corpus that lives outside this repo and
indexes it into the local qdrant store the RAG API serves. Both the corpus root
and the sub-directories to include come from the environment, so nothing
corpus-specific is hard-coded here. Run from the toolkit app dir:

    PROFILE_DOCS_ROOT=/path/to/corpus PROFILE_INCLUDE_DIRS=dirA,dirB \
        uv run python scripts/build_profile_store.py
"""

import os
from pathlib import Path

from langchain_core.documents import Document

from langchain_llm_toolkit.rag import RAGSystem

_docs_root = os.environ.get("PROFILE_DOCS_ROOT", "").strip()
_include_dirs = os.environ.get("PROFILE_INCLUDE_DIRS", "").strip()
if not _docs_root or not _include_dirs:
    raise SystemExit(
        "PROFILE_DOCS_ROOT and PROFILE_INCLUDE_DIRS must both be set "
        "(comma-separated directory names relative to the corpus root)."
    )

DOCS_ROOT = Path(_docs_root).expanduser()
INCLUDE_DIRS = [d.strip() for d in _include_dirs.split(",") if d.strip()]


def main() -> None:
    docs: list[Document] = []
    for sub in INCLUDE_DIRS:
        for f in sorted((DOCS_ROOT / sub).rglob("*.md")):
            try:
                text = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                print(f"skip (encoding): {f.name}")
                continue
            docs.append(
                Document(
                    page_content=text,
                    metadata={"source": str(f), "category": sub, "file": f.name},
                )
            )
    print(f"collected {len(docs)} markdown docs from {len(INCLUDE_DIRS)} dirs")

    rag = RAGSystem()
    rag.create_vector_store(docs)  # qdrant path mode persists automatically
    print("vector store created & persisted")


if __name__ == "__main__":
    main()
