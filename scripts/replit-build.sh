#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python -m pip install -r "$ROOT/backend/requirements.txt"
cd "$ROOT/frontend"
npm install
npm run build
