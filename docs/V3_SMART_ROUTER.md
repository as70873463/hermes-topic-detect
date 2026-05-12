# ARC v3 Smart Router Direction

ARC v2 is intentionally narrow: intent/action-first routing with a configurable topic-to-model map. v3 should become a broader smart-router layer.

## Goal

Choose the best configured model/provider for a turn using more than topic keywords.

A useful v3 router should consider:

- task/action type
- subject/domain
- prompt complexity
- required reasoning depth
- expected tool/subagent use
- latency preference
- cost preference
- privacy/local-vs-cloud preference
- available local hardware and runtimes
- provider availability / fallback state

## Candidate Architecture

```text
request context
  → feature extraction
      - action / intent
      - subject / topic
      - complexity score
      - privacy / locality signals
      - resource inventory
  → routing policy
      - user preferences
      - model capability registry
      - cost / latency budget
      - fallback and availability state
  → runtime override
      - model
      - provider
      - base_url / api_mode
  → final-model-aware signature
```

## Resource / Capability Inventory

A future Hermes-native router should be able to query:

- CPU / RAM
- GPU / VRAM
- installed local runtimes such as llama.cpp, vLLM, Ollama, LM Studio, etc.
- configured remote providers
- rough latency / cost / rate-limit availability

This enables decisions such as:

- simple private task → local small model if available
- hard coding/math/reasoning → stronger configured model
- cheap background task → lower-cost/free provider
- no suitable local hardware → remote provider fallback

## External Router Integration

External routers such as Manifest-style systems can provide complexity or intelligence-level estimates. ARC should treat those as optional signals rather than replacing user-configured policy.

Useful integration shape:

```text
external_router.score(prompt, context) -> {
  "complexity": 0.0-1.0,
  "recommended_tier": "small|medium|large",
  "latency_sensitive": bool,
  "privacy_sensitive": bool,
}
```

## Non-goals for v2

Do not turn v2 into the full smart router. v2 should remain stable as a reference implementation for:

- runtime model override
- action-first routing
- final-model-aware signatures
- patch-free migration after upstream runtime override support lands

## Open Questions

- Should complexity scoring be local, LLM-based, or external-router-based?
- How should users describe model capability and cost metadata?
- Should routing policy be declarative YAML, Python plugin code, or both?
- How should router decisions be exposed in logs/signatures without making replies noisy?
- How should provider rate limits and credential-pool state influence routing?
