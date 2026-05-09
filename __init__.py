from __future__ import annotations
import logging
from .classifier import classify_context, should_switch_topic
from .config_reader import load_config

logger = logging.getLogger("topic_detect")


class _State:
    def __init__(self):
        self.reset()

    def reset(self):
        self.current_topic: str | None = None
        self.current_model: str | None = None
        self.pending_topic: str | None = None
        self.consecutive_count: int = 0


_state = _State()
_config = None


def _get_config():
    global _config
    if _config is None:
        _config = load_config()
    return _config


def _pre_llm_call(**kwargs):
    cfg = _get_config()
    if not cfg.enabled:
        return None

    history = kwargs.get("conversation_history") or []
    user_msg = kwargs.get("user_message") or ""

    messages = []
    for entry in history:
        if isinstance(entry, dict):
            messages.append(entry)
    if isinstance(user_msg, str) and user_msg:
        messages.append({"role": "user", "content": user_msg})

    if not messages:
        return None

    result = classify_context(messages, window=3)

    new_topic = result.topic
    if new_topic == (_state.pending_topic or "none"):
        _state.consecutive_count += 1
    else:
        _state.pending_topic = new_topic
        _state.consecutive_count = 1

    should_switch, resolved_topic = should_switch_topic(
        current_topic=_state.current_topic,
        new_result=result,
        consecutive_count=_state.consecutive_count,
    )

    if should_switch:
        _state.current_topic = resolved_topic
        _state.consecutive_count = 0
        _state.pending_topic = None

    active_topic = _state.current_topic or "none"
    if active_topic == "none":
        target_model = cfg.default_model
    else:
        target_model = cfg.resolve_model(active_topic) or cfg.default_model

    _state.current_model = target_model

    short_name = target_model.split("/")[-1] if "/" in target_model else target_model
    short_name = short_name.split(":")[0]

    logger.info(
        "✓ TOPIC: %s | MODEL: %s | CONFIDENCE: %.2f",
        active_topic.upper(),
        short_name,
        result.confidence,
    )

    # Return context dict — Hermes injects this into the user message.
    # This is the ONLY supported return format for pre_llm_call hooks.
    if active_topic != "none":
        sig = f"— {short_name} [{active_topic}]"
        context_text = (
            f"[topic_detect] Detected topic: {active_topic}. "
            f"Active model: {short_name}. "
            f"Confidence: {result.confidence:.2f}. "
            f"End your response with: {sig}"
        )
        logger.info("SIG: %s [%s]", short_name, active_topic)
        return {"context": context_text}

    return None


def _on_session_start(**kwargs):
    global _config
    _state.reset()
    _config = None


def register(ctx):
    cfg = _get_config()
    if not cfg.enabled:
        return
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("on_session_reset", _on_session_start)
    logger.info("topic_detect plugin loaded")
