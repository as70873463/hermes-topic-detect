# ⚡ Hermes ARC — Adaptive Routing Core

> **Smart multi-agent orchestration for Hermes Agent.**<br>
> Routes conversations by Arena.ai-aligned topic — switching models, personas, and prompts in real time.

**English** · [ไทย](README_TH.md)

---

## What It Does

ARC watches what you're talking about and automatically:

- **Switches models** — software questions go to a software/coding model, finance questions to a business/finance model, etc.
- **Injects personas** — each topic gets a tailored system prompt (expert persona)
- **Shows a signature** — a small tag at the end of each response shows which model/topic was used

Topics are aligned with Arena.ai leaderboard categories so users can choose models by checking Arena themselves and putting their chosen model into config. ARC does **not** fetch Arena scores or choose models automatically.

If no specialized topic matches with enough confidence, ARC returns `none` and Hermes uses the main/default model. There is deliberately no `general` topic.

---

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash
```

The installer handles everything: plugin files, config, and runtime compatibility check.

Check for updates without installing:

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --check
```

Update explicitly:

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --update
```

After install, set your API key:

```bash
echo '<provider-your-use>_API_KEY=<your-key>' >> ~/.hermes/.env
hermes gateway restart
```

---

## Configuration

Minimal `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - topic_detect

topic_detect:
  enabled: true
  routing_mode: hybrid
  signature:
    enabled: true
  update_check:
    enabled: true
    # Checked once after each Hermes restart; logged only, never appended to chat.
    url: https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/plugin.yaml
    timeout_seconds: 2.5
  topics:
    software_it:
      # Arena refs: Software & IT Services, Coding
      provider: openrouter
      model: your/software-model
    business_finance:
      # Arena ref: Business, Management, & Financial Ops
      provider: openrouter
      model: your/business-finance-model
```

### Choosing Models

1. Open Arena.ai.
2. Select the leaderboard/category closest to your topic.
3. Pick the model you trust from that category.
4. Put that model into `topic_detect.topics.<topic>.model`.

ARC uses Arena as a **reference taxonomy**, not as a live data source.

### Updates

ARC has two update discovery paths:

- Manual: run installer with `--check` to compare local vs GitHub `plugin.yaml` version.
- Runtime: after Hermes restarts, ARC checks GitHub once and logs if a newer version exists. It does **not** spam user-visible chat responses.

Disable runtime checks:

```yaml
topic_detect:
  update_check:
    enabled: false
```

If a topic block is omitted, or a topic has no `provider`/`model`, ARC skips
the runtime override for that topic and Hermes keeps the main/default model.
This is intentional: categories with low specialist-model ROI can still be
classified for logging/signature without forcing a weaker route.

### Routing Modes

| Mode | Behavior |
|------|----------|
| `keyword` | Fast — keyword matching |
| `semantic` | Smart — LLM-based classification |
| `hybrid` | Recommended — keyword first, semantic fallback |

### Supported Primary Topics

- `software_it` — Arena refs: Software & IT Services, Coding
- `math` — Arena refs: Mathematical, Math
- `science` — Arena ref: Life, Physical, & Social Science
- `business_finance` — Arena ref: Business, Management, & Financial Ops
- `legal_government` — Arena ref: Legal & Government
- `medicine_healthcare` — Arena ref: Medicine & Healthcare
- `writing_language` — Arena refs: Writing/Literature/Language, Creative Writing, Language, English, Non-English, language-specific boards
- `entertainment_media` — Arena ref: Entertainment, Sports, & Media

Arena categories like Expert, Hard Prompts, Instruction Following, Multi-Turn, Longer Query, and language-specific boards are treated as modifiers/future metadata, not primary routes in this version.

Topic caveats:

- `entertainment_media` is intentionally optional. Movie/game/sports/media
  prompts often do not need a specialist model; leave its model unset if your
  main model handles these well.
- `writing_language` is broad by design and contains an internal tension:
  creative writing favors creativity/style, while translation favors
  multilingual precision. If users complain about this route later, this is the
  likely first candidate to split into subroutes or metadata-based routing.

`Exclude Ties` is a leaderboard filter and is not used by ARC.

### Provider Support

Any provider Hermes supports works as a topic target:

- **OpenRouter** — set `provider: openrouter` + `model:`
- **OpenAI-compatible** (DeepSeek, vLLM, etc.) — set `provider:` + `base_url:` + `api_key:`
- **OAuth providers** — set `provider:`, no `api_key` needed if Hermes handles auth for that provider

---

## Signature

When enabled, each response ends with a routing tag:

```text
- nemotron-3-super-120b-a12b [software_it]
- owl-alpha [business_finance]
- owl-alpha [none]
```

Disable with `signature.enabled: false`.

---

## Verify

```bash
hermes plugins list | grep topic_detect
hermes logs | grep topic_detect
```

Expected log:

```text
topic_detect: loaded
topic_detect: switching provider=openrouter model=nvidia/nemotron-3-super-120b-a12b:free
topic_detect: signature=- nemotron-3-super-120b-a12b [software_it]
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Plugin not loading | Check `plugins.enabled` contains `topic_detect` and `enabled: true`, then restart |
| Topic not switching | Lower `min_confidence` to `0.3`, or use `routing_mode: semantic` |
| Too many switches | Raise `inertia` to `3` or `4` |
| Unclear/general prompts route unexpectedly | They should return `none`; raise `min_confidence` if needed |
| Model not switching provider | Run `python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --check` and patch if needed |
| Persona not injecting | Same as above — patch Hermes core for `system_prompt` override support |

---

## License

MIT
