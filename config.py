from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import os
import yaml


@dataclass
class Target:
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = None
    system_prompt: str | None = None


@dataclass
class TopicDetectConfig:
    enabled: bool
    routing_mode: str

    inertia: int
    min_confidence: float

    default: Target
    topics: dict[str, Target]

    semantic_provider: str
    semantic_enabled: bool
    semantic_model: str
    semantic_confidence: float
    semantic_base_url: str
    semantic_api_key: str | None

    signature_enabled: bool

    agents_file: str | None


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value)

    return value


def _target_from_dict(data: dict[str, Any]) -> Target:
    return Target(
        provider=str(data["provider"]),
        model=str(data["model"]),
        base_url=_expand_env(data.get("base_url")),
        api_key=_expand_env(data.get("api_key")),
        system_prompt=data.get("system_prompt"),
    )


def load_config() -> TopicDetectConfig:
    path = Path.home() / ".hermes" / "config.yaml"

    raw = yaml.safe_load(path.read_text()) or {}

    section = raw.get("topic_detect", {})

    semantic = section.get("semantic", {})
    signature = section.get("signature", {})

    enabled = bool(
        section.get("enabled", True)
    )

    routing_mode = str(
        section.get("routing_mode", "hybrid")
    ).lower()

    inertia = int(
        section.get("inertia", 2)
    )

    min_confidence = float(
        section.get("min_confidence", 0.45)
    )

    semantic_enabled = bool(
        semantic.get("enabled", False)
    )

    semantic_provider = str(
        semantic.get("provider", "openrouter")
    )

    semantic_model = str(
        semantic.get("model", "openrouter/free")
    )

    semantic_confidence = float(
        semantic.get("min_confidence", 0.70)
    )

    semantic_base_url = str(
        semantic.get(
            "base_url",
            "https://openrouter.ai/api/v1",
        )
    )

    semantic_api_key = _expand_env(
        semantic.get(
            "api_key",
            "${OPENROUTER_API_KEY}",
        )
    )

    signature_enabled = bool(
        signature.get("enabled", True)
    )

    agents_file = str(
        section.get(
            "agents_file",
            "~/.hermes/plugins/topic_detect/AGENTS.md",
        )
    )

    default_data = section.get(
        "default",
        {
            "provider": raw.get(
                "provider",
                "openrouter",
            ),
            "model": raw.get(
                "model",
                "openrouter/owl-alpha",
            ),
        },
    )

    topics_data = section.get("topics", {})

    return TopicDetectConfig(
        enabled=enabled,
        routing_mode=routing_mode,

        inertia=inertia,
        min_confidence=min_confidence,

        default=_target_from_dict(default_data),

        topics={
            name: _target_from_dict(value)
            for name, value in topics_data.items()
        },

        semantic_provider=semantic_provider,
        semantic_enabled=semantic_enabled,
        semantic_model=semantic_model,
        semantic_confidence=semantic_confidence,
        semantic_base_url=semantic_base_url,
        semantic_api_key=semantic_api_key,

        signature_enabled=signature_enabled,

        agents_file=agents_file,
    )
