# Repository Layout

Hermes ARC deliberately keeps runtime plugin files at the repository root.

Reason: the one-line installer downloads raw files directly from GitHub into `~/.hermes/plugins/topic_detect`, and Hermes loads the plugin from that flat plugin directory. Moving runtime modules under a package directory would require a larger installer/plugin-loader migration.

## Runtime plugin files

These files are installed into `~/.hermes/plugins/topic_detect`:

- `__init__.py` — Hermes plugin entrypoint and hook registration
- `classifier.py` — v2 intent/action-first keyword router
- `semantic.py` — semantic router prompt/client
- `config.py` — config loading and target model mapping
- `agent_loader.py` — topic persona loader from `AGENTS.md`
- `signature.py` — visible ARC suffix builders
- `state.py` — topic inertia/switching state
- `update_checker.py` — startup update notice
- `patch_run_agent.py` — Hermes core compatibility patcher
- `plugin.yaml` — Hermes plugin manifest
- `AGENTS.md` — topic/persona prompts

## Development-only files

- `tests/` — smoke tests for classifier and signature finalize rendering
- `docs/` — design notes and operational references
- `.github/workflows/` — CI smoke checks
- `pyproject.toml` — local tooling metadata

## Cleanup rule

Keep the root runtime files flat until Hermes supports packaged plugin layouts or the installer is intentionally migrated. Clean documentation/tests around the flat runtime layout instead of breaking compatibility for aesthetic reasons.
