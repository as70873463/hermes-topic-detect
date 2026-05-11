# ⚡ Hermes ARC — Adaptive Routing Core

> **Smart multi-agent orchestration for Hermes Agent.**<br>
> Routes conversations by topic — switching models, personas, and prompts in real time.

**English** · [ไทย](README_TH.md)

---

## What It Does

ARC watches what you're talking about and automatically:

- **Switches models** — coding questions go to a coding model, finance questions to a finance model
- **Injects personas** — each topic gets a tailored system prompt (expert persona)
- **Shows a signature** — a small tag at the end of each response shows which model/topic was used

Topics don't flip instantly. ARC accumulates confidence across turns, so routing feels natural instead of jumpy.

---

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash
```

The installer handles everything: plugin files, config, and runtime compatibility check.

After install, set your API key:

```bash
echo '<provider>_API_KEY=<your-key>' >> ~/.hermes/.env
hermes gateway restart
```

---

## Configuration

Minimal `~/.hermes/config.yaml`:

```yaml
plugins:
  - topic_detect

topic_detect:
  enabled: true
  routing_mode: hybrid
  signature:
    enabled: true
  topics:
    programming:
      provider: openrouter
      model: inclusionai/ring-2.6-1t:free
    finance:
      provider: openrouter
      model: openrouter/owl-alpha
```

That's it. ARC works out of the box with sensible defaults. The installer fills in the rest.

### Routing Modes

| Mode | Behavior |
|------|----------|
| `keyword` | Fast — keyword matching |
| `semantic` | Smart — LLM-based classification |
| `hybrid` | Recommended — keyword first, semantic fallback |

### Supported Topics

`programming` · `finance` · `marketing` · `translation` · `legal` · `health` · `roleplay` · `seo` · `science` · `technology` · `academia` · `trivia`

Each topic has a built-in expert persona loaded from `AGENTS.md`.

### Provider Support

Any provider Hermes supports works as a topic target:

- **OpenRouter** — set `provider: openrouter` + `model:`
- **OpenAI-compatible** (DeepSeek, vLLM, etc.) — set `provider:` + `base_url:` + `api_key:`
- **OAuth providers** (OpenAI Codex, Anthropic) — set `provider:`, no `api_key` needed

You don't need `api_key` in config for OAuth providers — Hermes handles auth.

---

## Signature

When enabled, each response ends with a routing tag:

```
- ring-2.6-1t [programming]
- owl-alpha [finance]
- ring-2.6-1t [programming → finance]
```

Disable with `signature.enabled: false`.

---

## Verify

```bash
hermes plugins list | grep topic_detect
hermes logs | grep topic_detect
```

Expected log:

```
topic_detect: loaded
topic_detect: switching provider=openrouter model=inclusionai/ring-2.6-1t:free
topic_detect: signature=- ring-2.6-1t [programming]
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Plugin not loading | Check `plugins: [topic_detect]` and `enabled: true` in config, then restart |
| Topic not switching | Lower `min_confidence` to `0.3`, or use `routing_mode: semantic` |
| Too many switches | Raise `inertia` to `3` or `4` |
| Model not switching provider | Run `python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --check` and patch if needed |
| Persona not injecting | Same as above — patch Hermes core for `system_prompt` override support |

---

## License

MIT
