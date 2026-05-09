#!/usr/bin/env python3
"""
patch_agent.py — Fallback patcher for run_agent.py
Applies topic_detect model override support when standard patch fails.
Usage: python3 patch_agent.py /path/to/run_agent.py
"""

import sys
import os

if len(sys.argv) < 2:
    print("Usage: python3 patch_agent.py /path/to/run_agent.py")
    sys.exit(1)

filepath = sys.argv[1]

if not os.path.isfile(filepath):
    print(f"❌ File not found: {filepath}")
    sys.exit(1)

with open(filepath, "r") as f:
    content = f.read()

# Check if already patched
if "topic_detect: model override" in content:
    print("   Already patched — skipping")
    sys.exit(0)

patches_applied = 0

# ── Patch 1: Extract 'model' key from pre_llm_call hook results ──
old1 = '''                if isinstance(r, dict) and r.get("context"):
                    _ctx_parts.append(str(r["context"]))'''

new1 = '''                if isinstance(r, dict):
                    # Allow plugins to override the model for this turn
                    if r.get("model"):
                        _plugin_model_override = str(r["model"])
                        logger.info("pre_llm_call: model override -> %s", _plugin_model_override)
                    if r.get("context"):
                        _ctx_parts.append(str(r["context"]))'''

if old1 in content:
    content = content.replace(old1, new1)
    patches_applied += 1
    print("   ✅ Patch 1: model extraction in pre_llm_call loop")
else:
    # Try alternate pattern (single-space indent)
    old1b = '''            if isinstance(r, dict) and r.get("context"):
                _ctx_parts.append(str(r["context"]))'''
    new1b = '''            if isinstance(r, dict):
                # Allow plugins to override the model for this turn
                if r.get("model"):
                    _plugin_model_override = str(r["model"])
                    logger.info("pre_llm_call: model override -> %s", _plugin_model_override)
                if r.get("context"):
                    _ctx_parts.append(str(r["context"]))'''
    if old1b in content:
        content = content.replace(old1b, new1b)
        patches_applied += 1
        print("   ✅ Patch 1 (alt): model extraction in pre_llm_call loop")
    else:
        print("   ⚠️  Patch 1 skipped (pattern not found)")

# ── Patch 2: Initialize _plugin_model_override variable ──
old2 = "            for r in _pre_results:"
new2 = "            _plugin_model_override: str | None = None\n            for r in _pre_results:"

if old2 in content:
    content = content.replace(old2, new2, 1)
    patches_applied += 1
    print("   ✅ Patch 2: _plugin_model_override variable init")
else:
    print("   ⚠️  Patch 2 skipped")

# ── Patch 3: Apply model override before API call ──
old3 = '                    if self._force_ascii_payload:'
new3 = """                    # Apply plugin model override if set by pre_llm_call hook
                    if '_plugin_model_override' in dir() and _plugin_model_override:
                        logger.info("Applying plugin model override: %s -> %s",
                                     api_kwargs.get('model'), _plugin_model_override)
                        api_kwargs['model'] = _plugin_model_override

                    if self._force_ascii_payload:"""

if old3 in content and "Apply plugin model override" not in content:
    content = content.replace(old3, new3)
    patches_applied += 1
    print("   ✅ Patch 3: model override before API call")
else:
    print("   ⚠️  Patch 3 skipped (already present or pattern not found)")

# Write back
if patches_applied > 0:
    with open(filepath, "w") as f:
        f.write(content)
    print(f"\n   ✅ Applied {patches_applied} patch(es) to {filepath}")
else:
    print(f"\n   ❌ No patches applied — file may already be patched or version mismatch")
    sys.exit(1)