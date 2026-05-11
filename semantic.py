from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass


@dataclass
class SemanticResult:
    topic: str
    confidence: float
    reason: str


# Primary routing topics aligned to Arena.ai leaderboard categories.
# "none" means: do not override; let Hermes use the main/default model.
TOPICS = [
    "software_it",
    "math",
    "science",
    "business_finance",
    "legal_government",
    "medicine_healthcare",
    "writing_language",
    "entertainment_media",
    "none",
]

TOPIC_GUIDE = """
software_it: Arena refs Software & IT Services, Coding. Code, debugging, software engineering, IT, DevOps, infrastructure, APIs, databases, Hermes/plugins.
math: Arena refs Mathematical, Math. Mathematics, formal logic, proofs, statistics, quantitative reasoning, calculations, optimization.
science: Arena ref Life, Physical, & Social Science. Physics, chemistry, biology, social science, academic/scientific research.
business_finance: Arena ref Business, Management, & Financial Ops. Business, finance, accounting, investing, management, operations, marketing, SEO, economics.
legal_government: Arena ref Legal & Government. Law, contracts, regulation, policy, compliance, government.
medicine_healthcare: Arena ref Medicine & Healthcare. Medical/healthcare information, symptoms, diagnosis discussion, treatment, drugs, clinical topics.
writing_language: Arena refs Writing/Literature/Language, Creative Writing, Language, English, Non-English, language-specific boards. Writing, rewriting, translation, grammar, literature, creative writing, roleplay.
entertainment_media: Arena ref Entertainment, Sports, & Media. Movies, anime, games, sports, music, celebrities, media, pop culture.
none: no specialized Arena-aligned category is clear enough; use this instead of inventing a general category.
""".strip()


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
Classify the user's conversation into ONE primary Arena.ai-aligned routing topic.

Allowed topics:
{", ".join(TOPICS)}

Topic guide:
{TOPIC_GUIDE}

Important rules:
- Do not use a general topic. If no specialized category is clear, return "none".
- Expert, Hard Prompts, Instruction Following, Multi-Turn, Longer Query, and language-specific boards are modifiers/future metadata, not primary topics here.
- Prefer the domain/topic over the task shape. Example: "debug this Python API" = software_it, not instruction_following.
- Return JSON only.

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
                "content": "You are a strict Arena.ai-aligned topic classifier. Return JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0,
        "max_tokens": 160,
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

        raw_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Some OpenAI-compatible providers return content as a list of typed
        # blocks instead of a plain string. Normalize before `.strip()` so the
        # semantic classifier fails gracefully instead of raising AttributeError.
        if isinstance(raw_content, list):
            parts: list[str] = []
            for item in raw_content:
                if isinstance(item, dict):
                    value = item.get("text") or item.get("content") or ""
                    if isinstance(value, str):
                        parts.append(value)
                elif isinstance(item, str):
                    parts.append(item)
            raw_content = "\n".join(parts)

        if raw_content is None:
            raw_content = ""

        content = str(raw_content).strip()

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
