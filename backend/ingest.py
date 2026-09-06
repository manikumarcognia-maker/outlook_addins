#!/usr/bin/env python3
"""CLI entry point for the RAG indexing pipeline."""

import argparse
import sys

from rag.ingest import ingest_file
from rag.qdrant_store import get_client, list_documents, mark_superseded


def main() -> int:
    parser = argparse.ArgumentParser(description="Fr8Labs RAG document indexing")
    parser.add_argument("file_path", nargs="?", help="Path to PDF, DOCX, or TXT file")
    parser.add_argument("--list", action="store_true", help="List indexed documents from Qdrant")
    parser.add_argument("--supersede", metavar="DOCUMENT_ID", help="Mark document superseded and delete chunks")

    args = parser.parse_args()

    if args.list:
        client = get_client()
        docs = list_documents(client)
        if not docs:
            print("No documents indexed.")
            return 0
        for doc in docs:
            print(
                f"{doc['document_id']} | {doc.get('original_filename')} | "
                f"active={doc.get('active')} | "
                f"chunks={doc.get('chunk_count')} | {doc.get('uploaded_at')}"
            )
        return 0

    if args.supersede:
        client = get_client()
        mark_superseded(client, args.supersede)
        print(f"Superseded and deleted chunks for document_id={args.supersede}")
        return 0

    if not args.file_path:
        parser.print_help()
        return 1

    try:
        document_id = ingest_file(args.file_path)
        print(f"Ingested successfully: {document_id}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
