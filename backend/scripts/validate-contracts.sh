#!/usr/bin/env bash
set -euo pipefail
SPEC_DIR=../specs/001-bashclaudecli-specify-bodam/contracts
for file in "$SPEC_DIR"/*.yaml; do
  echo "Validating $file ..."
  # TODO: integrate with spectral or openapi-cli
done
echo "Contracts validation placeholder complete"
