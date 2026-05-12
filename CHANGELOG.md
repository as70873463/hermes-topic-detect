# Changelog

## 1.2.0 - 2026-05-12

### Breaking
- Full rewrite of core compatibility patch to match Hermes Agent v0.13+ plugin hook architecture. After 62 upstream commits refactored `pre_llm_call` (now returns context-only, no `runtime_override` dict) and removed `response_suffix` / `plugin_system_prompt` mechanisms entirely, v1.1.x patches are incompatible.

### Added
- `switch_model()` integration: runtime model/provider routing now uses Hermes' native `switch_model()` method instead of direct attribute mutation. This preserves provider-specific `api_mode`, OAuth credentials, headers, context-compressor metadata, and client rebuild logic.
- `provider=self.provider` injection into `transform_llm_output` hook — enables signature builder to detect fallback (final model differs from routed model).
- `_arc_signature` dict in `runtime_override` — structured routing metadata (`topic`, `routed_model`, `routed_provider`) carried into post-loop for final-render.
- System prompt override injected as part of `_ctx_parts` into user message, preserving prompt cache prefix stability.

### Changed
- `patch_run_agent.py` completely rewritten for v1.2.0:
  - Patch 1A: `_runtime_override` dict init before `pre_llm_call`
  - Patch 1B: collect `runtime_override` from hook results
  - Patch 1C: apply routing via `switch_model()` (with `resolve_provider_client` + `determine_api_mode`)
  - Patch 2: inject `provider=self.provider` into `transform_llm_output` hook
  - Patch 3: `_arc_signature` suffix render (fallback-aware)
  - Patch 4: system prompt capture as `_ctx_parts` member
- Plugin `__init__.py` unchanged — structurally compatible with v1.2.0 patch (sends `runtime_override` dict, reads `provider` from kwargs)
- Config topic models updated:
  - `software_it` → `nvidia/nemotron-3-super-120b-a12b:free`
  - `math` → `inclusionai/ring-2.6-1t:free`
  - `science` → `nvidia/nemotron-3-super-120b-a12b:free`
  - `business_finance` → `openai/gpt-oss-120b:free`
  - `legal_government` → `openai/gpt-oss-120b:free`
  - `medicine_healthcare` → `openrouter/owl-alpha`
  - `writing_language` → `google/gemma-4-31b-it:free`
  - `entertainment_media` → empty (falls back to main model)

### Deprecated
- PR #23898 (`_plugin_system_prompt` scope fix) — upstream removed the entire mechanism; v1.2.0 uses a different approach that doesn't require patching `_handle_max_iterations()`.

## 1.1.8 - 2026-05-12

### Fixed
- Signatures now identify the model that actually produced the final answer after Hermes fallback. When ARC routes to one model but the API call rate-limits/fails and Hermes switches to fallback, the suffix renders the final responder first and preserves the routed model as context, e.g. `- owl-alpha [software_it | routed: gemma-4-31b]`.
- The legacy `transform_llm_output` compatibility path also rebuilds signatures from the final model when available.

## 1.1.7 - 2026-05-11

### Fixed
- `patch_run_agent.py` no longer injects code referencing `_plugin_system_prompt` as a local variable inside `_handle_max_iterations()`. That variable only exists in `run_conversation()` scope and caused a `NameError` at runtime when max iterations was reached with a plugin system_prompt override. The patcher now adds `plugin_system_prompt: str = ""` as a parameter to `_handle_max_iterations`, uses the parameter in the injected code, and passes `_plugin_system_prompt` from the call site. Matches the fix in NousResearch/hermes-agent PR #23898.

## 1.1.6 - 2026-05-11

### Fixed
- Installer no longer prints `Removed unresolved api_key` and then re-adds the same `${OPENROUTER_API_KEY}` placeholder to topic targets. It now treats `OPENROUTER_API_KEY` in `~/.hermes/.env` as resolvable, and only omits/removes the placeholder when the key is unavailable from both the process environment and `.env`.

## 1.1.5 - 2026-05-11

### Fixed
- Restore visible topic signatures on patched Hermes cores by placing `response_suffix` inside `runtime_override`, where the ARC core patch reads it. Keeps the legacy `transform_llm_output` fallback for older cores without duplicating signatures.

## 1.1.4 - 2026-05-11

### Fixed
- Avoid duplicate topic signature suffixes when running on Hermes core builds that consume `runtime_override.response_suffix`; ARC now chooses either the core suffix path or the legacy `transform_llm_output` path, never both.

## 1.1.3 - 2026-05-11

### Fixed
- Installer now migrates/removes legacy 12-topic config keys when updating to the 8-topic Arena-aligned taxonomy, preventing stale topics from accumulating in `topic_detect.topics`.
- Legacy topic values are preserved when they can be safely moved into a new topic that does not already exist; custom non-legacy topics are left untouched.

## 1.1.2 - 2026-05-11

### Changed
- Polished README/README_TH positioning for Hermes ARC as a practical reference implementation for topic-aware runtime model routing.
- Added upstream Hermes issue links, clean smart-router architecture direction, roadmap, and current recommended model mapping examples.

## 1.1.1 - 2026-05-11

### Changed
- Signature display now renders internal `none`/empty fallback topics as `general`, e.g. `- gpt-5.5 [general]`, while keeping internal routing logic as `none`.

## 1.1.0 - 2026-05-11

### Added
- Runtime update notice: after Hermes restarts, ARC checks once whether a newer `plugin.yaml` version exists on GitHub and logs an update notice without spamming chat responses.
- `install.sh --check` to compare local vs latest GitHub version.
- `install.sh --update` as an explicit update alias for normal install/update flow.
- `topic_detect.update_check` config support.

### Changed
- Reworked taxonomy to 8 Arena.ai-aligned primary topics: `software_it`, `math`, `science`, `business_finance`, `legal_government`, `medicine_healthcare`, `writing_language`, `entertainment_media`.
- Removed the `general` topic; unclear prompts return `none` and use Hermes' main model.
- Tuned bilingual EN/TH keyword routing to be conservative and high-signal only.
- Removed ambiguous broad keywords such as `app`, `review`, `policy`, `market`, `terms`, `story`, generic `เขียน`, and generic `สุขภาพ`.
- English keyword matching now uses token boundaries instead of raw substring matching.
- Topics with missing/empty `provider` or `model` are skipped and gracefully fall back to Hermes' main model.

### Notes
- `entertainment_media` is intentionally optional; leave it without a model if your main model handles movie/game/sports/media prompts well.
- `writing_language` remains broad by design. If routing complaints appear later, split creative writing and translation first.
- Arena Expert/Hard/Instruction/Multi-Turn/Longer Query/language boards remain future modifiers, not primary routes.
