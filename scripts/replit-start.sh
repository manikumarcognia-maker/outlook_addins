#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
cd "$ROOT/backend"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-4000}"
