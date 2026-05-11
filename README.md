# ⚡ Hermes ARC — Adaptive Routing Core

> **A practical reference implementation for topic-aware runtime model routing in Hermes Agent.**  
> ARC detects what the user is talking about, then routes that turn to the model/persona best suited for the topic.

<p align="center">
  <strong>Topic-aware routing</strong> · <strong>Runtime model switching</strong> · <strong>Arena-aligned taxonomy</strong> · <strong>Hermes plugin</strong>
</p>

<p align="center">
  <a href="README_TH.md">ไทย</a> · <strong>English</strong>
</p>

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
  → classify topic
  → choose configured model/persona
  → call Hermes with a runtime override
  → append a small routing signature
```

ARC is intentionally small and practical. It does not claim to be a full smart-router yet. It is a working foundation for that direction.

---

## What It Does

- **Detects the topic** with keyword, semantic, or hybrid routing.
- **Switches model/provider at runtime** based on `topic_detect.topics`.
- **Adds a topic persona** from `AGENTS.md` so the routed model behaves like a specialist.
- **Falls back safely** to the main Hermes model when no specialized topic is confident enough.
- **Shows a signature** so users can see what route was used.

Example signatures:

```text
- gemma-4-31b:free [software_it]
- minimax-m2.5:free [business_finance]
- glm-4.5-air:free [entertainment_media]
- gpt-5.5 [general]
```

Internally, ARC still uses `none` for “no specialist topic matched.” The user-facing signature renders that as `[general]` because it is clearer.

---

## Relationship to Hermes Core

ARC currently works as a Hermes plugin and may use a compatibility patch on Hermes versions where `pre_llm_call` cannot yet apply runtime overrides.

Related upstream work:

- Smart routing discussion: https://github.com/NousResearch/hermes-agent/issues/21827
- Core primitive proposal: https://github.com/NousResearch/hermes-agent/issues/23739

If Hermes core adds native `pre_llm_call` runtime overrides, ARC can remove the monkey-patch path and use that hook directly.

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
topic_detect: signature=- gemma-4-31b:free [software_it]
```

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
- **v1.x:** Cleaner compatibility with upstream `pre_llm_call` runtime overrides once merged.
- **v2:** Complexity-aware routing: simple vs hard prompts, latency/cost preference, reasoning depth.
- **v3:** Smart-router interface that can integrate external routers such as Manifest-style systems.

---

## Design Principles

- **Router is configurable, not magical.** Users choose their own models.
- **Main model remains the safe fallback.** No confident topic → no specialist override.
- **Small visible signature.** Routing is transparent but not noisy.
- **Plugin first, core-friendly later.** ARC proves behavior now while aligning with cleaner Hermes core hooks.

---

## License

MIT
