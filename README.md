# hermes-topic-detect

A Hermes Agent plugin that automatically detects conversation topics and routes responses to the most appropriate LLM model.

## Features

- **Automatic topic detection** — classifies user messages into 12 topics using keyword signals and phrase boosts
- **Model routing** — switches the active LLM model based on the detected topic
- **Inertia logic** — requires 2 consecutive turns of the same topic before switching (prevents flapping)
- **High-confidence bypass** — switches immediately when confidence ≥ 0.90
- **Zero-confidence reset** — resets to default model when confidence is 0.00
- **Signature injection** — injects a CRITICAL INSTRUCTION into user_message so the model appends `[topic]` to responses
- **Multi-language keyword support** — easy to add keywords for any language

## Supported Topics

| Topic | Model |
|-------|-------|
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

1. Copy the `topic_detect/` directory into your Hermes plugins folder:

```bash
cp -r topic_detect/ ~/.hermes/plugins/topic_detect/
```

2. Make sure your `~/.hermes/config.yaml` has the topic_detect section:

```yaml
topic_detect:
  enabled: true
  default: openrouter/owl-alpha
  topics:
    programming:
      model: inclusionai/ring-2.6-1t:free
    finance:
      model: inclusionai/ring-2.6-1t:free
    science:
      model: inclusionai/ring-2.6-1t:free
    academia:
      model: inclusionai/ring-2.6-1t:free
    health:
      model: openrouter/owl-alpha
    legal:
      model: openrouter/owl-alpha
    seo:
      model: openrouter/owl-alpha
    translation:
      model: openrouter/owl-alpha
    technology:
      model: openrouter/owl-alpha
    marketing:
      model: openrouter/owl-alpha
    roleplay:
      model: inclusionai/cobuddy:free
    trivia:
      model: inclusionai/cobuddy:free
```

3. Restart Hermes:

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
| `default` | `openrouter/owl-alpha` | Fallback model when no topic is detected |
| `topics.<name>.model` | — | Model to route to when this topic is detected |

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
├── config_reader.py # YAML config parsing
└── README.md        # This file
```

## Requirements

- Python 3.10+
- PyYAML or ruamel.yaml
- Hermes Agent ≥ 0.11

## License

MIT