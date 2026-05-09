#!/bin/bash
# install.sh — One-click installer for hermes-topic-detect plugin
# Usage: curl -sSL https://raw.githubusercontent.com/as70873463/hermes-topic-detect/main/install.sh | bash

set -e

REPO="as70873463/hermes-topic-detect"
PLUGIN_DIR="$HOME/.hermes/plugins/topic_detect"
TMP_DIR=$(mktemp -d)

echo "🧊 Installing hermes-topic-detect plugin..."
echo ""

# Check prerequisites
if [ ! -d "$HOME/.hermes" ]; then
    echo "❌ Error: ~/.hermes directory not found. Is Hermes Agent installed?"
    exit 1
fi

# Create plugins directory if needed
mkdir -p "$HOME/.hermes/plugins"

# Download latest release from GitHub
echo "📦 Downloading latest version..."
git clone --depth 1 "https://github.com/$REPO.git" "$TMP_DIR/repo" 2>/dev/null

# Remove old version if exists
if [ -d "$PLUGIN_DIR" ]; then
    echo "🗑️  Removing old version..."
    rm -rf "$PLUGIN_DIR"
fi

# Copy plugin files
echo "📂 Installing to $PLUGIN_DIR..."
cp -r "$TMP_DIR/repo" "$PLUGIN_DIR"

# Cleanup
rm -rf "$TMP_DIR"

echo ""
echo "✅ Plugin installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Make sure topic_detect is enabled in ~/.hermes/config.yaml:"
echo ""
echo "     topic_detect:"
echo "       enabled: true"
echo "       default: openrouter/owl-alpha"
echo "       topics:"
echo "         programming:"
echo "           model: inclusionai/ring-2.6-1t:free"
echo "         finance:"
echo "           model: inclusionai/ring-2.6-1t:free"
echo ""
echo "  2. Restart Hermes:"
echo "     sudo systemctl restart hermes"
echo ""
echo "  3. Verify it's working:"
echo "     hermes logs | grep topic_detect"
echo ""
echo "🧊 Done!"
