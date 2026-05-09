#!/bin/bash
# hermes-topic-detect installer
# Usage: curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-topic-detect/main/install.sh | bash

set -e

REPO="ShockShoot/hermes-topic-detect"
PLUGIN_DIR="$HOME/.hermes/plugins/topic_detect"
TMP_DIR=$(mktemp -d)

echo "🧊 Installing hermes-topic-detect plugin..."
echo ""

if [ ! -d "$HOME/.hermes" ]; then
    echo "❌ Error: ~/.hermes directory not found. Is Hermes Agent installed?"
    exit 1
fi

mkdir -p "$HOME/.hermes/plugins"

echo "📦 Downloading latest version..."
git clone --depth 1 "https://github.com/$REPO.git" "$TMP_DIR/repo" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Failed to clone repository. Check your internet connection."
    rm -rf "$TMP_DIR"
    exit 1
fi

if [ -d "$PLUGIN_DIR" ]; then
    echo "🗑️  Removing old version..."
    rm -rf "$PLUGIN_DIR"
fi

echo "📂 Installing to $PLUGIN_DIR..."
cp -r "$TMP_DIR/repo" "$PLUGIN_DIR"

rm -rf "$TMP_DIR"

echo ""
echo "✅ Plugin files installed!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  IMPORTANT — You MUST do these steps manually:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Enable the plugin in ~/.hermes/config.yaml:"
echo ""
echo "    plugins:"
echo "      - topic_detect"
echo ""
echo "2️⃣  Add topic_detect config in the same file:"
echo ""
echo "    topic_detect:"
echo "      enabled: true"
echo "      provider: openrouter"
echo "      default: owl-alpha"
echo "      topics:"
echo "        programming:"
echo "          model: ring-2.6-1t:free"
echo "        finance:"
echo "          model: ring-2.6-1t:free"
echo ""
echo "3️⃣  Restart Hermes:"
echo ""
echo "    sudo systemctl restart hermes"
echo ""
echo "4️⃣  Verify it's working:"
echo ""
echo "    hermes logs | grep topic_detect"
echo ""
echo "    You should see: topic_detect plugin loaded"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 Full docs: https://github.com/ShockShoot/hermes-topic-detect"
echo ""
echo "🧊 Done!"