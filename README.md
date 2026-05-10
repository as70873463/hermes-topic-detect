# ⚡ Hermes ARC — Adaptive Routing Core

> **Smart multi-agent orchestration for Hermes Agent.**<br>
> Routes conversations by topic — switching models, personas, and prompts in real time, with human-like contextual inertia.

**English** · [ไทย](README_TH.md)

![License](https://img.shields.io/badge/license-MIT-green)
![Hermes Plugin](https://img.shields.io/badge/Hermes-plugin-blue)
![Status](https://img.shields.io/badge/status-v2.1--beta-orange)

**Product name:** Hermes ARC (Adaptive Routing Core)<br>
**Internal plugin name:** `topic_detect` — kept for backward compatibility<br>
**Config key:** `topic_detect:` — do **not** rename yet

Hermes ARC is an adaptive conversational orchestration layer for [Hermes Agent](https://hermes-agent.nousresearch.com). It began as a topic detector, but has evolved into a lightweight runtime for routing conversations across models, personas, prompts, and future tool/memory policies.

---

## 🚀 Installation

### One-Click Install

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash
```

The installer copies the plugin into:

```txt
~/.hermes/plugins/topic_detect
```

During install, ARC also updates `~/.hermes/config.yaml` with the required `plugins:` entry and a complete `topic_detect:` block if they are missing. Existing user values are preserved; the installer only fills missing fields and creates a timestamped config backup before writing.

ARC then discovers the active Hermes `run_agent.py` location and checks whether it supports runtime `system_prompt` and `response_suffix` overrides. If more than one Hermes runtime is found, the installer asks which one to check/patch. If support is missing, it asks before patching Hermes core and creates a timestamped backup first.

For unattended installs:

```bash
# Auto-patch runtime if needed
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --patch-runtime

# Install without modifying config.yaml
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --no-config

# Install against a custom Hermes config path
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --config-path /path/to/config.yaml

# Auto-patch a specific Hermes runtime when multiple installs exist
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --patch-runtime --run-agent-path /path/to/run_agent.py

# Never patch runtime
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --no-patch-runtime
```

### Manual Install

```bash
# 1. Clone the repo
git clone https://github.com/ShockShoot/hermes-arc.git
cd hermes-arc

# 2. Copy plugin files
mkdir -p ~/.hermes/plugins/topic_detect
cp __init__.py state.py classifier.py semantic.py config.py \
   agent_loader.py signature.py patch_run_agent.py AGENTS.md plugin.yaml README.md README_TH.md \
   ~/.hermes/plugins/topic_detect/

# 3. Enable plugin
hermes plugins enable topic_detect

# 4. Add/merge the topic_detect config block from the Configuration section below
#    (the one-click installer does this automatically)

# 5. Restart Hermes gateway, or exit/relaunch Hermes CLI
hermes gateway restart
```

### Verify Installation

```bash
hermes plugins list | grep topic_detect
hermes logs | grep topic_detect
```

Possible log output:

```txt
topic_detect: loaded
topic_detect: switching provider=openrouter model=inclusionai/ring-2.6-1t:free
topic_detect: signature=- ring-2.6-1t [programming]
```

---

## ✅ Runtime Compatibility Check

ARC includes a checker/patcher for Hermes core runtime override support. The installer runs this check automatically and asks before patching if compatibility is missing.

Manual discovery/check:

```bash
# List discovered Hermes runtimes
python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --list

# Check the auto-selected runtime, or prompt if multiple exist
python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --check

# Check a specific runtime
python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --check --path /path/to/run_agent.py
```

Expected fully-compatible result:

```txt
pre_llm_call hook: ✅
reads runtime_override: ✅
applies model override: ✅
applies provider override: ✅
applies system_prompt override: ✅
handles response_suffix: ✅
```

If `system_prompt` or `response_suffix` are missing, model routing may still work, but persona injection/signature behavior will be limited until `run_agent.py` is patched.

To patch supported installs:

```bash
# Auto-select/prompt
python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --patch

# Or patch a specific runtime
python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --patch --path /path/to/run_agent.py
```

Then restart Hermes.

---

## 🤔 The Problem

Most multi-agent systems switch models abruptly. One message goes to a coding expert, the next is silently handed off to another model mid-thought. That feels jarring, incoherent, and breaks conversational flow.

Hermes ARC fixes this by classifying intent, accumulating confidence across turns, and only committing to a route change when the signal is strong enough. The result is routing that feels natural instead of mechanical.

---

## ✨ Features

### 🔀 Runtime Model Routing

Per-topic provider, model, base URL, and API key switching via `config.yaml`. When the active topic changes, Hermes loads the correct model on the fly — no manual model picker, no restart for each topic.

Example:

```yaml
topic_detect:
  topics:
    programming:
      provider: openrouter
      model: inclusionai/ring-2.6-1t:free

    marketing:
      provider: openrouter
      model: openrouter/owl-alpha
```

### 🧠 Smart Inertia Engine

Topics do **not** switch instantly. Confidence accumulates across turns:

```txt
threshold = max(1.5, inertia × 0.8)
```

Behavior:

- Same topic reinforces the current route.
- Competing topics accumulate score over turns.
- Switch fires only when accumulated score reaches the threshold.

Example:

```txt
finance 0.82
finance 0.91
total = 1.73
→ switch
```

Result: smooth continuity instead of ping-pong routing.

Main file: `state.py`

### ⚡ Hybrid Routing

| Mode | Behavior |
|------|----------|
| `keyword` | Fastest — deterministic keyword/phrase scoring. |
| `semantic` | Smartest — LLM-based classification via OpenRouter. |
| `hybrid` | Recommended — keyword first, semantic fallback when confidence is low. |

Preferred production mode:

```txt
keyword first → semantic fallback
```

### 🎭 Persona Injection

Topic-specific expert personas are loaded from `AGENTS.md` and injected as `system_prompt` at runtime.

Supported topics:

```txt
programming · finance · marketing · translation · legal · health
roleplay · seo · science · technology · academia · trivia
```

Example persona:

```md
# finance

You are a careful finance analyst.

Rules:
- Focus on downside risk.
- Separate facts from opinions.
- Avoid emotional investing advice.
```

### 🔍 Signature Transparency Layer

Each response can include a compact routing tag so you can see what ARC is doing under the hood:

```txt
- ring-2.6-1t [programming]
- owl-alpha [marketing]
- ring-2.6-1t [programming → finance]
```

Enable or disable it with:

```yaml
topic_detect:
  signature:
    enabled: true
```

### 🧩 Runtime Prompt Injection

ARC can return a runtime override containing:

```python
runtime_override = {
    "provider": "openrouter",
    "model": "inclusionai/ring-2.6-1t:free",
    "base_url": "https://openrouter.ai/api/v1",
    "api_key": "${OPENROUTER_API_KEY}",
    "system_prompt": "You are an expert software engineer...",
}
```

This powers model routing + persona routing from the same decision layer.

If no configured topic target matches, ARC returns an empty `runtime_override` and Hermes keeps using the main `model:` config. ARC no longer defines a separate `topic_detect.default` model, because that can conflict with the user's primary Hermes model.

> Compatibility note: model/provider/base_url/api_key support depends on Hermes runtime version. `system_prompt` and `response_suffix` require a compatible or patched `run_agent.py`. Use the checker below.

---

## 🏗 Architecture

```txt
User Input
   ↓
Keyword Classifier       ← fast, deterministic
   ↓
Semantic Router          ← LLM-based fallback via OpenRouter
   ↓
Smart Inertia Engine     ← confidence accumulation across turns
   ↓
Topic State              → model routing + persona selection
   ↓
Runtime Override         → provider / model / base_url / api_key / system_prompt
   ↓
Signature Layer          → transparency tag appended to response
```

Current classification: this is no longer only *topic detection*. Hermes ARC is closer to an adaptive conversational orchestration framework — a lightweight multi-agent runtime for models, personas, tools, memory, and behavior.

---

## ⚙️ Configuration

Full example (`~/.hermes/config.yaml`):

```yaml
plugins:
  - topic_detect

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

Secrets should live in `~/.hermes/.env`, not directly in `config.yaml`. Add your OpenRouter key there under the standard `OPENROUTER_API_KEY` variable name.

---

## 🧭 Routing Mode Logic

```python
if mode == "keyword":
    result = keyword_classify(messages)

elif mode == "semantic":
    result = semantic_classify(messages)

elif mode == "hybrid":
    result = keyword_classify(messages)
    if result.confidence < semantic.min_confidence:
        semantic_result = semantic_classify(messages)
        if semantic_result.confidence > result.confidence:
            result = semantic_result

state.decide(result.topic, result.confidence, inertia, min_confidence)
```

---

## 📁 Plugin Files

| File | Purpose |
|------|---------|
| `__init__.py` | Plugin entry point. Registers the `pre_llm_call` hook and returns runtime overrides. |
| `classifier.py` | Keyword classifier with weighted scoring, phrase boosts, and recency weighting. |
| `semantic.py` | LLM-based semantic classifier via OpenRouter API. |
| `state.py` | Smart Inertia Engine — confidence accumulation and topic switching. |
| `config.py` | Loads `topic_detect:` config into typed dataclasses. |
| `agent_loader.py` | Parses `AGENTS.md` into topic-to-persona mappings. |
| `signature.py` | Builds the transparency signature tag. |
| `patch_run_agent.py` | Compatibility checker/patcher for Hermes core runtime override support. |
| `AGENTS.md` | Persona definitions for all supported topics. |
| `plugin.yaml` | Plugin metadata. |
| `README.md` | Project documentation in English. |
| `README_TH.md` | Project documentation in Thai. |

---

## 🔑 Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENROUTER_API_KEY` | Required for semantic mode and OpenRouter topic models | API key for OpenRouter. |

Store keys in `~/.hermes/.env`. Never commit secrets, tokens, logs, cache files, or `.env`.

---

## 🛠 Troubleshooting

### Plugin not loading

```bash
hermes plugins list | grep topic_detect
hermes logs | grep topic_detect
```

Check that both are true:

```yaml
plugins:
  - topic_detect

topic_detect:
  enabled: true
```

Then restart Hermes gateway or relaunch the CLI:

```bash
hermes gateway restart
```

### Topic does not switch

- Lower `min_confidence` temporarily, for example `0.3`.
- Use `routing_mode: semantic` for more nuanced classification.
- Check logs for classifier confidence and selected topic.

If no topic matches, this is expected: ARC emits no runtime override and Hermes uses the main `model:` config.

### Unexpected topic switches

- Raise `inertia`, for example `3` or `4`.
- Raise `min_confidence` if noisy keyword matches are causing false positives.
- Prefer `hybrid` mode over pure `semantic` if you need deterministic behavior.

### Semantic classifier failing

- Verify `OPENROUTER_API_KEY` exists in `~/.hermes/.env`.
- Confirm the semantic model is available on your OpenRouter account.
- Try a different semantic classifier model in `topic_detect.semantic.model`.

### Persona injection not working

Run:

```bash
python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --check
```

If `system_prompt override` is not supported, patch Hermes core or use ARC only for model routing/signature behavior.

---

## 🗺 Roadmap

| Priority | Feature | Status |
|----------|---------|--------|
| P1 | Persistent state across sessions (`~/.hermes/state/topic_state.json`) | Planned |
| P2 | Weighted multi-topic routing for mixed-domain conversations | Planned |
| P3 | Topic-aware tool sandboxing | Planned |
| P4 | Cost-aware routing by complexity, latency, token budget, and reasoning need | Planned |

Future ecosystem modules may include:

- Hermes ARC Runtime
- Hermes ARC Memory
- Hermes ARC Agents
- Hermes ARC Router
- Hermes ARC Tools
- Hermes ARC Studio

---

## 🧱 Design Principles

- Keep `Hermes ARC` as the product/platform name.
- Keep `topic_detect` as the internal plugin name until a coordinated migration exists.
- Prefer smooth routing transitions over instant switches.
- Make routing visible and debuggable through signatures.
- Keep secrets outside config and outside git.
- Favor incremental compatibility with Hermes core over risky rewrites.

---

## 📄 License

MIT — same as [Hermes Agent](https://github.com/NousResearch/hermes-agent).

---

<div align="center">
  <sub>Built for <a href="https://hermes-agent.nousresearch.com">Hermes Agent</a> · Maintained by <a href="https://github.com/ShockShoot">ShockShoot</a></sub>
</div>
