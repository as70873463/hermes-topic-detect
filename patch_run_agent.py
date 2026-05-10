#!/usr/bin/env python3
"""
Hermes ARC — run_agent.py compatibility checker & patcher

Checks whether run_agent.py properly handles runtime_override from
pre_llm_call hooks. Optionally applies a compatibility patch if needed.

Usage:
    python3 patch_run_agent.py --check     # Check only
    python3 patch_run_agent.py --patch     # Check and patch if needed
    python3 patch_run_agent.py --verify    # Verify patch applied correctly
"""

import argparse
import hashlib
import os
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime

RUN_AGENT_PATH = Path("/usr/local/lib/hermes-agent/run_agent.py")
BACKUP_SUFFIX = ".backup"


def find_run_agent() -> Path:
    """Locate run_agent.py."""
    if RUN_AGENT_PATH.exists():
        return RUN_AGENT_PATH

    # Fallback: search
    result = subprocess.run(
        ["find", "/usr/local", "-name", "run_agent.py", "-maxdepth", "3"],
        capture_output=True, text=True
    )
    paths = result.stdout.strip().splitlines()
    if paths:
        return Path(paths[0])

    print("❌ run_agent.py not found!")
    sys.exit(1)


def check_runtime_override_handling(content: str) -> dict:
    """Check if run_agent.py handles runtime_override from pre_llm_call hooks."""
    results = {}

    # Check 1: pre_llm_call hook exists
    results["has_pre_llm_call_hook"] = "pre_llm_call" in content

    # Check 2: runtime_override is read from hook result
    results["reads_runtime_override"] = bool(
        re.search(r'runtime_override', content)
    )

    # Check 3: model override from runtime_override
    results["applies_model_override"] = bool(
        re.search(r'_runtime_override\s*=\s*r\.get\(["\']runtime_override["\']\)', content)
        or re.search(r'runtime_override.*get.*model', content)
    )

    # Check 4: provider override
    results["applies_provider_override"] = bool(
        re.search(r'runtime_override.*get.*provider', content)
    )

    # Check 5: system_prompt override
    results["applies_system_prompt_override"] = bool(
        re.search(r'runtime_override.*get.*system_prompt', content)
    )

    # Check 6: response_suffix handling
    results["handles_response_suffix"] = bool(
        re.search(r'response_suffix', content)
    )

    return results


def needs_patch(results: dict) -> bool:
    """Determine if patching is needed."""
    required = [
        "has_pre_llm_call_hook",
        "reads_runtime_override",
        "applies_model_override",
        "applies_provider_override",
    ]
    return not all(results.get(k, False) for k in required)


def apply_patch(path: Path, content: str) -> str:
    """
    Apply compatibility patch to run_agent.py.

    The patch ensures that runtime_override from pre_llm_call hooks
    is properly applied to the agent's model, provider, base_url,
    api_key, and system_prompt.
    """
    # Find the pre_llm_call hook section
    hook_pattern = re.compile(
        r'(# Plugin hook: pre_llm_call.*?)(# Plugin hook: post_llm_call|$)',
        re.DOTALL
    )

    match = hook_pattern.search(content)
    if not match:
        print("⚠️  Could not locate pre_llm_call hook section — patch skipped")
        return content

    original_hook_section = match.group(1)

    # Check if already patched
    if "HERMES_ARC_PATCH" in content:
        print("ℹ️  Patch already applied — skipping")
        return content

    # Build patched section
    patched_section = original_hook_section.rstrip()
    patched_section += "\n\n"
    patched_section += "            # ── HERMES_ARC_PATCH: system_prompt override ──────────\n"
    patched_section += "            if isinstance(_runtime_override, dict):\n"
    patched_section += "                _new_system_prompt = _runtime_override.get(\"system_prompt\")\n"
    patched_section += "                if _new_system_prompt:\n"
    patched_section += "                    # Inject topic-specific system prompt\n"
    patched_section += "                    _existing_system = next(\n"
    patched_section += "                        (m for m in _messages if m.get(\"role\") == \"system\"),\n"
    patched_section += "                        None\n"
    patched_section += "                    )\n"
    patched_section += "                    if _existing_system:\n"
    patched_section += "                        _existing_system[\"content\"] = _new_system_prompt\n"
    patched_section += "                    else:\n"
    patched_section += "                        _messages.insert(\n"
    patched_section += "                            0,\n"
    patched_section += "                            {\"role\": \"system\", \"content\": _new_system_prompt}\n"
    patched_section += "                        )\n"
    patched_section += "                    logger.info(\n"
    patched_section += "                        \"hermes-arc: system_prompt injected from runtime_override\"\n"
    patched_section += "                    )\n"
    patched_section += "            # ── END HERMES_ARC_PATCH ──────────────────────────────\n"

    new_content = content.replace(original_hook_section, patched_section)
    return new_content


def backup_file(path: Path) -> Path:
    """Create a backup of the file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(f".py.{timestamp}{BACKUP_SUFFIX}")
    shutil.copy2(path, backup_path)
    print(f"📦 Backup created: {backup_path}")
    return backup_path


def verify_patch(path: Path) -> bool:
    """Verify that the patch is correctly applied."""
    content = path.read_text()

    checks = {
        "HERMES_ARC_PATCH marker": "HERMES_ARC_PATCH" in content,
        "system_prompt injection": "system_prompt injected from runtime_override" in content,
        "pre_llm_call hook intact": "pre_llm_call" in content,
        "runtime_override handling": "runtime_override" in content,
    }

    all_ok = True
    for name, ok in checks.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
        if not ok:
            all_ok = False

    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description="Hermes ARC — run_agent.py compatibility checker & patcher"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Check compatibility only (no changes)"
    )
    parser.add_argument(
        "--patch", action="store_true",
        help="Check and apply patch if needed"
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Verify patch is applied correctly"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force re-apply patch even if already present"
    )
    parser.add_argument(
        "--path", type=str, default=None,
        help="Custom path to run_agent.py"
    )

    args = parser.parse_args()

    if not any([args.check, args.patch, args.verify]):
        parser.print_help()
        sys.exit(0)

    # Locate run_agent.py
    run_agent_path = Path(args.path) if args.path else RUN_AGENT_PATH

    if not run_agent_path.exists():
        print(f"❌ run_agent.py not found at: {run_agent_path}")
        sys.exit(1)

    print(f"🔍 Target: {run_agent_path}")
    print(f"   Size: {run_agent_path.stat().st_size:,} bytes")
    print()

    content = run_agent_path.read_text()

    # ── Verify mode ──────────────────────────────────────────────────────
    if args.verify:
        print("🔎 Verifying patch...")
        if verify_patch(run_agent_path):
            print("\n✅ All checks passed — Hermes ARC patch is active")
            sys.exit(0)
        else:
            print("\n❌ Some checks failed — patch may not be applied correctly")
            sys.exit(1)

    # ── Check mode ───────────────────────────────────────────────────────
    print("🔎 Checking runtime_override handling...")
    results = check_runtime_override_handling(content)

    all_ok = True
    for name, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
        if not ok:
            all_ok = False

    print()

    if all_ok:
        print("✅ run_agent.py is fully compatible with Hermes ARC")
        print("   No patching needed — runtime_override is handled natively")
        sys.exit(0)

    # ── Patch mode ───────────────────────────────────────────────────────
    if args.patch:
        if not needs_patch(results):
            print("ℹ️  No critical issues found — patch not required")
            sys.exit(0)

        print("⚠️  Compatibility issues detected — patch needed")
        print()

        if "HERMES_ARC_PATCH" in content and not args.force:
            print("ℹ️  Patch marker already present — use --force to re-apply")
            sys.exit(0)

        # Backup
        backup_file(run_agent_path)

        # Apply patch
        new_content = apply_patch(run_agent_path, content)

        if new_content == content:
            print("⚠️  No changes made — patch could not be applied")
            sys.exit(1)

        run_agent_path.write_text(new_content)
        print("✅ Patch applied successfully!")
        print()

        # Verify
        print("🔎 Verifying...")
        if verify_patch(run_agent_path):
            print("\n✅ Hermes ARC patch verified — restart Hermes to activate")
            print("   hermes restart")
        else:
            print("\n⚠️  Verification incomplete — check manually")
    else:
        print("ℹ️  Run with --patch to apply the fix")


if __name__ == "__main__":
    import subprocess  # noqa: F811
    main()
