from __future__ import annotations

from pathlib import Path


DEFAULT_AGENTS_FILE = (
    Path.home()
    / ".hermes"
    / "plugins"
    / "topic_detect"
    / "AGENTS.md"
)


def load_agents(
    path: str | None = None,
) -> dict[str, str]:
    p = (
        Path(path).expanduser()
        if path
        else DEFAULT_AGENTS_FILE
    )

    if not p.exists():
        return {}

    text = p.read_text(
        encoding="utf-8",
    )

    agents: dict[str, list[str]] = {}

    current: str | None = None

    for line in text.splitlines():
        stripped = line.strip()

        # Topic header
        if stripped.startswith("# "):
            current = (
                stripped[2:]
                .strip()
                .lower()
            )

            agents[current] = []

            continue

        # Section separator
        if stripped == "---":
            current = None
            continue

        # Collect lines
        if current:
            agents[current].append(line)

    return {
        topic: "\n".join(lines).strip()
        for topic, lines in agents.items()
        if "\n".join(lines).strip()
    }


def get_agent_prompt(
    topic: str | None,
    path: str | None = None,
) -> str | None:
    if not topic or topic == "none":
        return None

    agents = load_agents(path)

    return agents.get(topic)
