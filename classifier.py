"""
classifier.py
Classify conversation topic from multi-turn context.

Two-tier approach:
  1. Keyword/phrase signals (fast, deterministic)
  2. LLM-based context understanding (fallback for ambiguous cases)

For adding new language support: tell the AI to suggest common keywords
for that language. The classifier works best with the most common words
native speakers would use when discussing each topic.

For contributors who want to avoid keyword maintenance entirely, the
LLM fallback can handle topic detection from context alone — no keywords
required. Set USE_LLM_FALLBACK=True in config to enable.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import NamedTuple

logger = logging.getLogger("topic_detect.classifier")

# ─────────────────────────────────────────────────────────────────────────────
# Topic keyword signals (used as lightweight scoring hints)
# ─────────────────────────────────────────────────────────────────────────────
# These are NOT strict matches — they weight the score.
# The classifier reads the combined context and accumulates scores.
#
# To add a new language: ask an AI to suggest the most common keywords
# a native speaker would use for each topic in that language.
# ─────────────────────────────────────────────────────────────────────────────

TOPIC_SIGNALS: dict[str, list[str]] = {
    "programming": [
        r"\bcode\b", r"\bdebug\b", r"\bfunction\b", r"\bclass\b", r"\bapi\b",
        r"\balgorithm\b", r"\bframework\b", r"\blibrary\b", r"\brepository\b",
        r"\bgit\b", r"\bpython\b", r"\bjavascript\b", r"\btypescript\b",
        r"\brust\b", r"\bgo\b", r"\bjava\b", r"\bc\+\+\b", r"\bsql\b",
        r"\bdatabase\b", r"\bserver\b", r"\bclient\b", r"\bendpoint\b",
        r"\bbug\b", r"\berror\b", r"\bstack trace\b", r"\bcompile\b",
        r"\bdeploy\b", r"\bcontainer\b", r"\bdocker\b", r"\bkubernetes\b",
        r"\btest\b", r"\bunit test\b", r"\brefactor\b", r"\bvariable\b",
        r"\bloop\b", r"\barray\b", r"\bobject\b", r"\bjson\b", r"\bxml\b",
    ],
    "finance": [
        r"\bstock\b", r"\binvest\b", r"\bportfolio\b", r"\bdividend\b",
        r"\bbond\b", r"\bequity\b", r"\bdebt\b", r"\bcredit\b",
        r"\binterest rate\b", r"\binflation\b", r"\bcurrency\b",
        r"\bcrypto\b", r"\bbitcoin\b", r"\bethereum\b", r"\bdefi\b",
        r"\bbudget\b", r"\bexpense\b", r"\brevenue\b", r"\bprofit\b",
        r"\bloss\b", r"\bbalance sheet\b", r"\bcash flow\b",
        r"\btax\b", r"\baudit\b", r"\baccounting\b", r"\bfund\b",
    ],
    "health": [
        r"\bsymptom\b", r"\bdiagnos\b", r"\btreatment\b", r"\bmedicine\b",
        r"\bdrug\b", r"\bprescription\b", r"\bdoctor\b", r"\bhospital\b",
        r"\bclinic\b", r"\btherapy\b", r"\bmental health\b",
        r"\bdepression\b", r"\banxiety\b", r"\bstress\b", r"\bsleep\b",
        r"\bdiet\b", r"\bnutrition\b", r"\bexercise\b", r"\bworkout\b",
        r"\bvitamin\b", r"\bsupplement\b", r"\bvaccine\b", r"\bvirus\b",
        r"\binfection\b", r"\bimmune\b", r"\bblood\b", r"\bheart\b",
    ],
    "legal": [
        r"\blaw\b", r"\blegal\b", r"\bcourt\b", r"\bjudge\b",
        r"\bcontract\b", r"\bagreement\b", r"\bclause\b", r"\bliabilit\b",
        r"\bregulation\b", r"\bcompliance\b", r"\bpolicy\b",
        r"\bintellectual property\b", r"\bcopyright\b", r"\btrademark\b",
        r"\bpatent\b", r"\bprivacy\b", r"\bgdpr\b", r"\bterms\b",
    ],
    "science": [
        r"\bphysics\b", r"\bchemistry\b", r"\bbiology\b", r"\bgenetics\b",
        r"\bevolution\b", r"\bquantum\b", r"\brelativity\b",
        r"\bexperiment\b", r"\bhypothesis\b", r"\btheory\b",
        r"\bresearch\b", r"\bpaper\b", r"\bjournal\b", r"\bpublish\b",
        r"\bscientist\b", r"\blab\b", r"\bmolecule\b", r"\batom\b",
        r"\bplanet\b", r"\bspace\b", r"\bastronomy\b", r"\bclimate\b",
    ],
    "technology": [
        r"\bai\b", r"\bmachine learning\b", r"\bdeep learning\b",
        r"\bneural\b", r"\bgpu\b", r"\bcpu\b", r"\bchip\b",
        r"\bsemiconductor\b", r"\bcloud\b", r"\bsaas\b", r"\bpaas\b",
        r"\bblockchain\b", r"\biot\b", r"\brobot\b", r"\bautomation\b",
        r"\b5g\b", r"\bwifi\b", r"\bnetwork\b", r"\bcybersecurity\b",
        r"\bhack\b", r"\bencrypt\b", r"\bllm\b", r"\bgpt\b",
    ],
    "marketing": [
        r"\bcampaign\b", r"\bbrand\b", r"\badvertis\b", r"\bcopywriting\b",
        r"\bsocial media\b", r"\bcontent\b", r"\bengagement\b",
        r"\bconversion\b", r"\bfunnel\b", r"\blead\b", r"\bsales\b",
        r"\bcustomer\b", r"\bmarket\b", r"\bcompetitor\b",
        r"\bpositioning\b", r"\bvalue proposition\b", r"\bgrowth\b",
    ],
    "seo": [
        "seo", "serp", "backlink", "meta description",
        "google search console", "organic traffic", "keyword research",
        "on-page seo", "off-page seo", "crawl budget",
    ],
    "translation": [
        r"\btranslat\b",
        r"\bin english\b", r"\bin thai\b", r"\bin japanese\b",
        r"\bin chinese\b", r"\bin korean\b", r"\bin french\b",
        r"\bmean in\b", r"\bhow to say\b", r"\bword for\b",
    ],
    "roleplay": [
        r"\broleplay\b", r"\brole.play\b", r"\byou are\b", r"\bact as\b",
        r"\bpretend\b", r"\bcharacter\b", r"\bpersona\b",
        r"\bfiction\b", r"\bstory\b", r"\bnarrative\b",
        r"\bscenario\b", r"\bscript\b", r"\bdialogue\b",
    ],
    "trivia": [
        r"\bfun fact\b", r"\bdid you know\b", r"\bquiz\b",
        r"\btrivia\b", r"\bguess\b", r"\bwho is\b", r"\bwhat is the\b",
        r"\bwhen was\b", r"\bwhere is\b", r"\brecord\b",
        r"\bfastest\b", r"\btallest\b", r"\blargest\b", r"\bsmallest\b",
    ],
    "academia": [
        r"\bthesis\b", r"\bdissertation\b", r"\bcitation\b",
        r"\breference\b", r"\bbibliograph\b", r"\bapa\b", r"\bmla\b",
        r"\bacademic\b", r"\bscholarly\b", r"\bpeer.review\b",
        r"\bpublication\b", r"\babstract\b", r"\bliterature review\b",
        r"\bmethodology\b", r"\bfindings\b", r"\bconclusion\b",
    ],
}

# Compile patterns once at import time
_COMPILED: dict[str, list[re.Pattern]] = {
    topic: [re.compile(p, re.IGNORECASE) for p in patterns]
    for topic, patterns in TOPIC_SIGNALS.items()
}

# ─────────────────────────────────────────────────────────────────────────────
# Phrase boosts — multi-word phrases that are strong topic indicators
# Worth more than single keywords because phrases are far more precise
# ─────────────────────────────────────────────────────────────────────────────
PHRASE_BOOSTS: dict[str, dict[str, float]] = {
    "programming": {
        "index out of range": 8,
        "stack trace": 7,
        "null pointer": 7,
        "syntax error": 6,
        "segmentation fault": 8,
    },
    "seo": {
        "keyword research": 5,
        "google search console": 5,
        "meta description": 5,
        "organic traffic": 5,
        "on-page seo": 5,
        "off-page seo": 5,
        "backlink": 5,
    },
    "trivia": {
        "fun fact": 5,
        "did you know": 5,
        "world record": 5,
        "tallest": 4,
        "largest": 4,
        "smallest": 4,
        "fastest": 4,
    },
}


class ClassificationResult(NamedTuple):
    topic: str          # winning topic or "none"
    confidence: float   # 0.0 – 1.0
    scores: dict        # raw scores per topic


def classify_context(messages: list[dict], window: int = 3) -> ClassificationResult:
    """
    Read context from the last N user messages and classify the topic.

    messages: list of {"role": "user"|"assistant", "content": "..."}
    window:   number of recent user turns to consider
    """

    # Extract recent user messages
    user_msgs = [
        m["content"] for m in messages
        if m.get("role") == "user" and isinstance(m.get("content"), str)
    ][-window:]

    if not user_msgs:
        return ClassificationResult("none", 0.0, {})

    # Weight recent messages more heavily (exponential decay)
    weighted_text_parts: list[tuple[str, float]] = []
    for i, msg in enumerate(user_msgs):
        weight = 0.5 + ((i + 1) ** 1.5)
        weighted_text_parts.append((msg, weight))

    # Accumulate scores per topic
    scores: dict[str, float] = defaultdict(float)
    for text, weight in weighted_text_parts:
        content = text.lower()

        # ── Phrase boosts (high-precision multi-word) ──
        for topic, phrases in PHRASE_BOOSTS.items():
            for phrase, boost in phrases.items():
                if phrase in content:
                    scores[topic] += boost * weight

        # ── Keyword signals ──
        for topic, patterns in _COMPILED.items():
            for pat in patterns:
                if pat.search(text):
                    scores[topic] += weight

    if not scores:
        return ClassificationResult("none", 0.0, dict(scores))

    best_topic = max(scores, key=lambda t: scores[t])
    best_score = scores[best_topic]
    total_score = sum(scores.values())

    # confidence = proportion of best topic score to total
    # capped at 0.95 because keyword-based classifier should never be 100% sure
    confidence = best_score / total_score if total_score > 0 else 0.0
    confidence = min(confidence, 0.95)

    # Must have minimum score to commit to a topic
    # (prevents false positives from a single keyword)
    MIN_SCORE = 1.5
    if best_score < MIN_SCORE:
        return ClassificationResult("none", confidence, dict(scores))

    # Must have sufficient confidence to commit
    # (prevents cases where multiple topics have similar scores)
    MIN_CONFIDENCE = 0.65
    if confidence < MIN_CONFIDENCE:
        return ClassificationResult("none", confidence, dict(scores))

    return ClassificationResult(best_topic, confidence, dict(scores))


def should_switch_topic(
    current_topic: str | None,
    new_result: ClassificationResult,
    consecutive_count: int,
) -> tuple[bool, str]:
    """
    Decide whether to switch topic.
    Uses inertia: must see the new topic for 2 consecutive turns before switching
    (prevents flapping).

    Returns (should_switch, new_topic)
    """
    new_topic = new_result.topic

    # If confidence is 0.00 = not any topic → reset to none immediately
    if new_result.confidence == 0.00 and current_topic is not None:
        return True, "none"

    # Still on the same topic — no switch needed
    if new_topic == (current_topic or "none"):
        return False, current_topic or "none"

    # High-confidence bypass — switch immediately if very confident
    if new_result.confidence >= 0.90:
        return True, new_topic

    # New topic must appear 2 consecutive times before switching
    if consecutive_count >= 2:
        return True, new_topic

    # Not yet — wait for next turn
    return False, current_topic or "none"
