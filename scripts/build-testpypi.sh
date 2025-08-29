#!/usr/bin/env bash
set -euo pipefail

# Build local packages and optionally upload them to TestPyPI
#
# Usage:
#   scripts/build-testpypi.sh [--upload] [--repository-url URL]
#
# Environment variables:
#   PYTHON_BIN          Python executable to use (default: python3)
#   TWINE_USERNAME      Username for TestPyPI (set when using --upload)
#   TWINE_PASSWORD      Password/token for TestPyPI (set when using --upload)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
UPLOAD=0
REPO_URL="https://test.pypi.org/legacy/"

usage() {
  echo "Usage: $0 [--upload] [--repository-url URL]" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --upload)
      UPLOAD=1
      shift
      ;;
    --repository-url)
      [[ $# -ge 2 ]] || usage
      REPO_URL="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      ;;
  esac
done

echo "[forge] Ensuring build tooling is installed (build, twine)"
"$PYTHON_BIN" -m pip install --upgrade --quiet build twine

build_pkg() {
  local pkg_dir="$1"
  local name
  name="$(basename "$pkg_dir")"
  echo "[forge] Building $name"
  pushd "$pkg_dir" >/dev/null
  rm -rf dist
  "$PYTHON_BIN" -m build .
  "$PYTHON_BIN" -m twine check dist/*
  popd >/dev/null
}

upload_pkg() {
  local pkg_dir="$1"
  local name
  name="$(basename "$pkg_dir")"
  echo "[forge] Uploading $name to $REPO_URL"
  "$PYTHON_BIN" -m twine upload \
    --non-interactive \
    --repository-url "$REPO_URL" \
    "$pkg_dir"/dist/*
}

cd "$ROOT_DIR"

# Build core first, then cli (which depends on core)
build_pkg "$ROOT_DIR/packages/core"
build_pkg "$ROOT_DIR/packages/cli"

if [[ "$UPLOAD" -eq 1 ]]; then
  if [[ -z "${TWINE_USERNAME:-}" || -z "${TWINE_PASSWORD:-}" ]]; then
    echo "[forge] TWINE_USERNAME and TWINE_PASSWORD must be set for upload" >&2
    exit 2
  fi
  upload_pkg "$ROOT_DIR/packages/core"
  upload_pkg "$ROOT_DIR/packages/cli"
  echo "[forge] Upload complete. Verify at https://test.pypi.org/project/"
else
  echo "[forge] Build complete. Artifacts in packages/*/dist"
  echo "[forge] To upload, rerun with --upload and export TWINE_USERNAME/TWINE_PASSWORD"
fi


