#!/usr/bin/env bash
#
# Build a standalone PromptPilot executable for Linux.
#
# Usage:
#   ./scripts/build_linux.sh                 # version "dev"
#   RELEASE_VERSION=v1.0.0 ./scripts/build_linux.sh
#
# Produces:
#   artifacts/promptpilot-<version>-linux-x64/promptpilot
#   artifacts/promptpilot-<version>-linux-x64/release-manifest.json
#   artifacts/promptpilot-<version>-linux-x64/SHA256SUMS.txt
#   artifacts/promptpilot-<version>-linux-x64.tar.gz
#
set -euo pipefail

cd "$(dirname "$0")/.."

VERSION="${RELEASE_VERSION:-dev}"
PLATFORM="linux-x64"
OUTPUT_DIR="artifacts/promptpilot-${VERSION}-${PLATFORM}"
ARCHIVE="artifacts/promptpilot-${VERSION}-${PLATFORM}.tar.gz"

echo "Cleaning previous artifacts..."
rm -rf build dist artifacts
rm -f promptpilot.spec
mkdir -p "$OUTPUT_DIR"

echo "Installing build dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"

echo "Running tests..."
python3 -m pytest --cov=promptpilot --cov-report=term-missing

echo "Building the promptpilot executable..."
python3 -m PyInstaller \
    --noconfirm \
    --clean \
    --onefile \
    --console \
    --name promptpilot \
    --paths src \
    src/promptpilot/__main__.py

install -m 0755 dist/promptpilot "$OUTPUT_DIR/promptpilot"

echo "Smoke-testing the executable..."
"$OUTPUT_DIR/promptpilot" --version
"$OUTPUT_DIR/promptpilot" --help > /dev/null
echo "Smoke test passed."

cat > "$OUTPUT_DIR/release-manifest.json" <<JSON
{
  "product": "PromptPilot",
  "version": "${VERSION}",
  "platform": "${PLATFORM}",
  "python": "$(python3 --version)",
  "built_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "binary": "promptpilot"
}
JSON

(
    cd "$OUTPUT_DIR"
    sha256sum promptpilot release-manifest.json > SHA256SUMS.txt
)

tar -czf "$ARCHIVE" -C artifacts "promptpilot-${VERSION}-${PLATFORM}"

echo "Release bundle: ${ARCHIVE}"
