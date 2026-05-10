#!/usr/bin/env bash
# Hermes ARC (Adaptive Routing Core) — One-Click Install
# Internal plugin name: topic_detect
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --patch-runtime
#   bash install.sh [--plugin-dir PATH] [--run-agent-path PATH] [--no-restart] [--patch-runtime|--no-patch-runtime]

set -euo pipefail

# ── Defaults ────────────────────────────────────────────────────────────────
REPO_RAW="https://raw.githubusercontent.com/ShockShoot/hermes-arc/main"
PLUGIN_DIR="${HOME}/.hermes/plugins/topic_detect"
RESTART=true
PATCH_RUNTIME="prompt" # prompt | yes | no
RUN_AGENT_PATH=""
CONFIGURE=true
CONFIG_PATH="${HOME}/.hermes/config.yaml"

# ── Parse args ──────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --plugin-dir) PLUGIN_DIR="$2"; shift 2 ;;
    --run-agent-path) RUN_AGENT_PATH="$2"; shift 2 ;;
    --config-path) CONFIG_PATH="$2"; shift 2 ;;
    --no-config) CONFIGURE=false; shift ;;
    --no-restart) RESTART=false; shift ;;
    --patch-runtime) PATCH_RUNTIME="yes"; shift ;;
    --no-patch-runtime) PATCH_RUNTIME="no"; shift ;;
    -h|--help)
      echo "Usage: bash install.sh [--plugin-dir PATH] [--config-path PATH] [--run-agent-path PATH] [--no-config] [--no-restart] [--patch-runtime|--no-patch-runtime]"
      echo ""
      echo "Config options:"
      echo "  --config-path PATH    Target Hermes config.yaml (default: ~/.hermes/config.yaml)"
      echo "  --no-config           Do not modify config.yaml"
      echo ""
      echo "Runtime patch options:"
      echo "  --run-agent-path PATH Target a specific Hermes run_agent.py when multiple installs exist"
      echo "  --patch-runtime       Patch Hermes run_agent.py automatically if ARC support is missing"
      echo "  --no-patch-runtime    Never patch Hermes core runtime"
      echo "  default               Ask before patching when a TTY is available; skip in non-interactive mode"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo ""
echo "🧊 Hermes ARC (Adaptive Routing Core) — Installer"
echo "   Plugin name : topic_detect"
echo "   Target dir  : ${PLUGIN_DIR}"
echo ""

# ── Pre-flight checks ───────────────────────────────────────────────────────
if ! command -v hermes &>/dev/null; then
  echo "❌ Hermes CLI not found. Install hermes-agent first:"
  echo "   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
  exit 1
fi

if ! command -v python3 &>/dev/null; then
  echo "❌ python3 not found. Hermes ARC requires Python 3."
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
  README_TH.md
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

# ── Optional Hermes runtime compatibility patch ─────────────────────────────
PATCHER="${PLUGIN_DIR}/patch_run_agent.py"
if [[ -f "${PATCHER}" ]]; then
  echo "🔎 Locating Hermes run_agent.py..."

  if [[ -z "${RUN_AGENT_PATH}" ]]; then
    mapfile -t RUN_AGENT_CANDIDATES < <(python3 "${PATCHER}" --list 2>/dev/null || true)

    if [[ ${#RUN_AGENT_CANDIDATES[@]} -eq 0 ]]; then
      echo "⚠️  No Hermes run_agent.py found. Runtime compatibility check skipped."
      echo "   If Hermes is installed in a custom location, re-run with:"
      echo "   bash install.sh --run-agent-path /path/to/run_agent.py"
      echo ""
      RUN_AGENT_PATH=""
    elif [[ ${#RUN_AGENT_CANDIDATES[@]} -eq 1 ]]; then
      RUN_AGENT_PATH="${RUN_AGENT_CANDIDATES[0]}"
      echo "   ✅ Found: ${RUN_AGENT_PATH}"
    else
      echo "   ⚠️  Multiple Hermes runtimes found:"
      for i in "${!RUN_AGENT_CANDIDATES[@]}"; do
        printf "     %d) %s\n" "$((i + 1))" "${RUN_AGENT_CANDIDATES[$i]}"
      done

      if [[ -r /dev/tty && -w /dev/tty ]]; then
        while true; do
          printf "Select runtime to check/patch [1-%d] or q to skip: " "${#RUN_AGENT_CANDIDATES[@]}" > /dev/tty
          read -r REPLY < /dev/tty || REPLY=""
          case "${REPLY}" in
            q|Q|quit|QUIT|skip|SKIP)
              RUN_AGENT_PATH=""
              break
              ;;
            ''|*[!0-9]*)
              echo "   Please enter a number or q."
              ;;
            *)
              if (( REPLY >= 1 && REPLY <= ${#RUN_AGENT_CANDIDATES[@]} )); then
                RUN_AGENT_PATH="${RUN_AGENT_CANDIDATES[$((REPLY - 1))]}"
                break
              else
                echo "   Choice out of range."
              fi
              ;;
          esac
        done
      else
        echo "   Non-interactive install cannot choose safely — runtime patch skipped."
        echo "   Re-run with --run-agent-path /path/to/run_agent.py"
        RUN_AGENT_PATH=""
      fi
    fi
  else
    echo "   Using explicit target: ${RUN_AGENT_PATH}"
  fi

  if [[ -n "${RUN_AGENT_PATH}" ]]; then
    echo "🔎 Checking Hermes runtime compatibility..."
    CHECK_OUTPUT="$(python3 "${PATCHER}" --check --path "${RUN_AGENT_PATH}" 2>&1 || true)"
    echo "${CHECK_OUTPUT}"

    if echo "${CHECK_OUTPUT}" | grep -q "fully compatible"; then
      echo "✅ Runtime already supports Hermes ARC overrides"
    else
      echo "⚠️  Hermes runtime may need ARC compatibility patching."
      echo "   Target: ${RUN_AGENT_PATH}"
      echo "   The patcher creates a timestamped backup before changing run_agent.py."
      echo "   If you have custom run_agent.py edits, review carefully or choose no."

      SHOULD_PATCH="no"
      case "${PATCH_RUNTIME}" in
        yes)
          SHOULD_PATCH="yes"
          ;;
        no)
          SHOULD_PATCH="no"
          ;;
        prompt)
          if [[ -r /dev/tty && -w /dev/tty ]]; then
            printf "Patch this Hermes runtime now? [y/N]: " > /dev/tty
            read -r REPLY < /dev/tty || REPLY=""
            # Accept answers that accidentally include composing characters from IMEs,
            # e.g. Thai keyboard input like "ัy".
            case "${REPLY}" in
              *y*|*Y*) SHOULD_PATCH="yes" ;;
              *) SHOULD_PATCH="no" ;;
            esac
          else
            echo "   Non-interactive install detected — skipping runtime patch."
            echo "   To force patching safely, include target path:"
            echo "   curl -fsSL ${REPO_RAW}/install.sh | bash -s -- --patch-runtime --run-agent-path ${RUN_AGENT_PATH}"
          fi
          ;;
      esac

      if [[ "${SHOULD_PATCH}" == "yes" ]]; then
        echo "🩹 Applying Hermes ARC runtime compatibility patch..."
        python3 "${PATCHER}" --patch --path "${RUN_AGENT_PATH}"
      else
        echo "ℹ️  Runtime patch skipped. You can run later:"
        echo "   python3 ${PATCHER} --patch --path ${RUN_AGENT_PATH}"
      fi
    fi
    echo ""
  fi
fi

# ── Ensure Hermes config.yaml has required ARC config ────────────────────────
if [[ "${CONFIGURE}" == true ]]; then
  echo "🧩 Ensuring Hermes config has topic_detect settings..."
  mkdir -p "$(dirname "${CONFIG_PATH}")"

  python3 - "${CONFIG_PATH}" <<'PY'
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except Exception as exc:
    print(f"❌ PyYAML is required to update config.yaml: {exc}")
    sys.exit(1)

path = Path(sys.argv[1]).expanduser()
backup = None
if path.exists():
    backup = path.with_suffix(path.suffix + ".arc-backup-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(path, backup)
    raw = yaml.safe_load(path.read_text()) or {}
else:
    raw = {}

if not isinstance(raw, dict):
    print("❌ config.yaml root must be a mapping/object")
    sys.exit(1)

changed = False

def ensure(key, value, obj=raw):
    global changed
    if key not in obj or obj[key] is None:
        obj[key] = value
        changed = True
    return obj[key]

plugins = raw.get("plugins")
if plugins is None:
    raw["plugins"] = {"enabled": ["topic_detect"]}
    changed = True
elif isinstance(plugins, dict):
    enabled = plugins.get("enabled")
    if enabled is None:
        plugins["enabled"] = ["topic_detect"]
        changed = True
    elif isinstance(enabled, list):
        if "topic_detect" not in enabled:
            enabled.append("topic_detect")
            changed = True
    else:
        print("⚠️  config.yaml plugins.enabled is not a list; leaving it unchanged.")
        print("   Run manually after install: hermes plugins enable topic_detect")
elif isinstance(plugins, list):
    # Older ARC installer versions wrote plugins as a plain list. Current Hermes
    # expects plugins.enabled, so migrate the legacy shape without dropping values.
    enabled = list(plugins)
    if "topic_detect" not in enabled:
        enabled.append("topic_detect")
    raw["plugins"] = {"enabled": enabled}
    changed = True
else:
    print("⚠️  config.yaml 'plugins' has an unsupported shape; leaving it unchanged.")
    print("   Run manually after install: hermes plugins enable topic_detect")

section = raw.get("topic_detect")
if section is None:
    section = {}
    raw["topic_detect"] = section
    changed = True
elif not isinstance(section, dict):
    print("❌ config.yaml 'topic_detect' must be a mapping/object. Please fix manually.")
    sys.exit(1)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_KEY = "${OPENROUTER_API_KEY}"

def target(model: str) -> dict:
    return {
        "provider": "openrouter",
        "model": model,
        "base_url": OPENROUTER_BASE,
        "api_key": OPENROUTER_KEY,
    }

ensure("enabled", True, section)
ensure("routing_mode", "hybrid", section)
ensure("inertia", 2, section)
ensure("min_confidence", 0.45, section)
ensure("agents_file", "~/.hermes/plugins/topic_detect/AGENTS.md", section)
ensure("default", target("openrouter/owl-alpha"), section)

semantic = section.get("semantic")
if semantic is None:
    semantic = {}
    section["semantic"] = semantic
    changed = True
elif not isinstance(semantic, dict):
    print("❌ topic_detect.semantic must be a mapping/object. Please fix manually.")
    sys.exit(1)
ensure("enabled", True, semantic)
ensure("provider", "openrouter", semantic)
ensure("model", "baidu/cobuddy:free", semantic)
ensure("min_confidence", 0.70, semantic)
ensure("base_url", OPENROUTER_BASE, semantic)
ensure("api_key", OPENROUTER_KEY, semantic)

signature = section.get("signature")
if signature is None:
    signature = {}
    section["signature"] = signature
    changed = True
elif not isinstance(signature, dict):
    print("❌ topic_detect.signature must be a mapping/object. Please fix manually.")
    sys.exit(1)
ensure("enabled", True, signature)

topics = section.get("topics")
if topics is None:
    topics = {}
    section["topics"] = topics
    changed = True
elif not isinstance(topics, dict):
    print("❌ topic_detect.topics must be a mapping/object. Please fix manually.")
    sys.exit(1)

ring = "inclusionai/ring-2.6-1t:free"
cobuddy = "baidu/cobuddy:free"
owl = "openrouter/owl-alpha"
required_topics = {
    "programming": ring,
    "finance": ring,
    "science": ring,
    "academia": ring,
    "marketing": cobuddy,
    "roleplay": cobuddy,
    "trivia": cobuddy,
    "translation": owl,
    "legal": owl,
    "health": owl,
    "seo": owl,
    "technology": owl,
}
for name, model in required_topics.items():
    current = topics.get(name)
    if current is None:
        topics[name] = target(model)
        changed = True
    elif isinstance(current, dict):
        # Preserve user choices; only fill missing required fields.
        for k, v in target(model).items():
            if k not in current or current[k] is None:
                current[k] = v
                changed = True
    else:
        print(f"❌ topic_detect.topics.{name} must be a mapping/object. Please fix manually.")
        sys.exit(1)

if changed:
    path.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"   ✅ Updated {path}")
    if backup:
        print(f"   🛟 Backup: {backup}")
else:
    print(f"   ✅ {path} already has required ARC config")
PY
  echo ""
else
  echo "ℹ️  Config update skipped (--no-config)"
  echo ""
fi

# ── Verify .env exists ─────────────────────────────────────────────────────
ENV_FILE="${HOME}/.hermes/.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "⚠️  No .env found at ${ENV_FILE}"
  echo "   Create one with your API keys:"
  echo "   echo 'OPENROUTER_API_KEY=<your-openrouter-key>' > ${ENV_FILE}"
  echo ""
fi

# ── Enable plugin ───────────────────────────────────────────────────────────
echo "🔧 Enabling plugin..."
hermes plugins enable topic_detect 2>&1 || true
echo ""

# ── Restart ─────────────────────────────────────────────────────────────────
if [[ "${RESTART}" == true ]]; then
  echo "🔄 Restarting Hermes gateway..."
  hermes gateway restart 2>&1 || true
  echo ""
fi

# ── Done ────────────────────────────────────────────────────────────────────
echo "─────────────────────────────────────────────"
echo "✅ Hermes ARC installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Set OPENROUTER_API_KEY in ~/.hermes/.env"
echo "  2. Restart/relaunch Hermes if it was running"
echo "  3. Run: hermes logs | grep topic_detect"
echo ""
echo "Docs: ${PLUGIN_DIR}/README.md"
echo "─────────────────────────────────────────────"
