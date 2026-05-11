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

    # Known install/source layouts.
    known = [
        RUN_AGENT_PATH,
        Path.home() / ".hermes/hermes-agent/run_agent.py",
        Path.home() / ".hermes/hermes_agent/run_agent.py",
        Path.home() / "hermes-agent/run_agent.py",
        Path.cwd() / "run_agent.py",
    ]
    for path in known:
        add(path)

    # Infer from the hermes executable/symlink/venv path when possible.
    hermes_bin = shutil.which("hermes")
    if hermes_bin:
        try:
            exe = Path(hermes_bin).resolve()
            for parent in [exe.parent, *exe.parents]:
                add(parent / "run_agent.py")
                add(parent.parent / "run_agent.py")
        except OSError:
            pass

    # Bounded fallback search. Avoid scanning the whole filesystem.
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
    results["reads_runtime_override"] = "runtime_override" in content
    results["applies_model_override"] = bool(
        "_arc_model" in content
        or re.search(r'runtime_override.*model', content, re.DOTALL)
    )
    results["applies_provider_override"] = bool(
        "_arc_provider" in content
        or re.search(r'runtime_override.*provider', content, re.DOTALL)
    )
    results["applies_system_prompt_override"] = bool(
        "plugin_system_prompt" in content
        and "HERMES_ARC_SYSTEM_PROMPT_PATCH" in content
    )
    results["uses_switch_model_runtime"] = bool(
        "switch_model(" in content
        and "_arc_resolve_provider_client" in content
        and "restore_main" in content
    )
    results["handles_response_suffix"] = bool(
        "HERMES_ARC_RESPONSE_SUFFIX_PATCH" in content
        or re.search(r'response_suffix', content)
    )
    return results


def needs_patch(results: dict) -> bool:
    """Determine if patching is needed."""
    required = [
        "has_pre_llm_call_hook",
        "reads_runtime_override",
        "applies_model_override",
        "applies_provider_override",
        "applies_system_prompt_override",
        "uses_switch_model_runtime",
        "handles_response_suffix",
    ]
    return not all(results.get(k, False) for k in required)


def apply_patch(path: Path, content: str) -> str:
    """
    Apply compatibility patch to run_agent.py.

    The patch ensures that runtime_override from pre_llm_call hooks
    is applied to model/provider/base_url/api_key, system_prompt, and
    response_suffix without renaming the topic_detect plugin.
    """
    if (
        "HERMES_ARC_PATCH" in content
        and "HERMES_ARC_RESPONSE_SUFFIX_PATCH" in content
        and "_arc_resolve_provider_client" in content
        and "restore_main" in content
    ):
        print("ℹ️  Patch already applied — skipping")
        return content

    new_content = content

    if "HERMES_ARC_PATCH: runtime_override support" not in new_content:
        init_old = '        _plugin_user_context = ""\n        try:\n'
        init_new = (
            '        _plugin_user_context = ""\n'
            '        # HERMES_ARC_PATCH: runtime_override support\n'
            '        _runtime_override = {}\n'
            '        _plugin_system_prompt = ""\n'
            '        try:\n'
        )
        if init_old not in new_content:
            print("⚠️  Could not locate pre_llm_call initialization — patch skipped")
            return content
        new_content = new_content.replace(init_old, init_new, 1)

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
            '                    _arc_override = r.get("runtime_override")\n'
            '                    if isinstance(_arc_override, dict):\n'
            '                        _runtime_override.update(_arc_override)\n'
            '                elif isinstance(r, str) and r.strip():\n'
            '                    _ctx_parts.append(r)\n'
        )
        if loop_old not in new_content:
            print("⚠️  Could not locate pre_llm_call result loop — patch skipped")
            return content
        new_content = new_content.replace(loop_old, loop_new, 1)

        ctx_old = (
            '            if _ctx_parts:\n'
            '                _plugin_user_context = "\\n\\n".join(_ctx_parts)\n'
        )
        runtime_block = """            if _ctx_parts:
                _plugin_user_context = "\\n\\n".join(_ctx_parts)

            # HERMES_ARC_PATCH: apply runtime routing overrides from plugins.
            # Use Hermes' own provider resolver + switch_model() instead of
            # mutating self.provider/self.model directly.  This preserves
            # provider-specific api_mode, OAuth/subscriber credentials,
            # headers, context-compressor metadata, and client rebuild logic.
            if isinstance(_runtime_override, dict) and _runtime_override:
                _arc_restore_main = bool(_runtime_override.get("restore_main"))
                _arc_model = _runtime_override.get("model")
                _arc_provider = _runtime_override.get("provider")
                _arc_base_url = _runtime_override.get("base_url")
                _arc_api_key = _runtime_override.get("api_key")
                _arc_api_mode = _runtime_override.get("api_mode")
                _arc_system_prompt = _runtime_override.get("system_prompt")

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
                        if hasattr(self, "_client_kwargs"):
                            if _resolved_base_url:
                                self._client_kwargs["base_url"] = self.base_url
                            if _resolved_api_key:
                                self._client_kwargs["api_key"] = self.api_key
                        if (_resolved_base_url or _resolved_api_key) and hasattr(self, "_replace_primary_openai_client"):
                            try:
                                if hasattr(self, "_apply_client_headers_for_base_url"):
                                    self._apply_client_headers_for_base_url(self.base_url)
                                self._replace_primary_openai_client(reason="hermes_arc_runtime_override")
                            except Exception as _arc_client_error:
                                logger.debug("hermes-arc: client refresh skipped: %s", _arc_client_error)

                    logger.info(
                        "hermes-arc: runtime_override applied provider=%s model=%s api_mode=%s",
                        getattr(self, "provider", ""),
                        getattr(self, "model", ""),
                        getattr(self, "api_mode", ""),
                    )

                if _arc_system_prompt:
                    _plugin_system_prompt = str(_arc_system_prompt)
"""
        if ctx_old not in new_content:
            print("⚠️  Could not locate context assembly — patch skipped")
            return content
        new_content = new_content.replace(ctx_old, runtime_block, 1)

    # Upgrade older ARC patches that mutated self.provider/self.model directly.
    # Older installers left the HERMES_ARC_PATCH marker in place, which made
    # --patch skip even though switch_model-compatible routing was missing.
    if (
        "HERMES_ARC_PATCH: apply runtime routing overrides from plugins." in new_content
        and "_arc_resolve_provider_client" not in new_content
    ):
        upgrade_pattern = re.compile(
            r'(?P<block>^[ \t]*# HERMES_ARC_PATCH: apply runtime routing overrides from plugins\.\n'
            r'(?:(?!^[ \t]{8}except Exception as exc:).+\n|\n)*)',
            re.MULTILINE,
        )
        upgrade_match = upgrade_pattern.search(new_content)
        if upgrade_match:
            old_block = upgrade_match.group("block")
            indent = re.match(r'^[ \t]*', old_block).group(0)
            upgrade_block = f'''{indent}# HERMES_ARC_PATCH: apply runtime routing overrides from plugins.
{indent}# Use Hermes' own provider resolver + switch_model() instead of
{indent}# mutating self.provider/self.model directly.  This preserves
{indent}# provider-specific api_mode, OAuth/subscriber credentials,
{indent}# headers, context-compressor metadata, and client rebuild logic.
{indent}if isinstance(_runtime_override, dict) and _runtime_override:
{indent}    _arc_restore_main = bool(_runtime_override.get("restore_main"))
{indent}    _arc_model = _runtime_override.get("model")
{indent}    _arc_provider = _runtime_override.get("provider")
{indent}    _arc_base_url = _runtime_override.get("base_url")
{indent}    _arc_api_key = _runtime_override.get("api_key")
{indent}    _arc_api_mode = _runtime_override.get("api_mode")
{indent}    _arc_system_prompt = _runtime_override.get("system_prompt")

{indent}    if not hasattr(self, "_hermes_arc_base_runtime"):
{indent}        self._hermes_arc_base_runtime = {{
{indent}            "model": getattr(self, "model", ""),
{indent}            "provider": getattr(self, "provider", ""),
{indent}            "base_url": getattr(self, "base_url", ""),
{indent}            "api_key": getattr(self, "api_key", ""),
{indent}            "api_mode": getattr(self, "api_mode", ""),
{indent}        }}

{indent}    if _arc_restore_main:
{indent}        _arc_base = getattr(self, "_hermes_arc_base_runtime", None) or {{}}
{indent}        _base_model = _arc_base.get("model")
{indent}        _base_provider = _arc_base.get("provider")
{indent}        if _base_model and _base_provider:
{indent}            if hasattr(self, "switch_model"):
{indent}                self.switch_model(
{indent}                    _base_model,
{indent}                    _base_provider,
{indent}                    api_key=_arc_base.get("api_key", ""),
{indent}                    base_url=_arc_base.get("base_url", ""),
{indent}                    api_mode=_arc_base.get("api_mode", ""),
{indent}                )
{indent}            else:
{indent}                self.model = str(_base_model)
{indent}                self.provider = str(_base_provider)
{indent}                if _arc_base.get("base_url"):
{indent}                    self.base_url = str(_arc_base.get("base_url")).rstrip("/")
{indent}                if _arc_base.get("api_key"):
{indent}                    self.api_key = str(_arc_base.get("api_key"))
{indent}            logger.info(
{indent}                "hermes-arc: restored main runtime provider=%s model=%s",
{indent}                getattr(self, "provider", ""),
{indent}                getattr(self, "model", ""),
{indent}            )
{indent}    elif _arc_model or _arc_provider or _arc_base_url or _arc_api_key:
{indent}        _target_provider = str(_arc_provider or getattr(self, "provider", "") or "auto")
{indent}        _target_model = str(_arc_model or getattr(self, "model", ""))
{indent}        _resolved_model = _target_model
{indent}        _resolved_api_key = str(_arc_api_key or "")
{indent}        _resolved_base_url = str(_arc_base_url or "")
{indent}        _resolved_api_mode = str(_arc_api_mode or "")

{indent}        try:
{indent}            from agent.auxiliary_client import resolve_provider_client as _arc_resolve_provider_client
{indent}            _arc_client, _arc_client_model = _arc_resolve_provider_client(
{indent}                _target_provider,
{indent}                model=_target_model,
{indent}                raw_codex=True,
{indent}                explicit_base_url=_resolved_base_url or None,
{indent}                explicit_api_key=_resolved_api_key or None,
{indent}                api_mode=_resolved_api_mode or None,
{indent}                main_runtime=getattr(self, "_primary_runtime", None),
{indent}            )
{indent}            if _arc_client is not None:
{indent}                _resolved_model = str(_arc_client_model or _target_model)
{indent}                _resolved_api_key = str(getattr(_arc_client, "api_key", "") or _resolved_api_key)
{indent}                _resolved_base_url = str(getattr(_arc_client, "base_url", "") or _resolved_base_url).rstrip("/")
{indent}        except Exception as _arc_resolve_error:
{indent}            logger.debug("hermes-arc: provider resolution skipped: %s", _arc_resolve_error)

{indent}        if not _resolved_api_mode:
{indent}            try:
{indent}                from hermes_cli.providers import determine_api_mode as _arc_determine_api_mode
{indent}                _resolved_api_mode = _arc_determine_api_mode(_target_provider, _resolved_base_url)
{indent}            except Exception:
{indent}                _resolved_api_mode = getattr(self, "api_mode", "")

{indent}        if hasattr(self, "switch_model"):
{indent}            self.switch_model(
{indent}                _resolved_model,
{indent}                _target_provider,
{indent}                api_key=_resolved_api_key,
{indent}                base_url=_resolved_base_url,
{indent}                api_mode=_resolved_api_mode,
{indent}            )
{indent}        else:
{indent}            self.model = str(_resolved_model)
{indent}            self.provider = str(_target_provider)
{indent}            if _resolved_base_url:
{indent}                self.base_url = _resolved_base_url
{indent}            if _resolved_api_key:
{indent}                self.api_key = _resolved_api_key
{indent}            if hasattr(self, "_client_kwargs"):
{indent}                if _resolved_base_url:
{indent}                    self._client_kwargs["base_url"] = self.base_url
{indent}                if _resolved_api_key:
{indent}                    self._client_kwargs["api_key"] = self.api_key
{indent}            if (_resolved_base_url or _resolved_api_key) and hasattr(self, "_replace_primary_openai_client"):
{indent}                try:
{indent}                    if hasattr(self, "_apply_client_headers_for_base_url"):
{indent}                        self._apply_client_headers_for_base_url(self.base_url)
{indent}                    self._replace_primary_openai_client(reason="hermes_arc_runtime_override")
{indent}                except Exception as _arc_client_error:
{indent}                    logger.debug("hermes-arc: client refresh skipped: %s", _arc_client_error)

{indent}        logger.info(
{indent}            "hermes-arc: runtime_override applied provider=%s model=%s api_mode=%s",
{indent}            getattr(self, "provider", ""),
{indent}            getattr(self, "model", ""),
{indent}            getattr(self, "api_mode", ""),
{indent}        )

{indent}    if _arc_system_prompt:
{indent}        _plugin_system_prompt = str(_arc_system_prompt)
'''
            new_content = new_content.replace(old_block, upgrade_block, 1)
            print("🩹 Upgraded old ARC runtime patch to switch_model-compatible routing")
        else:
            print("⚠️  Could not locate old ARC runtime block — upgrade skipped")

    if "HERMES_ARC_SYSTEM_PROMPT_PATCH" not in new_content:
        # Patch 1: Add plugin_system_prompt parameter to _handle_max_iterations signature
        sig_old = (
            '    def _handle_max_iterations(self, messages: list, api_call_count: int) -> str:\n'
        )
        sig_new = (
            '    def _handle_max_iterations(\n'
            '        self,\n'
            '        messages: list,\n'
            '        api_call_count: int,\n'
            '        plugin_system_prompt: str = "",\n'
            '    ) -> str:\n'
        )
        if sig_old in new_content:
            new_content = new_content.replace(sig_old, sig_new, 1)
        else:
            print("⚠️  Could not locate _handle_max_iterations signature — system_prompt patch skipped")
            return new_content

        # Patch 2: Use the parameter instead of the undefined local variable
        sys_old = (
            '            if self.ephemeral_system_prompt:\n'
            '                effective_system = (effective_system + "\\n\\n" + self.ephemeral_system_prompt).strip()\n'
        )
        sys_new = (
            '            if self.ephemeral_system_prompt:\n'
            '                effective_system = (effective_system + "\\n\\n" + self.ephemeral_system_prompt).strip()\n'
            '            # HERMES_ARC_SYSTEM_PROMPT_PATCH: topic/persona prompt from runtime_override\n'
            '            if plugin_system_prompt:\n'
            '                effective_system = (effective_system + "\\n\\n" + plugin_system_prompt).strip()\n'
        )
        if sys_old in new_content:
            new_content = new_content.replace(sys_old, sys_new, 1)
        else:
            print("⚠️  Could not locate effective_system block — system_prompt patch skipped")

        # Patch 3: Pass _plugin_system_prompt when calling _handle_max_iterations from run_conversation
        call_old = (
            '            final_response = self._handle_max_iterations(messages, api_call_count)\n'
        )
        call_new = (
            '            final_response = self._handle_max_iterations(\n'
            '                messages,\n'
            '                api_call_count,\n'
            '                plugin_system_prompt=_plugin_system_prompt,\n'
            '            )\n'
        )
        if call_old in new_content:
            new_content = new_content.replace(call_old, call_new, 1)
        else:
            print("⚠️  Could not locate _handle_max_iterations call site — system_prompt patch skipped")


    if "HERMES_ARC_RESPONSE_SUFFIX_PATCH" not in new_content:
        final_response_pattern = re.compile(
            r'^(?P<indent>\s*)final_response\s*=\s*assistant_message\.content(?:\s+or\s+["\']{2})?\s*$',
            re.MULTILINE,
        )
        final_match = final_response_pattern.search(new_content)
        if final_match:
            indent = final_match.group("indent")
            suffix_block = (
                "\n"
                f"{indent}# HERMES_ARC_RESPONSE_SUFFIX_PATCH: append routing signature\n"
                f"{indent}try:\n"
                f"{indent}    if isinstance(_runtime_override, dict):\n"
                f"{indent}        _response_suffix = _runtime_override.get(\"response_suffix\")\n"
                f"{indent}        if _response_suffix:\n"
                f"{indent}            final_response = f\"{{final_response}}{{_response_suffix}}\"\n"
                f"{indent}except Exception as _arc_suffix_error:\n"
                f"{indent}    logger.debug(\"hermes-arc: response_suffix append skipped: %s\", _arc_suffix_error)\n"
            )
            new_content = new_content[:final_match.end()] + suffix_block + new_content[final_match.end():]
        else:
            print("⚠️  Could not locate final_response assignment — response_suffix patch skipped")

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
        "system_prompt injection": "HERMES_ARC_SYSTEM_PROMPT_PATCH" in content or "plugin_system_prompt" in content,
        "response_suffix append": "HERMES_ARC_RESPONSE_SUFFIX_PATCH" in content,
        "pre_llm_call hook intact": "pre_llm_call" in content,
        "runtime_override handling": "runtime_override" in content,
        "switch_model runtime routing": "_arc_resolve_provider_client" in content and "restore_main" in content,
        "max_iterations accepts plugin_system_prompt": 'def _handle_max_iterations(' in content and "plugin_system_prompt: str" in content,
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
    parser.add_argument(
        "--list", action="store_true",
        help="List discovered Hermes run_agent.py candidates"
    )

    args = parser.parse_args()

    if args.list:
        candidates = find_run_agent_candidates()
        if not candidates:
            print("No Hermes run_agent.py candidates found")
            sys.exit(1)
        for path in candidates:
            print(path)
        sys.exit(0)

    if not any([args.check, args.patch, args.verify]):
        parser.print_help()
        sys.exit(0)

    # Locate run_agent.py
    run_agent_path = choose_run_agent_path(args.path, interactive=True)

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
        print("   runtime_override is handled with switch_model-compatible routing")
        sys.exit(0)

    # ── Patch mode ───────────────────────────────────────────────────────
    if args.patch:
        if not needs_patch(results):
            print("ℹ️  No critical issues found — patch not required")
            sys.exit(0)

        print("⚠️  Compatibility issues detected — patch needed")
        print()

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
            print("   hermes gateway restart")
        else:
            print("\n⚠️  Verification incomplete — check manually")
    else:
        print("ℹ️  Run with --patch to apply the fix")


if __name__ == "__main__":
    main()
