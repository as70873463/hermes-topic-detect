#!/usr/bin/env bash
# Hermes ARC (Adaptive Routing Core) — One-Click Install
# Internal plugin name: topic_detect
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash
#   bash install.sh [--plugin-dir PATH] [--no-restart]

set -euo pipefail

# ── Defaults ────────────────────────────────────────────────────────────────
REPO_RAW="https://raw.githubusercontent.com/ShockShoot/hermes-arc/main"
PLUGIN_DIR="${HOME}/.hermes/plugins/topic_detect"
RESTART=true

# ── Parse args ──────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --plugin-dir) PLUGIN_DIR="$2"; shift 2 ;;
    --no-restart) RESTART=false; shift ;;
    -h|--help)
      echo "Usage: bash install.sh [--plugin-dir PATH] [--no-restart]"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo ""
echo "🧊 Hermes ARC (Adaptive Routing Core) — Installer"
echo "   Plugin name : topic_detect"
echo "   Target dir : ${PLUGIN_DIR}"
echo ""

# ── Pre-flight checks ───────────────────────────────────────────────────────
if ! command -v hermes &>/dev/null; then
  echo "❌ Hermes CLI not found. Install hermes-agent first:"
  echo "   pip install hermes-agent"
  exit 1
fi

# ── Create plugin directory ─────────────────────────────────────────────────
mkdir -p "${PLUGIN_DIR}"
echo "✅ Plugin directory ready: ${PLUGIN_DIR}"

# ── Source files to install ─────────────────────────────────────────────────
FILES=(
  __init__.py
  state.py
  classifier.py
  semantic.py
  config.py
  agent_loader.py
  signature.py
  patch_run_agent.py
  AGENTS.md
  plugin.yaml
  README.md
)

# ── Download or copy ────────────────────────────────────────────────────────
if [[ "${REPO_RAW}" == *"<USERNAME>"* ]]; then
  echo ""
  echo "⚠️  REPO_RAW contains <USERNAME>/<REPO> placeholder."
  echo "    Copying from local plugin directory instead..."
  echo ""

  LOCAL_SRC="${HOME}/.hermes/plugins/topic_detect"
  for f in "${FILES[@]}"; do
    if [[ -f "${LOCAL_SRC}/${f}" ]]; then
      if [[ "${LOCAL_SRC}/${f}" -ef "${PLUGIN_DIR}/${f}" ]]; then
        echo "  ✅ ${f} (already in place)"
      else
        cp -f "${LOCAL_SRC}/${f}" "${PLUGIN_DIR}/${f}"
        echo "  ✅ ${f}"
      fi
    else
      echo "  ⚠️  ${f} not found in ${LOCAL_SRC} — skipped"
    fi
  done
else
  echo "Downloading from: ${REPO_RAW}"
  for f in "${FILES[@]}"; do
    if curl -fsSL "${REPO_RAW}/${f}" -o "${PLUGIN_DIR}/${f}"; then
      echo "  ✅ ${f}"
    else
      echo "  ❌ Failed to download ${f}"
      exit 1
    fi
  done
fi

echo ""

# ── Syntax check ────────────────────────────────────────────────────────────
echo "🔍 Running Python syntax check..."
if python3 -m compileall "${PLUGIN_DIR}" -q 2>/dev/null; then
  echo "   ✅ All Python files compile OK"
else
  echo "   ❌ Syntax error detected! Aborting."
  exit 1
fi
echo ""

# ── Verify .env exists ─────────────────────────────────────────────────────
ENV_FILE="${HOME}/.hermes/.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "⚠️  No .env found at ${ENV_FILE}"
  echo "   Create one with your API keys:"
  echo "   echo 'OPENROUTER_API_KEY=sk-or-...' > ${ENV_FILE}"
  echo ""
fi

# ── Enable plugin ───────────────────────────────────────────────────────────
echo "🔧 Enabling plugin..."
hermes plugins enable topic_detect 2>&1 || true
echo ""

# ── Restart ─────────────────────────────────────────────────────────────────
if [[ "${RESTART}" == true ]]; then
  echo "🔄 Restarting Hermes..."
  hermes restart 2>&1 || true
  echo ""
fi

# ── Done ────────────────────────────────────────────────────────────────────
echo "─────────────────────────────────────────────"
echo "✅ Hermes ARC installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Set OPENROUTER_API_KEY in ~/.hermes/.env"
echo "  2. Configure topic_detect in ~/.hermes/config.yaml"
echo "  3. Run: hermes logs | grep topic_detect"
echo ""
echo "Docs: ${PLUGIN_DIR}/README.md"
echo "─────────────────────────────────────────────"
