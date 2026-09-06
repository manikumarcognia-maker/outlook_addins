#!/usr/bin/env python3
"""CLI entry point for the RAG draft-reply pipeline."""

import argparse
import json
import sys

from rag.generation import generate_draft_reply


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an AI draft reply from an email")
    parser.add_argument("subject", help="Email subject line")
    parser.add_argument("body", help="Email body text")
    args = parser.parse_args()

    try:
        result = generate_draft_reply(args.subject, args.body)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("=== DRAFT REPLY ===")
    print(result.draft_text)
    print()
    print(f"Rerank succeeded: {result.rerank_succeeded}")
    print()
    print("=== CITATIONS ===")
    citations = [
        {
            "document_id": c.document_id,
            "original_filename": c.original_filename,
            "chunk_index": c.chunk_index,
        }
        for c in result.citations
    ]
    print(json.dumps(citations, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
