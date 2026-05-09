# hermes-topic-detect

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green)
![Hermes](https://img.shields.io/badge/Hermes-%E2%89%A50.11-orange)

A Hermes Agent plugin that automatically detects conversation topics and routes responses to the most appropriate LLM model based on context.

---

## Quick Start

```bash
# 1. Install (one command)
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-topic-detect/main/install.sh | bash

# 2. Enable the plugin
hermes plugins enable topic_detect

# 3. Add config to ~/.hermes/config.yaml (see Configuration below)

# 4. Restart Hermes
sudo systemctl restart hermes

# 5. Verify it's working
hermes logs | grep topic_detect
```

Expected output:
```
topic_detect plugin loaded
✓ TOPIC: NONE | MODEL: owl-alpha | CONFIDENCE: 0.00
```

> 🇹🇭 **Thai version** (English + Thai keywords):
> ```bash
> curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-topic-detect/thai/install-thai.sh | bash
> ```

---

## Features

- **Automatic topic detection** — classifies user messages into 12 topics using keyword signals and phrase boosts
- **Model routing** — switches the active LLM model based on the detected topic
- **Multi-provider support** — works with OpenRouter, Together AI, Groq, Anthropic, OpenAI, or local models
- **Inertia logic** — requires 2 consecutive turns of the same topic before switching (prevents flapping)
- **High-confidence bypass** — switches immediately when confidence ≥ 0.90
- **Zero-confidence reset** — resets to default model when confidence is 0.00
- **Signature injection** — injects instruction into prompt so LLM outputs model/topic info (guaranteed delivery across all platforms)
- **Multi-language keyword support** — easy to add keywords for any language

---

## Supported Topics

| Topic | Default Model | Use Case |
|-------|---------------|----------|
| programming | ring-2.6-1t | Code debugging, architecture, algorithms |
| finance | ring-2.6-1t | Stocks, investing, budgets, financial planning |
| science | ring-2.6-1t | Physics, biology, chemistry, research |
| academia | ring-2.6-1t | Theses, citations, scholarly writing |
| health | owl-alpha | Medical, symptoms, fitness, nutrition |
| legal | owl-alpha | Contracts, laws, compliance, rights |
| seo | owl-alpha | Search ranking, keywords, backlinks |
| translation | owl-alpha | Language conversion, word meanings |
| technology | owl-alpha | AI, hardware, software, gadgets |
| marketing | cobuddy | Campaigns, branding, copywriting |
| roleplay | cobuddy | Character play, fiction, personas |
| trivia | cobuddy | Fun facts, quizzes, games |
| *none (default)* | owl-alpha | General conversation |

---

## How to See It In Action

Ask Hermes a programming question twice in a row:

### Turn 1:
```
help me debug this python code
```
→ Plugin classifies as programming (confidence 0.83)
→ Status: pending (waiting for confirmation)
→ Model: still default

### Turn 2:
```
getting an error in the loop
```
→ Plugin confirms programming (confidence 0.95)
→ Status: confirmed (2 consecutive turns)
→ Model: switches to ring-2.6-1t

### Check Logs
```bash
hermes logs | grep topic_detect
```

Expected output:
```
✓ TOPIC: PROGRAMMING | MODEL: ring-2.6-1t | CONFIDENCE: 0.95
```

---

## Installation

### Automatic (Recommended)

**Universal version** (English keywords only):
```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-topic-detect/main/install.sh | bash
```

**Thai version** (English + Thai keywords):
```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-topic-detect/thai/install-thai.sh | bash
```

### Manual Install

**Universal:**
```bash
git clone --depth 1 https://github.com/ShockShoot/hermes-topic-detect.git /tmp/topic-detect
cp -r /tmp/topic-detect/topic_detect/ ~/.hermes/plugins/topic_detect/
```

**Thai:**
```bash
git clone --depth 1 --branch thai https://github.com/ShockShoot/hermes-topic-detect.git /tmp/topic-detect
cp -r /tmp/topic-detect/topic_detect/ ~/.hermes/plugins/topic_detect/
```

---

## Configuration

### Step 1: Enable the Plugin in Hermes

```bash
hermes plugins enable topic_detect
```

Or manually add to `~/.hermes/config.yaml`:
```yaml
plugins:
  - topic_detect
```

> ⚠️ **This step is required!** Without this, Hermes will not load the plugin.

### Step 2: Add topic_detect Config Block

Add to `~/.hermes/config.yaml`:

#### Simple Configuration (Single Model Per Topic)

Works with any LLM provider:

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

#### Advanced Configuration (Per-Provider Model Mapping)

Use this if different users run the plugin with different LLM providers:

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

**Model Resolution Order:**
1. `models.<provider>` — if `provider` field is set and per-provider mapping exists
2. `model` — generic fallback (works for all providers)
3. `default` — global fallback

### Step 3: Set Up Provider Credentials

Credentials are read from `~/.hermes/.env`. Add the API keys for your provider:

| Provider | API Key | Base URL (optional) | Default |
|----------|---------|---------------------|---------|
| OpenRouter | `OPENROUTER_API_KEY` | `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` |
| Together AI | `TOGETHER_API_KEY` | `TOGETHER_BASE_URL` | `https://api.together.xyz/v1` |
| Groq | `GROQ_API_KEY` | `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` |
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_BASE_URL` | `https://api.openai.com/v1` |
| Local | *(none needed)* | `LOCAL_BASE_URL` | `http://localhost:8000/v1` |

Example `~/.hermes/.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

If a base URL env var is not set, the default is used automatically.

### Step 4: Restart Hermes

```bash
sudo systemctl restart hermes
```

> ⚠️ **Required!** Plugin is loaded at startup. Changes to config or plugin files require a restart.

---

## Signature Injection Explained

### What Happens

The plugin injects a CRITICAL INSTRUCTION into the user message before LLM inference:

```
[REQUIRED: End your response with exactly: — ring-2.6-1t [programming]]
```

This forces the LLM to output the signature directly (not post-processed).

### Why Injected, Not Appended?

Post-processing fails on some platforms:
- Telegram, Discord, and some integrations ignore response modifications
- They only see what the LLM actually generated

Injection guarantees delivery:
- Signature is part of the prompt → LLM generates it → all platforms see it
- No post-processing required → no platform-specific failures

---

## Monitoring

### Check if Plugin Loaded

```bash
hermes logs | grep topic_detect
```

Expected output:
```
topic_detect plugin loaded
✓ TOPIC: NONE | MODEL: owl-alpha | CONFIDENCE: 0.00
```

### Watch Live Classification

Run this while chatting with Hermes:

```bash
hermes logs --follow | grep "TOPIC:"
```

Example output as you chat:
```
✓ TOPIC: NONE | MODEL: owl-alpha | CONFIDENCE: 0.00
✓ TOPIC: PROGRAMMING | MODEL: ring-2.6-1t | CONFIDENCE: 0.83
✓ TOPIC: PROGRAMMING | MODEL: ring-2.6-1t | CONFIDENCE: 0.95    ← model switched!
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Plugin not loading | 1. Add `topic_detect` to `plugins:` list in config.yaml<br>2. Set `enabled: true` in `topic_detect:` block<br>3. Restart Hermes: `sudo systemctl restart hermes` |
| No topic detection | Check `hermes logs \| grep topic_detect` for errors |
| Model not switching | Normal behavior — plugin requires 2 consecutive turns of same topic before switching (prevents flapping) |
| Thai keywords not working | Use the Thai version: `curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-topic-detect/thai/install-thai.sh \| bash` |
| Signature not appearing | 1. Check `provider` field matches your LLM provider<br>2. Verify config syntax is correct<br>3. Restart Hermes |
| Config not taking effect | Always restart after editing: `sudo systemctl restart hermes` |

---

## How It Works Under the Hood

### Classification Pipeline

1. **Extract context** — reads last N user messages (configurable window, default 3)
2. **Apply weights** — recent messages count more (exponential decay backward)
3. **Score topics** using two methods:
   - **Phrase boosts** — multi-word phrases (e.g. "stack trace", "keyword research") add high weight
   - **Keyword signals** — regex patterns match individual words
4. **Calculate confidence** — ratio of best score to total score (capped at 0.95)
5. **Enforce thresholds** — minimum score (1.5) and minimum confidence (0.65) gates

### Topic Switching Logic

| Scenario | Action | Delay |
|----------|--------|-------|
| Same topic detected | No switch | — |
| Zero confidence (0.00) | Reset to default | Immediate |
| High confidence (≥ 0.90) | Switch immediately | Immediate |
| Normal confidence (0.65–0.90) | Wait for confirmation | 2 consecutive turns |

Why 2-turn inertia? Prevents flapping between topics (e.g., one sentence about code, then back to chat).

---

## Adding Keywords for New Languages

To support a new language (German, Japanese, Spanish, etc.):

1. Ask an AI model to suggest the most common words native speakers use when discussing each of the 12 topics
2. Add them to the `TOPIC_SIGNALS` dict in `classifier.py`
3. **Important for non-Latin scripts:** Do NOT use `\b` word boundaries — just use plain strings

### Example: German Programming Keywords

Edit `classifier.py`:
```python
"programming": [
    # ... existing English keywords ...
    "funktion", "klasse", "schleife", "array", "variable",
    "debuggen", "kompilieren", "bereitstellen",
],
```

### Example: Thai Health Keywords

```python
"health": [
    # ... existing English keywords ...
    "อาการ", "โรค", "ยา", "หมอ", "สุขภาพ",
    "โรงพยาบาล", "รักษา", "ปวด", "ไข้",
],
```

Then test and submit a PR! 🙌

---

## Configuration Reference

| Setting | Default | Type | Description |
|---------|---------|------|-------------|
| `enabled` | `false` | bool | Enable/disable the plugin |
| `default` | `owl-alpha` | string | Fallback model when no topic is detected |
| `provider` | `""` | string | LLM provider name (used for per-provider model mapping) |
| `topics.<name>.model` | — | string | Generic model for this topic (any provider) |
| `topics.<name>.models.<provider>` | — | string | Provider-specific model override |

---

## File Structure

```
topic_detect/
├── __init__.py      # Plugin hooks (pre_llm_call, on_session_start)
├── classifier.py    # Topic classification logic and keyword signals
├── config_reader.py # YAML config parsing with multi-provider support
├── plugin.yaml      # Plugin metadata
└── README.md        # Documentation
```

---

## Requirements

- Python 3.10+
- PyYAML or ruamel.yaml (usually bundled with Hermes)
- Hermes Agent ≥ 0.11

---

## Performance Notes

- **Classification latency:** ~5–10ms (lightweight keyword matching, no LLM call)
- **Memory overhead:** ~2MB (plugin + classifier state)
- **No API costs:** Purely local keyword-based, no external ML service calls

---

## Future Enhancements

- [ ] LLM-based fallback for keyword-free detection (supports any language without manual lists)
- [ ] Dynamic topic learning from user feedback
- [ ] Per-user topic preferences
- [ ] Topic confidence visualization in UI

---

## Contributing

Found a bug? Want to add keywords for your language? Issues and PRs welcome!

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-thing`)
3. Commit your changes (`git commit -am 'Add amazing thing'`)
4. Push to the branch (`git push origin feature/amazing-thing`)
5. Open a Pull Request

---

## Support

- 📖 Documentation: See this README and inline code comments
- 🐛 Bug reports: Open an issue on GitHub
- 💬 Questions: Discussions coming soon

---

Made with ❤️ for Hermes Agent users
