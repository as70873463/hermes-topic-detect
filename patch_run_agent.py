#!/usr/bin/env python3
"""
Hermes ARC v1.2.0 — run_agent.py compatibility checker & patcher

Checks whether run_agent.py properly handles runtime_override from
pre_llm_call hooks, provider in transform_llm_output, and response
suffix rendering. Optionally applies a compatibility patch if needed.

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
import subprocess
import sys
from pathlib import Path
from datetime import datetime

RUN_AGENT_PATH = Path("/usr/local/lib/hermes-agent/run_agent.py")
BACKUP_SUFFIX = ".backup"


def _looks_like_hermes_run_agent(path: Path) -> bool:
    """Return True if path appears to be Hermes Agent's core run_agent.py."""
    try:
        if not path.is_file() or path.name != "run_agent.py":
            return False
        text = path.read_text(errors="ignore")[:250_000]
    except OSError:
        return False
    markers = ("class AIAgent", "pre_llm_call", "run_conversation")
    return sum(marker in text for marker in markers) >= 2


def find_run_agent_candidates() -> list[Path]:
    """Locate likely Hermes run_agent.py files across common install layouts."""
    candidates: list[Path] = []

    def add(path: Path) -> None:
        try:
            resolved = path.expanduser().resolve()
        except OSError:
            return
        if resolved not in candidates and _looks_like_hermes_run_agent(resolved):
            candidates.append(resolved)

    known = [
        RUN_AGENT_PATH,
        Path.home() / ".hermes/hermes-agent/run_agent.py",
        Path.home() / ".hermes/hermes_agent/run_agent.py",
        Path.home() / "hermes-agent/run_agent.py",
        Path.cwd() / "run_agent.py",
    ]
    for path in known:
        add(path)

    hermes_bin = shutil.which("hermes")
    if hermes_bin:
        try:
            exe = Path(hermes_bin).resolve()
            for parent in [exe.parent, *exe.parents]:
                add(parent / "run_agent.py")
                add(parent.parent / "run_agent.py")
        except OSError:
            pass

    roots = [
        Path("/usr/local/lib"),
        Path("/usr/local/share"),
        Path("/opt"),
        Path.home() / ".hermes",
        Path.home() / ".local",
    ]
    for root in roots:
        if not root.exists():
            continue
        try:
            for path in root.rglob("run_agent.py"):
                add(path)
        except (OSError, PermissionError):
            continue

    return sorted(candidates, key=lambda p: str(p))


def choose_run_agent_path(explicit_path: str | None = None, interactive: bool = True) -> Path:
    """Choose a run_agent.py path, prompting when multiple candidates exist."""
    if explicit_path:
        path = Path(explicit_path).expanduser().resolve()
        if not _looks_like_hermes_run_agent(path):
            print(f"❌ Not a valid Hermes run_agent.py: {path}")
            sys.exit(1)
        return path

    candidates = find_run_agent_candidates()
    if not candidates:
        print("❌ No Hermes run_agent.py candidates found.")
        print("   Pass --path /path/to/run_agent.py if Hermes is installed in a custom location.")
        sys.exit(1)

    if len(candidates) == 1:
        return candidates[0]

    print("⚠️  Multiple Hermes run_agent.py candidates found:")
    for i, path in enumerate(candidates, 1):
        print(f"  {i}. {path}")

    if interactive and sys.stdin.isatty():
        while True:
            choice = input(f"Select target [1-{len(candidates)}] or q to abort: ").strip().lower()
            if choice in {"q", "quit", "abort"}:
                sys.exit(1)
            if choice.isdigit() and 1 <= int(choice) <= len(candidates):
                return candidates[int(choice) - 1]

    print("❌ Ambiguous runtime target in non-interactive mode.")
    print("   Re-run with --path /path/to/run_agent.py")
    sys.exit(1)


def check_runtime_override_handling(content: str) -> dict:
    """Check if run_agent.py handles runtime_override from pre_llm_call hooks."""
    results = {}

    results["has_pre_llm_call_hook"] = "pre_llm_call" in content
    results["has_transform_llm_output_hook"] = "transform_llm_output" in content
    results["reads_runtime_override"] = "_runtime_override" in content and "runtime_override" in content
    results["uses_switch_model_runtime"] = bool(
        "switch_model(" in content
        and "_arc_resolve_provider_client" in content
        and "_hermes_arc_base_runtime" in content
    )
    results["handles_response_suffix"] = bool(
        "HERMES_ARC_RESPONSE_SUFFIX_PATCH" in content
        and "_arc_signature" in content
    )
    results["sends_provider_in_transform_hook"] = bool(
        re.search(r'transform_llm_output.*provider\s*=\s*self\.provider', content, re.DOTALL)
    )
    results["supports_topic_fallback_chain"] = "HERMES_ARC_TOPIC_FALLBACK_PATCH" in content

    return results


def needs_patch(results: dict) -> bool:
    """Determine if patching is needed."""
    required = [
        "has_pre_llm_call_hook",
        "has_transform_llm_output_hook",
        "reads_runtime_override",
        "uses_switch_model_runtime",
        "handles_response_suffix",
        "sends_provider_in_transform_hook",
        "supports_topic_fallback_chain",
    ]
    return not all(results.get(k, False) for k in required)


def apply_patch(path: Path, content: str) -> str:
    """
    Apply compatibility patch to run_agent.py v1.2.0.

    Three patch sections:
    1. HERMES_ARC_PATCH: runtime_override support (collect + apply via switch_model)
    2. HERMES_ARC_RESPONSE_SUFFIX_PATCH: render _arc_signature in final response
    3. transform_llm_output provider injection
    """
    new_content = content

    # ─── Patch 1A: Add _runtime_override init before pre_llm_call block ───
    # Run each sub-patch independently so partially patched cores can be repaired.
    if "_runtime_override = {}" not in new_content:
        init_old = '        _plugin_user_context = ""\n        try:\n'
        init_new = (
            '        _plugin_user_context = ""\n'
            '        # HERMES_ARC_PATCH: runtime_override support\n'
            '        _runtime_override = {}\n'
            '        try:\n'
        )
        if init_old not in new_content:
            print("⚠️  Could not locate pre_llm_call initialization — init patch skipped")
        else:
            new_content = new_content.replace(init_old, init_new, 1)

    # ─── Patch 1B: Collect runtime_override from pre_llm_call results ───
    if '_arc_ov = r.get("runtime_override")' not in new_content:
        loop_old = (
            '            for r in _pre_results:\n'
            '                if isinstance(r, dict) and r.get("context"):\n'
            '                    _ctx_parts.append(str(r["context"]))\n'
            '                elif isinstance(r, str) and r.strip():\n'
            '                    _ctx_parts.append(r)\n'
        )
        loop_new = (
            '            for r in _pre_results:\n'
            '                if isinstance(r, dict):\n'
            '                    if r.get("context"):\n'
            '                        _ctx_parts.append(str(r["context"]))\n'
            '                    _arc_ov = r.get("runtime_override")\n'
            '                    if isinstance(_arc_ov, dict):\n'
            '                        _runtime_override.update(_arc_ov)\n'
            '                elif isinstance(r, str) and r.strip():\n'
            '                    _ctx_parts.append(r)\n'
        )
        if loop_old not in new_content:
            print("⚠️  Could not locate pre_llm_call result loop — collect patch skipped")
        else:
            new_content = new_content.replace(loop_old, loop_new, 1)

    # ─── Patch 1C: Apply runtime overrides after context assembly ───
    if "_arc_resolve_provider_client" not in new_content:
        ctx_old = (
            '            if _ctx_parts:\n'
            '                _plugin_user_context = "\\n\\n".join(_ctx_parts)\n'
        )
        runtime_block = '''            if _ctx_parts:
                _plugin_user_context = "\\n\\n".join(_ctx_parts)

            # HERMES_ARC_PATCH: apply runtime routing overrides from plugins.
            # Use Hermes' own switch_model() instead of mutating attributes
            # directly — preserves provider-specific api_mode, OAuth, headers,
            # context-compressor metadata, and client rebuild logic.
            if isinstance(_runtime_override, dict) and _runtime_override:
                _arc_restore_main = bool(_runtime_override.get("restore_main"))
                _arc_model = _runtime_override.get("model")
                _arc_provider = _runtime_override.get("provider")
                _arc_base_url = _runtime_override.get("base_url")
                _arc_api_key = _runtime_override.get("api_key")
                _arc_api_mode = _runtime_override.get("api_mode")

                if not hasattr(self, "_hermes_arc_base_runtime"):
                    self._hermes_arc_base_runtime = {
                        "model": getattr(self, "model", ""),
                        "provider": getattr(self, "provider", ""),
                        "base_url": getattr(self, "base_url", ""),
                        "api_key": getattr(self, "api_key", ""),
                        "api_mode": getattr(self, "api_mode", ""),
                    }

                if _arc_restore_main:
                    _arc_base = getattr(self, "_hermes_arc_base_runtime", None) or {}
                    _base_model = _arc_base.get("model")
                    _base_provider = _arc_base.get("provider")
                    if _base_model and _base_provider:
                        if hasattr(self, "switch_model"):
                            self.switch_model(
                                _base_model,
                                _base_provider,
                                api_key=_arc_base.get("api_key", ""),
                                base_url=_arc_base.get("base_url", ""),
                                api_mode=_arc_base.get("api_mode", ""),
                            )
                        else:
                            self.model = str(_base_model)
                            self.provider = str(_base_provider)
                            if _arc_base.get("base_url"):
                                self.base_url = str(_arc_base.get("base_url")).rstrip("/")
                            if _arc_base.get("api_key"):
                                self.api_key = str(_arc_base.get("api_key"))
                        logger.info(
                            "hermes-arc: restored main runtime provider=%s model=%s",
                            getattr(self, "provider", ""),
                            getattr(self, "model", ""),
                        )
                elif _arc_model or _arc_provider or _arc_base_url or _arc_api_key:
                    _target_provider = str(_arc_provider or getattr(self, "provider", "") or "auto")
                    _target_model = str(_arc_model or getattr(self, "model", ""))
                    _resolved_model = _target_model
                    _resolved_api_key = str(_arc_api_key or "")
                    _resolved_base_url = str(_arc_base_url or "")
                    _resolved_api_mode = str(_arc_api_mode or "")

                    try:
                        from agent.auxiliary_client import resolve_provider_client as _arc_resolve_provider_client
                        _arc_client, _arc_client_model = _arc_resolve_provider_client(
                            _target_provider,
                            model=_target_model,
                            raw_codex=True,
                            explicit_base_url=_resolved_base_url or None,
                            explicit_api_key=_resolved_api_key or None,
                            api_mode=_resolved_api_mode or None,
                            main_runtime=getattr(self, "_primary_runtime", None),
                        )
                        if _arc_client is not None:
                            _resolved_model = str(_arc_client_model or _target_model)
                            _resolved_api_key = str(getattr(_arc_client, "api_key", "") or _resolved_api_key)
                            _resolved_base_url = str(getattr(_arc_client, "base_url", "") or _resolved_base_url).rstrip("/")
                    except Exception as _arc_resolve_error:
                        logger.debug("hermes-arc: provider resolution skipped: %s", _arc_resolve_error)

                    if not _resolved_api_mode:
                        try:
                            from hermes_cli.providers import determine_api_mode as _arc_determine_api_mode
                            _resolved_api_mode = _arc_determine_api_mode(_target_provider, _resolved_base_url)
                        except Exception:
                            _resolved_api_mode = getattr(self, "api_mode", "")

                    if hasattr(self, "switch_model"):
                        self.switch_model(
                            _resolved_model,
                            _target_provider,
                            api_key=_resolved_api_key,
                            base_url=_resolved_base_url,
                            api_mode=_resolved_api_mode,
                        )
                    else:
                        self.model = str(_resolved_model)
                        self.provider = str(_target_provider)
                        if _resolved_base_url:
                            self.base_url = _resolved_base_url
                        if _resolved_api_key:
                            self.api_key = _resolved_api_key

                    logger.info(
                        "hermes-arc: runtime_override applied provider=%s model=%s api_mode=%s",
                        getattr(self, "provider", ""),
                        getattr(self, "model", ""),
                        getattr(self, "api_mode", ""),
                    )
'''
        if ctx_old not in new_content:
            print("⚠️  Could not locate context assembly — patch skipped")
            return content
        new_content = new_content.replace(ctx_old, runtime_block, 1)

    # ─── Patch 2: Add provider to transform_llm_output hook call ───
    if "HERMES_ARC_TRANSFORM_PROVIDER_PATCH" not in new_content:
        # Find the transform_llm_output invoke_hook call and add provider=self.provider
        old_hook = '''                _transform_results = _invoke_hook(
                    "transform_llm_output",
                    response_text=final_response,
                    session_id=self.session_id or "",
                    model=self.model,
                    platform=getattr(self, "platform", None) or "",
                )'''
        new_hook = '''                # HERMES_ARC_TRANSFORM_PROVIDER_PATCH: add provider for signature rebuild
                _transform_results = _invoke_hook(
                    "transform_llm_output",
                    response_text=final_response,
                    session_id=self.session_id or "",
                    model=self.model,
                    provider=self.provider,
                    platform=getattr(self, "platform", None) or "",
                )'''
        if old_hook in new_content:
            new_content = new_content.replace(old_hook, new_hook, 1)
        else:
            print("⚠️  Could not locate transform_llm_output hook call — provider patch skipped")

    # ─── Patch 3: Response suffix rendering (signature append) ───
    if "_arc_signature" not in new_content:
        # Insert before post_llm_call. Older patcher versions required the exact
        # transform warning line immediately before this marker; newer Hermes
        # cores may change spacing/comments, so anchor on the stable next hook.
        suffix_marker = '        # Plugin hook: post_llm_call'
        suffix_block = '''        # HERMES_ARC_RESPONSE_SUFFIX_PATCH: render ARC signature from
        # _runtime_override (structured _arc_signature dict) and the final
        # model/provider after any fallback occurred.
        if final_response and not interrupted:
            try:
                _arc_sig = (_runtime_override or {}).get("_arc_signature")
                if isinstance(_arc_sig, dict):
                    try:
                        from hermes_cli.plugins import invoke_hook as _arc_inv
                        _arc_final_sig_results = _arc_inv(
                            "transform_llm_output",
                            response_text="",
                            session_id=self.session_id or "",
                            model=self.model,
                            provider=self.provider,
                            platform=getattr(self, "platform", None) or "",
                            _arc_finalize=_arc_sig,
                        )
                        for _arc_hr in _arc_final_sig_results:
                            if isinstance(_arc_hr, str) and _arc_hr:
                                final_response = final_response.rstrip() + "\\n\\n" + _arc_hr
                                break
                    except Exception:
                        _routed = _arc_sig.get("routed_model", "")
                        _routed_p = _arc_sig.get("routed_provider", "")
                        _final_m = self.model or ""
                        _final_p = self.provider or ""
                        _topic = _arc_sig.get("topic", "")
                        _short = lambda m: m.split("/")[-1] if "/" in m else m
                        if _short(_final_m) == _short(_routed) and _final_p == _routed_p:
                            _arc_suffix = f"- {_short(_final_m)} [{_topic}]"
                        else:
                            _arc_suffix = f"- {_short(_final_m)} [{_topic} | routed: {_short(_routed)}]"
                        if _arc_suffix:
                            final_response = final_response.rstrip() + "\\n\\n" + _arc_suffix
            except Exception:
                logger.debug("hermes-arc: response suffix render failed")

'''
        if suffix_marker in new_content:
            new_content = new_content.replace(suffix_marker, suffix_block + suffix_marker, 1)
        else:
            print("⚠️  Could not locate post_llm_call hook boundary — suffix patch skipped")

    # ─── Patch 5: topic-scoped fallback chains ───
    if "HERMES_ARC_TOPIC_FALLBACK_PATCH" not in new_content:
        modern_old = '''            self.switch_model(new_model, new_provider, api_key=api_key, base_url=base_url, api_mode=api_mode)
            # ``switch_model`` deliberately prunes fallback entries for
'''
        modern_new = '''            self.switch_model(new_model, new_provider, api_key=api_key, base_url=base_url, api_mode=api_mode)
            # HERMES_ARC_TOPIC_FALLBACK_PATCH: allow router plugins to scope
            # the fallback chain for this runtime override before falling back
            # to the agent's global chain.
            _override_fallback_chain = runtime_override.get("fallback_chain")
            if isinstance(_override_fallback_chain, list):
                fallback_chain = [
                    f for f in _override_fallback_chain
                    if isinstance(f, dict) and f.get("provider") and f.get("model")
                ]
                fallback_model = fallback_chain[0] if fallback_chain else None
                fallback_index = 0
            # ``switch_model`` deliberately prunes fallback entries for
'''
        legacy_old = '''                    logger.info(
                        "hermes-arc: runtime_override applied provider=%s model=%s api_mode=%s",
'''
        legacy_new = '''                    # HERMES_ARC_TOPIC_FALLBACK_PATCH: optional topic-scoped
                    # fallback chain supplied by topic_detect runtime_override.
                    _arc_fb_chain_raw = _runtime_override.get("fallback_chain")
                    if isinstance(_arc_fb_chain_raw, list):
                        _arc_fb_chain = [
                            f for f in _arc_fb_chain_raw
                            if isinstance(f, dict) and f.get("provider") and f.get("model")
                        ]
                        self._fallback_chain = _arc_fb_chain
                        self._fallback_model = _arc_fb_chain[0] if _arc_fb_chain else None
                        self._fallback_index = 0
                        self._fallback_activated = False
                        logger.info(
                            "hermes-arc: topic fallback chain loaded entries=%d",
                            len(_arc_fb_chain),
                        )

                    logger.info(
                        "hermes-arc: runtime_override applied provider=%s model=%s api_mode=%s",
'''
        if modern_old in new_content:
            new_content = new_content.replace(modern_old, modern_new, 1)
        elif legacy_old in new_content:
            new_content = new_content.replace(legacy_old, legacy_new, 1)
        else:
            print("⚠️  Could not locate runtime override apply block — topic fallback patch skipped")

    # ─── Patch 4: system_prompt support (pre_llm_call → inject before context assembly) ───
    if "HERMES_ARC_SYSTEM_PROMPT_PATCH" not in new_content:
        # Add _plugin_system_prompt init alongside _runtime_override
        old_runtime_init = (
            '        # HERMES_ARC_PATCH: runtime_override support\n'
            '        _runtime_override = {}\n'
        )
        new_runtime_init = (
            '        # HERMES_ARC_PATCH: runtime_override support\n'
            '        _runtime_override = {}\n'
            '        _plugin_system_prompt = ""\n'
        )
        if old_runtime_init in new_content:
            new_content = new_content.replace(old_runtime_init, new_runtime_init, 1)

        # Add system_prompt extraction from runtime_override, after context assembly
        old_ctx_end = '                    logger.info(\n                        "hermes-arc: runtime_override applied provider=%s model=%s api_mode=%s",\n'
        new_ctx_end = '''                    logger.info(
                        "hermes-arc: runtime_override applied provider=%s model=%s api_mode=%s",
'''
        # We need to inject system_prompt capture right after the runtime block
        # Find the end of the runtime block and inject system_prompt handling
        inject_point = '                    logger.info(\n                        "hermes-arc: runtime_override applied provider=%s model=%s api_mode=%s",\n                        getattr(self, "provider", ""),\n                        getattr(self, "model", ""),\n                        getattr(self, "api_mode", ""),\n                    )\n'
        if inject_point in new_content:
            after_inject = '''                    logger.info(
                        "hermes-arc: runtime_override applied provider=%s model=%s api_mode=%s",
                        getattr(self, "provider", ""),
                        getattr(self, "model", ""),
                        getattr(self, "api_mode", ""),
                    )

                # HERMES_ARC_SYSTEM_PROMPT_PATCH: capture system prompt override
                _arc_sys = _runtime_override.get("system_prompt")
                if _arc_sys:
                    _plugin_system_prompt = str(_arc_sys)
                    _ctx_parts.append(_plugin_system_prompt)
'''
            new_content = new_content.replace(inject_point, after_inject, 1)
        else:
            print("⚠️  Could not locate runtime override log line — system prompt patch skipped")

    return new_content


def verify_patch(content: str) -> dict:
    """Verify all ARC patches are correctly applied."""
    checks = {}

    checks["HERMES_ARC_PATCH marker"] = "HERMES_ARC_PATCH: runtime_override support" in content
    checks["_runtime_override init"] = "_runtime_override = {}" in content
    checks["runtime_override collect"] = '_arc_ov = r.get("runtime_override")' in content
    checks["switch_model call"] = "switch_model(" in content and "_arc_resolve_provider_client" in content
    checks["_hermes_arc_base_runtime"] = "_hermes_arc_base_runtime" in content
    checks["HERMES_ARC_RESPONSE_SUFFIX_PATCH"] = "HERMES_ARC_RESPONSE_SUFFIX_PATCH" in content
    checks["_arc_signature"] = "_arc_signature" in content
    checks["HERMES_ARC_TRANSFORM_PROVIDER_PATCH"] = "HERMES_ARC_TRANSFORM_PROVIDER_PATCH" in content
    checks["provider=self.provider in transform hook"] = bool(
        re.search(r'transform_llm_output[\s\S]{0,200}provider\s*=\s*self\.provider', content)
    )
    checks["HERMES_ARC_SYSTEM_PROMPT_PATCH"] = "HERMES_ARC_SYSTEM_PROMPT_PATCH" in content
    checks["HERMES_ARC_TOPIC_FALLBACK_PATCH"] = "HERMES_ARC_TOPIC_FALLBACK_PATCH" in content

    return checks


def main():
    parser = argparse.ArgumentParser(description="Hermes ARC run_agent.py patcher")
    parser.add_argument("--check", action="store_true", help="Check only")
    parser.add_argument("--patch", action="store_true", help="Check and patch if needed")
    parser.add_argument("--verify", action="store_true", help="Verify patch applied")
    parser.add_argument("--path", type=str, help="Explicit path to run_agent.py")
    args = parser.parse_args()

    if not any([args.check, args.patch, args.verify]):
        parser.print_help()
        sys.exit(1)

    path = choose_run_agent_path(args.path)
    content = path.read_text(encoding="utf-8", errors="ignore")

    if args.check:
        results = check_runtime_override_handling(content)
        print("🔍 Hermes ARC compatibility check:")
        for key, val in results.items():
            status = "✅" if val else "❌"
            print(f"  {status} {key}")
        if needs_patch(results):
            print("\n⚠️  Patch needed. Run: python3 patch_run_agent.py --patch")
        else:
            print("\n✅ All checks passed — no patch needed.")

    if args.patch:
        new_content = apply_patch(path, content)
        if new_content == content:
            print("✅ Already patched or patch could not be applied — no changes made.")
        else:
            backup = path.with_suffix(path.suffix + BACKUP_SUFFIX)
            if not backup.exists():
                shutil.copy2(path, backup)
                print(f"📦 Backup created: {backup}")
            path.write_text(new_content, encoding="utf-8")
            content = new_content
            print("✅ Patch applied successfully.")

    if args.verify:
        # Re-read after --patch so `--patch --verify` verifies the file on disk,
        # not the pre-patch content captured at startup.
        content = path.read_text(encoding="utf-8", errors="ignore")
        checks = verify_patch(content)
        print("🔍 Hermes ARC patch verification:")
        all_ok = True
        for key, val in checks.items():
            status = "✅" if val else "❌"
            print(f"  {status} {key}")
            if not val:
                all_ok = False
        if all_ok:
            print("\n✅ All patches verified successfully.")
        else:
            print("\n❌ Some patches missing or incomplete.")


if __name__ == "__main__":
    main()
