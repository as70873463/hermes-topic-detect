# Hermes ARC — Adaptive Routing Core

> **Product name:** Hermes ARC (Adaptive Routing Core)
> **Internal plugin name:** `topic_detect` (kept for backward compatibility)
> **Config key:** `topic_detect:` (do NOT change)

Hermes ARC is an adaptive conversational multi-agent orchestration layer for
[Hermes Agent](https://hermes-agent.nousresearch.com). It routes conversations
by topic — dynamically switching models, personas, and system prompts in
real-time, with human-like contextual inertia instead of jarring instant swaps.

---

## Architecture

```
User Input
   ↓
Keyword Classifier (fast, deterministic)
   ↓
Semantic Router (LLM-based fallback)
   ↓
Smart Inertia Engine (confidence accumulation)
   ↓
Topic State → Model Routing + Persona Injection
   ↓
Runtime Override (provider / model / system_prompt)
   ↓
Signature Layer (transparency tag)
```

---

## Features

### Runtime Model Routing
Per-topic provider and model switching via `config.yaml`. When the active topic
changes, Hermes loads the corresponding model, provider, base_url, and API key
on the fly.

### Smart Inertia Engine
Does NOT switch topics instantly. Instead it accumulates confidence across
turns until a threshold is reached:

- `threshold = max(1.5, inertia * 0.8)`
- Same topic reinforces → no switch
- Competing topic accumulates score over turns
- Switch only fires when accumulated score ≥ threshold

Result: **smooth conversational continuity** instead of ping-pong routing.

### Hybrid Routing
Three modes:

| Mode | Behavior |
|------|----------|
| `keyword` | Fastest. Pure keyword matching. |
| `semantic` | Smartest. LLM-based classification via OpenRouter. |
| `hybrid` (recommended) | Keyword first. Falls back to semantic when confidence is low. |

### Persona Injection (AGENTS.md)
Topic-specific expert personas loaded from `~/.hermes/plugins/topic_detect/AGENTS.md`.
The active persona is injected as `system_prompt` at runtime — no manual prompt
engineering needed.

Supported topics: `programming`, `finance`, `marketing`, `translation`, `legal`,
`health`, `roleplay`, `seo`, `science`, `technology`, `academia`, `trivia`.

### Signature Transparency Layer
Appends a compact routing tag to each response:

```
- ring-2.6-1t [programming]
- owl-alpha [marketing]
- ring-2.6-1t [programming → finance]   ← transition in progress
```

Configurable via `signature.enabled`.

### Conversational Continuity
During topic transitions, both the current and candidate topics are visible
in the signature. The model only commits to the new topic after inertia
threshold is met — keeping the conversation coherent.

---

## Installation

### One-Click Install

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash
```

### Manual Install

```bash
# 1. Copy plugin files
mkdir -p ~/.hermes/plugins/topic_detect
cp __init__.py state.py classifier.py semantic.py config.py \
   agent_loader.py signature.py patch_run_agent.py AGENTS.md plugin.yaml README.md \
   ~/.hermes/plugins/topic_detect/

# 2. Enable plugin
hermes plugins enable topic_detect

# 3. Restart
hermes restart
```

### Verify Installation

```bash
hermes logs | grep topic_detect
```

Expected output:

```
topic_detect: loaded
topic_detect: switching provider=openrouter model=inclusionai/ring-2.6-1t:free
topic_detect: signature=- ring-2.6-1t [programming]
```

---

## Configuration

Full example (`~/.hermes/config.yaml`):

```yaml
topic_detect:
  enabled: true
  inertia: 2
  min_confidence: 0.45
  routing_mode: hybrid        # keyword | semantic | hybrid

  signature:
    enabled: true

  semantic:
    enabled: true
    provider: openrouter
    model: baidu/cobuddy:free
    min_confidence: 0.7
    base_url: https://openrouter.ai/api/v1
    api_key: ${OPENROUTER_API_KEY}

  # Default model when no topic matches
  default:
    provider: openrouter
    model: openrouter/owl-alpha

  # Per-topic model routing
  topics:
    programming:
      provider: openrouter
      model: inclusionai/ring-2.6-1t:free
    finance:
      provider: openrouter
      model: inclusionai/ring-2.6-1t:free
    science:
      provider: openrouter
      model: inclusionai/ring-2.6-1t:free
    academia:
      provider: openrouter
      model: inclusionai/ring-2.6-1t:free
    health:
      provider: openrouter
      model: openrouter/owl-alpha
    legal:
      provider: openrouter
      model: openrouter/owl-alpha
    seo:
      provider: openrouter
      model: openrouter/owl-alpha
    translation:
      provider: openrouter
      model: openrouter/owl-alpha
    technology:
      provider: openrouter
      model: openrouter/owl-alpha
    marketing:
      provider: openrouter
      model: openrouter/owl-alpha
    roleplay:
      provider: openrouter
      model: baidu/cobuddy:free
    trivia:
      provider: openrouter
      model: baidu/cobuddy:free
```

### Routing Mode Logic

```
if mode == keyword:
    result = keyword_classify(messages)

if mode == semantic:
    result = semantic_classify(messages)

if mode == hybrid:
    result = keyword_classify(messages)
    if result.confidence < semantic.min_confidence:
        semantic = semantic_classify(messages)
        if semantic.confidence > result.confidence:
            result = semantic

state.decide(result.topic, result.confidence, inertia, min_confidence)
```

---

## Plugin Files

| File | Purpose |
|------|---------|
| `__init__.py` | Plugin entry point. Registers `pre_llm_call` hook. |
| `classifier.py` | Keyword-based topic classifier with weighted scoring and recency boost. |
| `semantic.py` | LLM-based semantic classifier via OpenRouter API. |
| `state.py` | Smart Inertia Engine — confidence accumulation and topic switching logic. |
| `config.py` | Loads `topic_detect` section from `config.yaml` into typed dataclasses. |
| `agent_loader.py` | Parses `AGENTS.md` → topic-to-persona-prompt mapping. |
| `signature.py` | Builds the transparency signature tag. |
| `patch_run_agent.py` | Local compatibility patcher for Hermes core runtime override support. |
| `AGENTS.md` | Persona definitions for all 12 topics. |
| `plugin.yaml` | Plugin metadata. |
| `README.md` | This file. |

---

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENROUTER_API_KEY` | Yes | API key for OpenRouter (semantic + topic models) |

Keys are read from `~/.hermes/.env` — never hardcode them in config files.

---

## Roadmap

| Priority | Feature | Status |
|----------|---------|--------|
| P1 | Persistent state (`~/.hermes/state/topic_state.json`) | Planned |
| P2 | Weighted multi-topic routing (mixed-domain) | Planned |
| P3 | Topic-aware tool sandboxing | Planned |
| P4 | Cost-aware model selection | Planned |

---

## License

MIT — same as [Hermes Agent](https://github.com/nousresearch/hermes-agent).
