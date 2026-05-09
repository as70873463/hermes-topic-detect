#!/bin/bash
# ============================================================================
# hermes-topic-detect installer — Universal (English keywords)
# Usage:
#   bash install.sh              (with backup)
#   bash install.sh --no-backup  (without backup)
# ============================================================================

set -e

REPO="ShockShoot/hermes-topic-detect"
BRANCH="main"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR=""
DO_BACKUP=true

for arg in "$@"; do
    case "$arg" in
        --no-backup) DO_BACKUP=false ;;
        --help|-h)
            echo "Usage: bash install.sh [--no-backup] [--agent-dir /path/to/hermes-agent]"
            exit 0 ;;
        --agent-dir)
            shift
            AGENT_DIR="$1" ;;
    esac
done

# Auto-detect Hermes agent directory
if [ -z "$AGENT_DIR" ]; then
    for d in /usr/local/lib/hermes-agent ~/.hermes/hermes-agent ~/hermes-agent; do
        if [ -f "$d/run_agent.py" ]; then
            AGENT_DIR="$d"
            break
        fi
    done
fi

if [ -z "$AGENT_DIR" ] || [ ! -f "$AGENT_DIR/run_agent.py" ]; then
    echo "❌ Could not find run_agent.py."
    echo "   Try: bash install.sh --agent-dir /path/to/hermes-agent"
    exit 1
fi

echo "============================================="
echo "  hermes-topic-detect installer"
echo "  Universal (English keywords)"
echo "============================================="
echo ""
echo "📍 Hermes Agent: $AGENT_DIR"
echo "📁 Plugin dir:   $SCRIPT_DIR"
echo ""

# ── Step 1: Backup ─────────────────────────────────────────────────
if [ "$DO_BACKUP" = true ]; then
    BACKUP_DIR="${HOME}/.hermes_backup_$(date +%Y%m%d_%H%M%S)"
    echo "💾 Backing up $AGENT_DIR to $BACKUP_DIR"
    cp -r "$AGENT_DIR" "$BACKUP_DIR"
    echo "   ✅ Backup done"
    echo ""
fi

# ── Step 2: Patch run_agent.py ─────────────────────────────────────
PATCH_FILE="$SCRIPT_DIR/agent_patch.diff"

if [ -f "$PATCH_FILE" ]; then
    echo "🔧 Patching run_agent.py..."

    # Check if already patched
    if grep -q "topic_detect: model override" "$AGENT_DIR/run_agent.py" 2>/dev/null; then
        echo "   ⚠️  Already patched — skipping"
    else
        cd "$AGENT_DIR"
        # Create backup copy for patch
        cp run_agent.py run_agent.py.bak
        if patch -p0 --forward < "$PATCH_FILE" 2>/dev/null; then
            echo "   ✅ Patch applied successfully"
            rm -f run_agent.py.bak
        else
            echo "   ⚠️  Standard patch failed, trying fallback method..."
            # Fallback: manual sed-based patching
            # This is a simpler approach that works on most versions

            # Check if already patched by looking for the pattern
            if grep -q "topic_detect.*model override" "$AGENT_DIR/run_agent.py"; then
                echo "   ✅ Already patched (fallback check)"
            else
                python3 "$SCRIPT_DIR/patch_agent.py" "$AGENT_DIR/run_agent.py"
                if [ $? -eq 0 ]; then
                    echo "   ✅ Patch applied via Python script"
                else
                    echo "   ❌ Patch failed! Check $PATCH_FILE manually."
                    echo "   Restore from backup: cp $BACKUP_DIR/run_agent.py $AGENT_DIR/"
                    exit 1
                fi
            fi
        fi
    fi
else
    echo "   ⚠️  No patch file found at $PATCH_FILE"
    echo "   Plugin will still inject context, but model override won't work"
fi

echo ""

# ── Step 3: Download/copy plugin files ─────────────────────────────
echo "📁 Setting up plugin files..."

# Plugin files are already in the same directory as this script
# Just verify they exist
FILES="__init__.py classifier.py config_reader.py plugin.yaml"
MISSING=0
for file in $FILES; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        echo "   ✅ $file exists"
    else
        echo "   ❌ Missing: $file"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo ""
    echo "   ⚠️  $MISSING file(s) missing. Downloading from GitHub..."
    for file in $FILES; do
        echo "   Downloading $file..."
        curl -fsSL "https://raw.githubusercontent.com/$REPO/$BRANCH/$file" -o "$SCRIPT_DIR/$file" || true
    done
fi

echo ""

# ── Step 4: Summary ────────────────────────────────────────────────
echo "============================================="
echo "  Installation complete! 🎉"
echo "============================================="
echo ""
echo "Next steps:"
echo ""
echo "  1. Add to ~/.hermes/config.yaml:"
echo ""
echo "     plugins:"
echo "       - topic_detect"
echo ""
echo "     topic_detect:"
echo "       enabled: true"
echo "       provider: openrouter"
echo "       default: owl-alpha"
echo "       topics:"
echo "         programming:"
echo "           model: inclusionai/ring-2.6-1t:free"
echo "         finance:"
echo "           model: inclusionai/ring-2.6-1t:free"
echo "         # ... add more as needed"
echo ""
echo "  2. Add API key to ~/.hermes/.env:"
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
echo "     Expected log: ✓ TOPIC: PROGRAMMING | MODEL: ring-2.6-1t"
echo ""
echo "============================================="
echo "  🔗 GitHub: https://github.com/ShockShoot/hermes-topic-detect"
echo "  🇹🇭 Thai:   replace 'main' with 'thai' in the URL"
echo "============================================="