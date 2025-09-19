#!/usr/bin/env bash
set -euo pipefail
OUTPUT=${1:-../specs/openapi.json}
python - <<'PY'
from pathlib import Path
from src.main import app
from fastapi.openapi.utils import get_openapi

spec = get_openapi(title=app.title, version="0.1.0", routes=app.routes)
Path("../specs").mkdir(exist_ok=True)
Path(OUTPUT).write_text(__import__('json').dumps(spec, indent=2))
PY

echo "OpenAPI spec written to $OUTPUT"
