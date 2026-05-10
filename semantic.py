from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass


@dataclass
class SemanticResult:
    topic: str
    confidence: float
    reason: str


TOPICS = [
    "programming",
    "finance",
    "translation",
    "health",
    "seo",
    "marketing",
    "science",
    "technology",
    "legal",
    "academia",
    "roleplay",
    "trivia",
    "none",
]

def semantic_classify(
    messages: list[str],
    *,
    provider: str = "openrouter",
    model: str,
    api_key: str | None,
    base_url: str = "https://openrouter.ai/api/v1",
) -> SemanticResult:

    if not api_key:
        return SemanticResult("none", 0.0, "missing_api_key")

    text = "\n".join(messages[-5:])

    prompt = f"""
Classify the user's conversation topic.

Allowed topics:
{", ".join(TOPICS)}

Return JSON only:
{{"topic":"...", "confidence":0.0, "reason":"..."}}

Conversation:
{text}
""".strip()

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a strict topic classifier. Return JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0,
        "max_tokens": 120,
    }

    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        content = data["choices"][0]["message"]["content"].strip()

        if content.startswith("```"):
            content = content.strip("`")

            if content.startswith("json"):
                content = content[4:].strip()

        start = content.find("{")
        end = content.rfind("}")

        if start >= 0 and end >= 0:
            content = content[start:end + 1]

        parsed = json.loads(content)

        topic = str(parsed.get("topic", "none")).lower()
        confidence = float(parsed.get("confidence", 0.0))
        reason = str(parsed.get("reason", ""))

        if topic not in TOPICS:
            topic = "none"
            confidence = 0.0

        return SemanticResult(topic, confidence, reason)

    except Exception as e:
        return SemanticResult("none", 0.0, f"semantic_error:{type(e).__name__}")
