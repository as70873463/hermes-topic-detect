# Changelog

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
