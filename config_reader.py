"""
config_reader.py
Load topic_detect configuration from ~/.hermes/config.yaml
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("topic_detect.config_reader")

_DEFAULT_CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"


def _load_yaml(path: Path) -> dict:
    """Load YAML file — supports both PyYAML and ruamel.yaml"""
    try:
        import yaml  # PyYAML

        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        pass

    try:
        from ruamel.yaml import YAML  # ruamel (bundled with Hermes)

        yaml = YAML()
        with open(path, encoding="utf-8") as f:
            return dict(yaml.load(f) or {})
    except ImportError:
        logger.error("No yaml library found — install PyYAML or ruamel.yaml")
        return {}


class TopicDetectConfig:
    """
    Configuration structure from config.yaml topic_detect section:

    topic_detect:
      enabled: true
      default: openrouter/owl-alpha
      topics:
        finance:
          model: inclusionai/ring-2.6-1t:free
        programming:
          model: inclusionai/ring-2.6-1t:free
        ...
    """

    def __init__(self, raw: dict):
        self.enabled: bool = bool(raw.get("enabled", False))
        self.default_model: str = raw.get("default", "")
        # topics: { "finance": "model_string", ... }
        self.topics: dict[str, str] = {}
        for topic_name, topic_cfg in (raw.get("topics") or {}).items():
            if isinstance(topic_cfg, dict) and "model" in topic_cfg:
                self.topics[topic_name.lower()] = topic_cfg["model"]

    def model_for_topic(self, topic: str) -> str | None:
        """Return model string for the given topic, or None if not found"""
        return self.topics.get(topic.lower())

    def short_model_name(self, model: str) -> str:
        """
        Extract short name from full model string:
        'inclusionai/ring-2.6-1t:free'  →  'ring-2.6-1t'
        'openrouter/owl-alpha'          →  'owl-alpha'
        'baidu/cobuddy:free'            →  'cobuddy'
        """
        name = model.split("/")[-1]
        name = name.split(":")[0]
        return name

    def __repr__(self) -> str:
        return (
            f"TopicDetectConfig(enabled={self.enabled}, "
            f"default={self.default_model!r}, "
            f"topics={list(self.topics.keys())})"
        )


def load_config(config_path: Path | None = None) -> TopicDetectConfig:
    """
    Load config.yaml and return TopicDetectConfig.
    Returns disabled config if file or topic_detect section is missing.
    """
    path = config_path or _DEFAULT_CONFIG_PATH

    if not path.exists():
        logger.warning("Config file not found at %s", path)
        return TopicDetectConfig({})

    try:
        raw_cfg = _load_yaml(path)
        raw_topic = raw_cfg.get("topic_detect") or {}
        cfg = TopicDetectConfig(raw_topic)
        logger.debug("Loaded topic_detect config: %s", cfg)
        return cfg
    except Exception as e:
        logger.error("Failed to load config.yaml: %s", e)
        return TopicDetectConfig({})