# Changelog

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
