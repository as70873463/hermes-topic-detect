#!/bin/bash
# ============================================================================
# hermes-topic-detect installer — Universal (English keywords)
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-topic-detect/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-topic-detect/main/install.sh | bash -s -- --no-backup
# ============================================================================

set -e

REPO="ShockShoot/hermes-topic-detect"
BRANCH="main"
PLUGIN_DIR="${HOME}/.hermes/plugins/topic_detect"
AGENT_PY="$(find ~/.hermes -name 'run_agent.py' -path '*/hermes-agent/*' 2>/dev/null | head -1)"
PATCH_MARKER="# topic_detect: model override enabled"
DO_BACKUP=true

for arg in "$@"; do
    case "$arg" in
        --no-backup) DO_BACKUP=false ;;
    esac
done

echo "============================================="
echo "  hermes-topic-detect installer"
echo "  Universal version (English keywords)"
echo "============================================="
echo ""

if [ -z "$AGENT_PY" ]; then
    echo "❌ Could not find run_agent.py in ~/.hermes/"
    echo "   Is Hermes installed?"
    exit 1
fi

echo "📍 Found Hermes: $AGENT_PY"
echo ""

# ── Step 1: Backup ─────────────────────────────────────────────────
if [ "$DO_BACKUP" = true ]; then
    BACKUP_DIR="${HOME}/.hermes_backup_$(date +%Y%m%d_%H%M%S)"
    echo "💾 Backing up Hermes to: $BACKUP_DIR"
    cp -r ~/.hermes "$BACKUP_DIR"
    echo "   ✅ Backup done"
    echo ""
fi

# ── Step 2: Patch run_agent.py ─────────────────────────────────────
echo "🔧 Patching run_agent.py for model override support..."

if grep -q "$PATCH_MARKER" "$AGENT_PY" 2>/dev/null; then
    echo "   ⚠️  Already patched — skipping"
else
    # Use Python to apply patches cleanly
    python3 << PYEOF
import re

with open("$AGENT_PY", "r") as f:
    content = f.read()

# Patch 1: In pre_llm_call result loop, extract 'model' key
old1 = '''                if isinstance(r, dict) and r.get("context"):
                    _ctx_parts.append(str(r["context"]))'''

new1 = '''                if isinstance(r, dict):
                    # topic_detect: model override enabled
                    if r.get("model"):
                        _plugin_model_override = str(r["model"])
                        logger.info("pre_llm_call: model override -> %s", _plugin_model_override)
                    if r.get("context"):
                        _ctx_parts.append(str(r["context"]))'''

if old1 in content:
    content = content.replace(old1, new1)
    print("   ✅ Patch 1: model extraction in pre_llm_call loop")
else:
    print("   ⚠️  Patch 1 skipped (pattern not found)")

# Patch 2: Initialize _plugin_model_override before the loop
old2 = "            for r in _pre_results:"
new2 = "            _plugin_model_override: str | None = None\n            for r in _pre_results:"

# Only apply to the first occurrence (the one in pre_llm_call)
if old2 in content:
    content = content.replace(old2, new2, 1)
    print("   ✅ Patch 2: _plugin_model_override variable init")
else:
    print("   ⚠️  Patch 2 skipped")

# Patch 3: Apply model override before API call
old3 = '                    if self._force_ascii_payload:'
new3 = """                    # topic_detect: apply plugin model override
                    if '_plugin_model_override' in dir() and _plugin_model_override:
                        logger.info("Applying plugin model override: %s -> %s",
                                     api_kwargs.get('model'), _plugin_model_override)
                        api_kwargs['model'] = _plugin_model_override

                    if self._force_ascii_payload:"""

if 'Apply plugin model override' not in content and old3 in content:
    content = content.replace(old3, new3)
    print("   ✅ Patch 3: model override before API call")
else:
    print("   ⚠️  Patch 3 skipped (already present)")

with open("$AGENT_PY", "w") as f:
    f.write(content)

print("   ✅ run_agent.py patched successfully")
PYEOF
fi

echo ""

# ── Step 3: Install plugin files ───────────────────────────────────
echo "📁 Installing plugin files..."
mkdir -p "$PLUGIN_DIR"

FILES="__init__.py classifier.py config_reader.py plugin.yaml README.md install.sh"
for file in $FILES; do
    echo "   Downloading $file..."
    curl -fsSL "https://raw.githubusercontent.com/$REPO/$BRANCH/$file" -o "$PLUGIN_DIR/$file" 2>/dev/null || {
        echo "   ⚠️  Failed to download $file (may not exist in repo)"
    }
done
echo "   ✅ Plugin files installed"
echo ""

# ── Step 4: Summary ────────────────────────────────────────────────
echo "============================================="
echo "  Installation complete! 🎉"
echo "============================================="
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit ~/.hermes/config.yaml:"
echo ""
echo "     plugins:"
echo "       - topic_detect"
echo ""
echo "     topic_detect:"
echo "       enabled: true"
echo "       provider: openrouter        # or groq, together, etc."
echo "       default: owl-alpha"
echo "       topics:"
echo "         programming:"
echo "           model: inclusionai/ring-2.6-1t:free"
echo "         finance:"
echo "           model: inclusionai/ring-2.6-1t:free"
echo "         health:"
echo "           model: openrouter/owl-alpha"
echo "         roleplay:"
echo "           model: openrouter/cobuddy:free"
echo "         # ... add more topics as needed"
echo ""
echo "  2. Set API key in ~/.hermes/.env:"
echo ""
echo "     OPENROUTER_API_KEY=sk-or-v1-xxx"
echo ""
echo "  3. Restart Hermes:"
echo ""
echo "     sudo systemctl restart hermes"
echo ""
echo "  4. Verify:"
echo ""
echo "     hermes logs | grep topic_detect"
echo ""
echo "  5. Test:"
echo '     Send "ช่วยเขียนโค้ด Python" to Hermes'
echo "     Check logs for: ✓ TOPIC: PROGRAMMING | MODEL: ring-2.6-1t"
echo ""
echo "============================================="
echo "  🔗 GitHub: https://github.com/ShockShoot/hermes-topic-detect"
echo "  🇹🇭 Thai version: replace 'main' with 'thai' in URL"
echo "============================================="