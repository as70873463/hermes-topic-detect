# ⚡ Hermes ARC — Adaptive Routing Core

> **A practical reference implementation for intent-aware runtime model routing in Hermes Agent.**  
> ARC detects what the user is trying to do first, then uses the subject as a tiebreaker when needed.

<p align="center">
  <strong>Intent-aware routing</strong> · <strong>Runtime model switching</strong> · <strong>Final-model signatures</strong> · <strong>Hermes plugin</strong>
</p>

<p align="center">
  <a href="README_TH.md">ไทย</a> · <strong>English</strong>
</p>

---

## At a Glance

ARC is a Hermes Agent plugin that routes each turn to a configured specialist model when doing so is useful, while leaving ordinary chat on the main model.

- **Problem:** one default model is not always the cheapest or strongest choice for every task.
- **Approach:** detect the user's action first, then use the subject/topic as a tiebreaker.
- **Current status:** works today as a plugin; `patch_run_agent.py` is a temporary compatibility bridge.
- **Upstream path:** once NousResearch/hermes-agent#23898 lands, ARC can drop the patch and use native plugin runtime overrides.
- **Next direction:** smart routing with complexity, cost/latency, hardware awareness, and external router integrations.

---

## Why ARC Exists

Hermes can run with one powerful main model for every task, but that is not always ideal:

- Coding questions may benefit from a coding-strong model.
- Finance questions may benefit from a business/finance model.
- Creative or media questions may not need the same expensive reasoning model.
- Simple/general chat should stay on the main model without unnecessary switching.

**Hermes ARC turns model routing into a plugin-level capability:**

```text
User message
  → detect action/intent first
  → use subject/topic as tiebreaker when needed
  → choose configured model/persona
  → call Hermes with a runtime override
  → append a small routing signature
```

ARC is intentionally small and practical. It does not claim to be a full smart-router yet. It is a working foundation for that direction.

---

## What It Does

- **Detects the user's intent/action first** with keyword, semantic, or hybrid routing.
- **Uses subject/topic as a tiebreaker** when action alone is not enough.
- **Switches model/provider at runtime** based on `topic_detect.topics`.
- **Adds a topic persona** from `AGENTS.md` so the routed model behaves like a specialist.
- **Falls back safely** to the main Hermes model when no specialized topic is confident enough.
- **Shows a signature** so users can see what route was used.

Example signatures:

```text
- gemma-4-31b [software_it]
- minimax-m2.5 [business_finance]
- glm-4.5-air [entertainment_media]
- gpt-5.5 [general]
- gemini-3-flash [software_it | routed: nemotron-3-super-120b-a12b]
```

Internally, ARC still uses `none` for “no specialist topic matched.” The user-facing signature renders that as `[general]` because it is clearer.

---

## Routing Examples

These examples show the intended behavior, not a hard-coded model recommendation. Your configured `topic_detect.topics` mapping decides the actual model.

```text
User: fix this failing API test
ARC:  action=technical → route=software_it
Shown suffix: - gemma-4-31b [software_it]

User: calculate ROI for this project
ARC:  action=analytical + subject=business_finance → route=business_finance
Shown suffix: - minimax-m2.5 [business_finance]

User: write a short fantasy scene
ARC:  action=creative + subject=writing_language → route=writing_language
Shown suffix: - gemma-4-31b [writing_language]

User: thanks
ARC:  no confident specialist route → main model
Shown suffix: - gpt-5.5 [general]

User: debug this server, but the routed model falls back in Hermes
ARC:  route=software_it, final responder differs from requested route model
Shown suffix: - gemini-3-flash [software_it | routed: nemotron-3-super-120b-a12b]
```

---

## Relationship to Hermes Core

ARC currently works as a Hermes plugin and may use a compatibility patch on Hermes versions where `pre_llm_call` cannot yet apply runtime overrides.

Related upstream work:

- Smart routing discussion: https://github.com/NousResearch/hermes-agent/issues/21827
- Core primitive proposal: https://github.com/NousResearch/hermes-agent/issues/23739
- Native plugin runtime override PR: https://github.com/NousResearch/hermes-agent/pull/23898

Until native runtime overrides land in Hermes core, ARC ships `patch_run_agent.py` as a compatibility bridge. Once upstream PR #23898 merges and is available in a Hermes release, ARC v2.x can drop the patch dependency and use the native plugin hook directly.

Clean target architecture:

```text
Hermes core pre_llm_call runtime override
  → router plugins/providers
  → topic routing, complexity routing, Manifest-style smart routing
```

---

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash
```

Check for updates without installing:

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --check
```

Update explicitly:

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --update
```

After install, add your provider key, for example OpenRouter:

```bash
echo 'OPENROUTER_API_KEY=<your-key>' >> ~/.hermes/.env
hermes gateway restart
```

---

## Recommended Config

Add or update this section in `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - topic_detect

topic_detect:
  enabled: true
  routing_mode: hybrid
  inertia: 2
  min_confidence: 0.45
  agents_file: ~/.hermes/plugins/topic_detect/AGENTS.md
  semantic:
    enabled: true
    provider: openrouter
    model: baidu/cobuddy:free
    min_confidence: 0.7
    base_url: https://openrouter.ai/api/v1
    api_key: ${OPENROUTER_API_KEY}
  signature:
    enabled: true
  update_check:
    enabled: true
    url: https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/plugin.yaml
    timeout_seconds: 2.5
  topics:
    software_it:
      provider: openrouter
      model: google/gemma-4-31b:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    math:
      provider: openrouter
      model: google/gemma-4-31b:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    science:
      provider: openrouter
      model: google/gemma-4-31b:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    business_finance:
      provider: openrouter
      model: minimax/minimax-m2.5:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    legal_government:
      provider: openrouter
      model: minimax/minimax-m2.5:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    medicine_healthcare:
      provider: openrouter
      model: minimax/minimax-m2.5:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    writing_language:
      provider: openrouter
      model: google/gemma-4-31b:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    entertainment_media:
      provider: openrouter
      model: z-ai/glm-4.5-air:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
```

These are only example defaults. ARC does **not** fetch Arena scores or choose models automatically. You remain in control of the model mapping.

---

## Supported Topics

ARC uses an Arena-aligned primary topic taxonomy:

| Topic | Intended use |
|---|---|
| `software_it` | Programming, debugging, infrastructure, software/IT systems |
| `math` | Calculation, proofs, symbolic reasoning, quantitative problems |
| `science` | Natural/social science explanations, mechanisms, research-style questions |
| `business_finance` | Markets, finance, accounting, business operations, strategy |
| `legal_government` | Legal, policy, compliance, public-sector questions |
| `medicine_healthcare` | Medical/healthcare information and safety-aware explanations |
| `writing_language` | Writing, editing, translation, literature, language nuance |
| `entertainment_media` | Movies, games, sports, media analysis, pop culture |

Arena categories such as Expert, Hard Prompts, Instruction Following, Multi-Turn, Longer Query, and language-specific boards are treated as future metadata/modifiers, not primary routes in this version.

---

## Routing Modes

| Mode | Behavior |
|---|---|
| `keyword` | Fast deterministic keyword matching |
| `semantic` | LLM-based classification |
| `hybrid` | Recommended: keyword first, semantic fallback |

Useful knobs:

- `min_confidence`: raise it to reduce accidental routing, lower it to route more aggressively.
- `inertia`: raise it to avoid frequent topic switching in multi-turn conversations.
- `semantic.min_confidence`: controls how confident the semantic classifier must be before it wins.

---

## Verify

```bash
hermes plugins list | grep topic_detect
hermes logs | grep topic_detect
```

Expected style of logs:

```text
topic_detect: loaded
topic_detect: switching provider=openrouter model=google/gemma-4-31b:free
topic_detect: signature=- gemma-4-31b [software_it]
```

---

## Development

Runtime plugin files intentionally stay importable without packaging, but tests need a small dependency set.

```bash
python -m pip install -r requirements-test.txt
python -m compileall . -q
python tests/test_v2_classifier.py
python tests/test_signature_finalize.py
```

`requirements-test.txt` currently contains `PyYAML`, which is needed because the plugin config loader imports `yaml`.

---

## Signature Source

The current patched-core path is:

```text
runtime_override._arc_signature
  → transform_llm_output(_arc_finalize=...)
  → signature.build_final_signature(...)
```

That path renders the model that actually answered after Hermes fallback. `runtime_override.response_suffix` is still kept as a compatibility fallback for older patched cores.

See [`docs/SIGNATURE_FLOW.md`](docs/SIGNATURE_FLOW.md) for the full flow.

---

## Repository Layout

Runtime plugin files intentionally stay flat at the repo root because the one-line installer downloads raw files directly into `~/.hermes/plugins/topic_detect`.

Development-only files live under:

- `tests/` — classifier and signature smoke tests
- `docs/` — design and operational notes
- `.github/workflows/` — CI smoke checks

See [`docs/REPO_LAYOUT.md`](docs/REPO_LAYOUT.md).

Additional design notes:

- [`docs/SIGNATURE_FLOW.md`](docs/SIGNATURE_FLOW.md) — how final-model-aware signatures are rendered.
- [`docs/V2_REWRITE_PLAN.md`](docs/V2_REWRITE_PLAN.md) — v2 action-first routing rewrite plan.
- [`docs/V3_SMART_ROUTER.md`](docs/V3_SMART_ROUTER.md) — future smart-router direction.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Plugin not loading | Check `plugins.enabled` contains `topic_detect`, then restart Hermes |
| Topic not switching | Lower `min_confidence`, or use `routing_mode: semantic` |
| Too many switches | Raise `inertia` to `3` or `4` |
| General prompts route unexpectedly | Raise `min_confidence`; unclear prompts should resolve to internal `none` / display `[general]` |
| Model/provider not switching | Run `python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --check` and apply compatibility patch if needed |
| Persona not injecting | Same as above; older Hermes core needs runtime system-prompt override support |

---

## Roadmap

- **v1:** Topic-aware runtime model routing.
- **v2:** Intent/action-first routing with technical override and final-model-aware signatures.
- **v2.x:** Drop `patch_run_agent.py` dependency once upstream PR #23898 merges native plugin runtime override support.
- **v3:** Smart-router with complexity scoring, cost/latency policy, and external router integration.

---

## Design Principles

- **Router is configurable, not magical.** Users choose their own models.
- **Main model remains the safe fallback.** No confident topic → no specialist override.
- **Small visible signature.** Routing is transparent but not noisy.
- **Plugin first, core-friendly later.** ARC proves behavior now while aligning with cleaner Hermes core hooks.

---

## License

MIT
