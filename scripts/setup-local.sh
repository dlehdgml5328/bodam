#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$ROOT_DIR/.venv"

log() {
  printf '[setup] %s\n' "$1"
}

warn() {
  printf '[setup][warn] %s\n' "$1"
}

error() {
  printf '[setup][error] %s\n' "$1" >&2
  exit 1
}

# 1. Ensure Python is available
command -v python3 >/dev/null 2>&1 || error "python3 not found. Install Python 3.11+ first."

# 2. Prepare virtual environment
if [[ ! -d "$VENV_DIR" ]]; then
  log "Creating virtual environment at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

log "Upgrading pip"
pip install --upgrade pip >/dev/null

log "Installing backend dependencies"
pip install -e "$BACKEND_DIR" >/dev/null

# 3. Ensure backend .env exists
if [[ -f "$BACKEND_DIR/.env.example" && ! -f "$BACKEND_DIR/.env" ]]; then
  log "Creating backend/.env from template"
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi

# 4. Install frontend dependencies (if Node is available)
if command -v npm >/dev/null 2>&1; then
  log "Installing frontend dependencies"
  pushd "$FRONTEND_DIR" >/dev/null
  if [[ -f package-lock.json ]]; then
    npm ci >/dev/null
  else
    npm install >/dev/null
  fi
  popd >/dev/null
else
  warn "npm not found. Skipping frontend dependency install."
fi

# 5. Prepare containers and database (requires Docker)
if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    log "Building backend image"
    docker compose build backend
    log "Starting database services"
    docker compose up -d db redis
    log "Running database migrations"
    docker compose run --rm backend alembic upgrade head
  else
    warn "docker compose not available. Skipping container setup."
  fi
else
  warn "Docker not installed. Skipping container setup."
fi

log "Local setup complete."
