"""
config_reader.py
Load topic_detect configuration from ~/.hermes/config.yaml
and resolve provider credentials from ~/.hermes/.env

Config format:
    topic_detect:
      enabled: true
      provider: openrouter
      default: owl-alpha
      base_url: https://openrouter.ai/api/v1     # optional override
      topics:
        programming:
          model: ring-2.6-1t:free
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("topic_detect.config_reader")

_DEFAULT_CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"
_DEFAULT_ENV_PATH = Path.home() / ".hermes" / ".env"

# ─────────────────────────────────────────────────────────────────────────────
# Provider credential mapping — known providers
# Key: provider name used in config → env var names for key/url
# ─────────────────────────────────────────────────────────────────────────────
_PROVIDER_ENV_MAP: dict[str, dict] = {
    "openrouter": {
        "api_key": "OPENROUTER_API_KEY",
        "base_url": "OPENROUTER_BASE_URL",
        "default_base_url": "https://openrouter.ai/api/v1",
    },
    "together": {
        "api_key": "TOGETHER_API_KEY",
        "base_url": "TOGETHER_BASE_URL",
        "default_base_url": "https://api.together.xyz/v1",
    },
    "groq": {
        "api_key": "GROQ_API_KEY",
        "base_url": "GROQ_BASE_URL",
        "default_base_url": "https://api.groq.com/openai/v1",
    },
    "anthropic": {
        "api_key": "ANTHROPIC_API_KEY",
        "base_url": "ANTHROPIC_BASE_URL",
        "default_base_url": "https://api.anthropic.com",
    },
    "openai": {
        "api_key": "OPENAI_API_KEY",
        "base_url": "OPENAI_BASE_URL",
        "default_base_url": "https://api.openai.com/v1",
    },
    "local": {
        "api_key": None,
        "base_url": "LOCAL_BASE_URL",
        "default_base_url": "http://localhost:8000/v1",
    },
}

# Aliases — user-friendly names that map to known providers
_PROVIDER_ALIASES: dict[str, str] = {
    "groq": "groq",
    "ollama": "local",
    "lmstudio": "local",
    "vllm": "local",
    "openai": "openai",
    "anthropic": "anthropic",
}


def _load_env(path: Path | None = None) -> dict[str, str]:
    """
    Load .env file and return key-value pairs.
    Supports KEY=VALUE format, ignores comments (#) and blank lines.
    """
    env_path = path or _DEFAULT_ENV_PATH
    env_vars: dict[str, str] = {}

    if not env_path.exists():
        logger.debug("No .env file found at %s", env_path)
        return env_vars

    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key:
                        env_vars[key] = value
    except Exception as e:
        logger.warning("Failed to read .env: %s", e)

    return env_vars


def _load_yaml(path: Path) -> dict:
    """Load YAML file — supports both PyYAML and ruamel.yaml"""
    try:
        import yaml
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        pass

    try:
        from ruamel.yaml import YAML
        yaml = YAML()
        with open(path, encoding="utf-8") as f:
            return dict(yaml.load(f) or {})
    except ImportError:
        logger.error("No yaml library found — install PyYAML or ruamel.yaml")
        return {}


class ProviderCredentials:
    """Resolved provider credentials (api_key + base_url)."""

    def __init__(self, provider: str, env_vars: dict[str, str], config_base_url: str = ""):
        self.provider = provider
        self.api_key: str | None = None
        self.base_url: str = ""

        # Resolve actual provider name (handle aliases)
        real_provider = _PROVIDER_ALIASES.get(provider, provider)
        mapping = _PROVIDER_ENV_MAP.get(real_provider)

        if not mapping:
            # Unknown/custom provider — try config-level base_url or env
            if config_base_url:
                self.base_url = config_base_url
            else:
                # Try env var matching provider name: e.g. provider "myapi" → "MYAPI_BASE_URL"
                env_key = f"{provider.upper()}_BASE_URL"
                self.base_url = env_vars.get(env_key) or os.environ.get(env_key, "")
            logger.info("Using custom provider '%s' with base_url: %s", provider, self.base_url)
            return

        # Known provider — resolve API key
        if mapping.get("api_key"):
            env_key = mapping["api_key"]
            self.api_key = env_vars.get(env_key) or os.environ.get(env_key)

        # Resolve base URL: config override > env var > default
        if config_base_url:
            self.base_url = config_base_url
        elif mapping.get("base_url"):
            env_key = mapping["base_url"]
            self.base_url = (
                env_vars.get(env_key)
                or os.environ.get(env_key)
                or mapping.get("default_base_url", "")
            )

    @property
    def is_configured(self) -> bool:
        """Check if this provider has minimum credentials."""
        if self.provider in ("local", "ollama", "lmstudio", "vllm"):
            return bool(self.base_url)
        return bool(self.api_key and self.base_url)

    def __repr__(self) -> str:
        key_preview = (
            f"{self.api_key[:8]}..."
            if self.api_key and len(self.api_key) > 8
            else "None"
        )
        return (
            f"ProviderCredentials(provider={self.provider!r}, "
            f"api_key={key_preview}, base_url={self.base_url!r})"
        )


class TopicDetectConfig:
    """
    Configuration for the topic_detect plugin.
    """

    def __init__(self, raw: dict, env_vars: dict[str, str] | None = None):
        self.enabled: bool = bool(raw.get("enabled", False))
        self.default_model: str = raw.get("default", "")
        self.provider: str = raw.get("provider", "")
        # Optional config-level base_url override (takes precedence over .env)
        self._config_base_url: str = raw.get("base_url", "")
        self._env_vars = env_vars or {}

        # topics: { "finance": "model_string", ... }
        self.topics: dict[str, str] = {}
        # per-provider overrides: { "finance": { "openrouter": "model", ... }, ... }
        self._provider_models: dict[str, dict[str, str]] = {}

        for topic_name, topic_cfg in (raw.get("topics") or {}).items():
            topic_key = topic_name.lower()
            if isinstance(topic_cfg, dict):
                self.topics[topic_key] = topic_cfg.get("model", "")
                if "models" in topic_cfg and isinstance(topic_cfg["models"], dict):
                    self._provider_models[topic_key] = {
                        k.lower(): v for k, v in topic_cfg["models"].items()
                    }
            elif isinstance(topic_cfg, str):
                self.topics[topic_key] = topic_cfg

        # Resolve provider credentials
        self.credentials = ProviderCredentials(
            self.provider, self._env_vars, self._config_base_url
        )

    def resolve_model(self, topic: str) -> str:
        """
        Resolve the best model for the given topic.

        Resolution order:
        1. Per-provider model mapping (if provider is set)
        2. Generic model string
        3. Default model
        """
        topic_key = topic.lower()

        # 1. Try per-provider mapping
        if self.provider and topic_key in self._provider_models:
            provider_map = self._provider_models[topic_key]
            if self.provider in provider_map:
                return provider_map[self.provider]

        # 2. Try generic model
        if topic_key in self.topics and self.topics[topic_key]:
            return self.topics[topic_key]

        # 3. Fallback to default
        return self.default_model

    def model_for_topic(self, topic: str) -> str | None:
        """Return model string for the given topic, or None if not found"""
        model = self.resolve_model(topic)
        return model if model else None

    def short_model_name(self, model: str) -> str:
        """
        Extract short name from full model string:
        'inclusionai/ring-2.6-1t:free'  →  'ring-2.6-1t'
        'openrouter/owl-alpha'          →  'owl-alpha'
        """
        name = model.split("/")[-1]
        name = name.split(":")[0]
        return name

    def __repr__(self) -> str:
        return (
            f"TopicDetectConfig(enabled={self.enabled}, "
            f"default={self.default_model!r}, "
            f"provider={self.provider!r}, "
            f"topics={list(self.topics.keys())})"
        )


def load_config(
    config_path: Path | None = None,
    env_path: Path | None = None,
) -> TopicDetectConfig:
    """
    Load config.yaml + .env and return TopicDetectConfig.
    Returns disabled config if file or topic_detect section is missing.
    """
    cfg_path = config_path or _DEFAULT_CONFIG_PATH

    # Load .env first
    env_vars = _load_env(env_path)

    if not cfg_path.exists():
        logger.warning("Config file not found at %s", cfg_path)
        return TopicDetectConfig({}, env_vars)

    try:
        raw_cfg = _load_yaml(cfg_path)
        raw_topic = raw_cfg.get("topic_detect") or {}
        cfg = TopicDetectConfig(raw_topic, env_vars)
        logger.debug("Loaded topic_detect config: %s", cfg)
        logger.debug("Provider credentials: %s", cfg.credentials)
        return cfg
    except Exception as e:
        logger.error("Failed to load config.yaml: %s", e)
        return TopicDetectConfig({}, env_vars)