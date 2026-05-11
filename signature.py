from __future__ import annotations


def build_signature(
    model: str,
    topic: str | None,
) -> str:
    short = model.split("/")[-1]

    if ":" in short:
        short = short.split(":")[0]

    label = topic or "general"
    if label == "none":
        label = "general"

    return f"- {short} [{label}]"
