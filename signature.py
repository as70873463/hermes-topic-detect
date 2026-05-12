from __future__ import annotations


def short_model(model: str | None) -> str:
    short = str(model or "default").split("/")[-1]

    if ":" in short:
        short = short.split(":")[0]

    return short or "default"


def _label(topic: str | None, reason: str | None = None) -> str:
    if reason == "skip":
        return "skip"

    label = topic or "general"
    if label == "none":
        label = "general"
    return label


def build_signature(
    model: str,
    topic: str | None,
    *,
    reason: str | None = None,
) -> str:
    label = _label(topic, reason)

    return f"- {short_model(model)} [{label}]"


def build_final_signature(
    *,
    routed_model: str | None,
    final_model: str | None,
    topic: str | None,
    routed_provider: str | None = None,
    final_provider: str | None = None,
    reason: str | None = None,
) -> str:
    """Build a visible signature using the model that actually answered.

    If Hermes falls back after ARC selected a topic target, the final model can
    differ from the routed model. Put the final responder first, and preserve
    the originally routed model as context.
    """

    label = _label(topic, reason)

    final = short_model(final_model or routed_model)
    routed = short_model(routed_model)

    if reason == "skip":
        return f"- {final} [{label}]"

    if routed_model and (
        str(final_model or "") != str(routed_model or "")
        or str(final_provider or "") != str(routed_provider or "")
    ):
        return f"- {final} [{label} | routed: {routed}]"

    return f"- {final} [{label}]"
