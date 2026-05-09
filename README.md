# hermes-topic-detect

A Hermes Agent plugin that automatically detects conversation topics and routes responses to the most appropriate LLM model.

## Features

- **Automatic topic detection** — classifies user messages into 12 topics using keyword signals and phrase boosts
- **Model routing** — switches the active LLM model based on the detected topic
- **Multi-provider support** — works with OpenRouter, Together AI, Groq, Anthropic, OpenAI, or local models
- **Inertia logic** — requires 2 consecutive turns of the same topic before switching (prevents flapping)
- **High-confidence bypass** — switches immediately when confidence ≥ 0.90
- **Zero-confidence reset** — resets to default model when confidence is 0.00
- **Signature injection** — injects a CRITICAL INSTRUCTION into user_message so the model appends `[topic]` to responses
- **Multi-language keyword support** — easy to add keywords for any language

## Supported Topics

| Topic | Default Model |
|-------|---------------|
| programming | ring-2.6-1t |
| finance | ring-2.6-1t |
| science | ring-2.6-1t |
| academia | ring-2.6-1t |
| health | owl-alpha |
| legal | owl-alpha |
| seo | owl-alpha |
| translation | owl-alpha |
| roleplay | cobuddy |
| trivia | cobuddy |
| marketing | cobuddy |
| technology | owl-alpha |
| none (default) | owl-alpha |

## Installation

### Universal version (English keywords only)

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-topic-detect/main/install.sh | bash
```

### Thai version (English + Thai keywords)

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-topic-detect/thai/install-thai.sh | bash
```

### Manual install

```bash
# Universal
git clone --depth 1 https://github.com/ShockShoot/hermes-topic-detect.git /tmp/topic-detect
cp -r /tmp/topic-detect/topic_detect/ ~/.hermes/plugins/topic_detect/

# Thai version
git clone --depth 1 --branch thai https://github.com/ShockShoot/hermes-topic-detect.git /tmp/topic-detect
cp -r /tmp/topic-detect/topic_detect/ ~/.hermes/plugins/topic_detect/
```

## Configuration

Add to your `~/.hermes/config.yaml`:

### Simple (single model per topic — works with any provider)

```yaml
topic_detect:
  enabled: true
  provider: openrouter
  default: owl-alpha
  topics:
    programming:
      model: ring-2.6-1t:free
    finance:
      model: ring-2.6-1t:free
    science:
      model: ring-2.6-1t:free
    academia:
      model: ring-2.6-1t:free
    health:
      model: owl-alpha
    legal:
      model: owl-alpha
    seo:
      model: owl-alpha
    translation:
      model: owl-alpha
    technology:
      model: owl-alpha
    marketing:
      model: owl-alpha
    roleplay:
      model: cobuddy:free
    trivia:
      model: cobuddy:free
```

### Advanced (per-provider model mapping)

Use this if you or other users run the plugin with different LLM providers:

```yaml
topic_detect:
  enabled: true
  provider: openrouter
  default: owl-alpha
  topics:
    programming:
      model: ring-2.6-1t:free
      models:
        openrouter: ring-2.6-1t:free
        together: meta-llama/Llama-3.1-8B-Instruct-Turbo
        groq: llama-3.1-8b-instant
        anthropic: claude-sonnet-4-20250514
        openai: gpt-4o-mini
        local: qwen2.5-coder-7b-instruct
    finance:
      model: ring-2.6-1t:free
      models:
        openrouter: ring-2.6-1t:free
        together: meta-llama/Llama-3.1-70B-Instruct-Turbo
        groq: llama-3.1-70b-versatile
```

**Model resolution order:**
1. `models.<provider>` — if `provider` field is set and per-provider mapping exists
2. `model` — generic fallback (works for all providers)
3. `default` — global fallback

### Provider Credentials

Credentials are read from `~/.hermes/.env`. The plugin looks for these environment variables based on the `provider` field:

| Provider | API Key Env Var | Base URL Env Var | Default Base URL |
|----------|-----------------|------------------|------------------|
| OpenRouter | `OPENROUTER_API_KEY` | `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` |
| Together AI | `TOGETHER_API_KEY` | `TOGETHER_BASE_URL` | `https://api.together.xyz/v1` |
| Groq | `GROQ_API_KEY` | `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` |
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_BASE_URL` | `https://api.openai.com/v1` |
| Local | *(none needed)* | `LOCAL_BASE_URL` | `http://localhost:8000/v1` |

Example `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

If a base URL env var is not set, the default is used automatically.

Then restart Hermes:

```bash
sudo systemctl restart hermes
```

## How It Works

### Classification Pipeline

1. Extract the last N user messages (configurable `window`, default 3)
2. Apply exponential weighting — recent messages count more
3. Score each topic using two methods:
   - **Phrase boosts** — multi-word phrases (e.g. "stack trace", "keyword research") add high weight
   - **Keyword signals** — regex patterns match individual words
4. Calculate confidence as the ratio of best score to total score (capped at 0.95)
5. Enforce minimum score (1.5) and minimum confidence (0.65) thresholds

### Switching Logic

- **Same topic** → no switch
- **Zero confidence** → reset to default immediately
- **High confidence (≥ 0.90)** → switch immediately
- **Normal confidence** → wait for 2 consecutive turns of the same topic

## Adding Keywords for New Languages

To add keywords for a new language (e.g. German, Japanese, Spanish):

1. Ask an AI model to suggest the most common words native speakers use when discussing each topic
2. Add them to the `TOPIC_SIGNALS` dict in `classifier.py`
3. For non-Latin scripts (Chinese, Japanese, Thai, etc.), do NOT use `\b` word boundaries — just use plain strings

Example for German programming keywords:

```python
"programming": [
    # ... existing English keywords ...
    "funktion", "klasse", "schleife", "array", "variable",
    "debuggen", "kompilieren", "bereitstellen",
],
```

### Keyword-Free Detection (Future)

For a keyword-free approach, the plan is to use an LLM-based fallback that reads the conversation context and determines the topic without keyword matching. This would:
- Work for any language without manual keyword lists
- Understand nuance and context better than keyword matching
- Be slower and cost more per request

## Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `enabled` | `false` | Enable/disable the plugin |
| `default` | `owl-alpha` | Fallback model when no topic is detected |
| `provider` | `""` | LLM provider name for per-provider model mapping |
| `topics.<name>.model` | — | Generic model for this topic (any provider) |
| `topics.<name>.models.<provider>` | — | Provider-specific model override |

## Monitoring

Check that the plugin is working:

```bash
hermes logs | grep topic_detect
```

Expected output:

```
✓ TOPIC: NONE | MODEL: owl-alpha | CONFIDENCE: 0.00
✓ TOPIC: PROGRAMMING | MODEL: ring-2.6-1t | CONFIDENCE: 0.95
```

## File Structure

```
topic_detect/
├── __init__.py      # Plugin hooks (pre_llm_call, on_session_start)
├── classifier.py    # Topic classification logic and keyword signals
├── config_reader.py # YAML config parsing with multi-provider support
└── README.md        # This file
```

## Requirements

- Python 3.10+
- PyYAML or ruamel.yaml
- Hermes Agent ≥ 0.11

## License

MIT
