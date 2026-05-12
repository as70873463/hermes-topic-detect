from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class ClassificationResult:
    topic: str
    confidence: float
    scores: dict[str, float]
    action_detected: str = "none"
    action_score: float = 0.0
    subject_detected: str = "none"
    final_route_reason: str = "none"
    debug: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionCategory:
    name: str
    priority: int
    keywords: dict[str, int]
    route: str | None = None
    negative_patterns: tuple[str, ...] = ()


TOPICS: dict[str, dict[str, int]] = {
    # Arena refs: Software & IT Services, Coding
    "software_it": {
        "python": 9,
        "javascript": 8,
        "typescript": 8,
        "php": 7,
        "java": 7,
        "c++": 7,
        "c#": 7,
        "golang": 7,
        "rust": 7,
        "swift": 6,
        "kotlin": 6,
        "code": 7,
        "coding": 8,
        "programming": 8,
        "debug": 8,
        "bug": 8,
        "traceback": 9,
        "stacktrace": 9,
        "syntax error": 9,
        "api": 7,
        "database": 7,
        "sql": 7,
        "postgres": 8,
        "mysql": 8,
        "docker": 8,
        "kubernetes": 8,
        "frontend": 7,
        "backend": 7,
        "react": 7,
        "nodejs": 7,
        "fastapi": 8,
        "django": 7,
        "flask": 7,
        "git": 6,
        "github actions": 8,
        "โค้ด": 10,
        "เขียนโค้ด": 10,
        "เขียนโปรแกรม": 10,
        "โปรแกรมมิ่ง": 9,
        "ดีบัก": 8,
        "แก้บัค": 9,
        "บัค": 8,
        "ฐานข้อมูล": 8,
        "ด็อกเกอร์": 8,
        "ฟรอนต์เอนด์": 7,
        "แบ็กเอนด์": 7,
        "เอพีไอ": 7,
    },

    # Arena refs: Mathematical, Math
    "math": {
        "math": 8,
        "mathematics": 9,
        "algebra": 8,
        "calculus": 8,
        "geometry": 7,
        "trigonometry": 7,
        "probability": 8,
        "statistics": 8,
        "linear algebra": 9,
        "equation": 8,
        "theorem": 8,
        "proof": 8,
        "integral": 8,
        "derivative": 8,
        "matrix": 7,
        "vector": 7,
        "คณิต": 10,
        "คณิตศาสตร์": 10,
        "พีชคณิต": 8,
        "แคลคูลัส": 8,
        "เรขาคณิต": 8,
        "ความน่าจะเป็น": 8,
        "สถิติ": 8,
        "สมการ": 8,
        "ทฤษฎีบท": 8,
        "พิสูจน์": 8,
        "อินทิกรัล": 8,
        "อนุพันธ์": 8,
        "เมทริกซ์": 7,
        "เวกเตอร์": 7,
    },

    # Arena ref: Life, Physical, & Social Science
    "science": {
        "science": 7,
        "scientific": 7,
        "physics": 8,
        "chemistry": 8,
        "biology": 8,
        "biochemistry": 8,
        "astronomy": 7,
        "geology": 7,
        "ecology": 7,
        "neuroscience": 8,
        "psychology": 7,
        "sociology": 7,
        "experiment": 7,
        "hypothesis": 8,
        "quantum": 8,
        "relativity": 8,
        "molecule": 7,
        "cell biology": 8,
        "dna": 8,
        "evolution": 7,
        "climate science": 8,
        "research paper": 8,
        "peer review": 8,
        "black hole": 9,
        "วิทยาศาสตร์": 10,
        "ฟิสิกส์": 9,
        "เคมี": 9,
        "ชีววิทยา": 9,
        "ดาราศาสตร์": 8,
        "ธรณีวิทยา": 8,
        "นิเวศวิทยา": 8,
        "ประสาทวิทยา": 8,
        "จิตวิทยา": 7,
        "สังคมวิทยา": 7,
        "การทดลอง": 8,
        "สมมติฐาน": 8,
        "ควอนตัม": 8,
        "โมเลกุล": 7,
        "ดีเอ็นเอ": 8,
        "วิวัฒนาการ": 7,
        "งานวิจัย": 7,
        "บทความวิจัย": 8,
    },

    # Arena ref: Business, Management, & Financial Ops
    "business_finance": {
        "business": 7,
        "finance": 8,
        "financial": 7,
        "accounting": 8,
        "stock": 8,
        "stocks": 8,
        "nasdaq": 8,
        "nyse": 8,
        "inflation": 7,
        "interest rate": 8,
        "earnings": 8,
        "revenue": 7,
        "profit margin": 8,
        "valuation": 8,
        "dividend": 8,
        "portfolio": 8,
        "technical analysis": 8,
        "fundamental analysis": 8,
        "bitcoin": 8,
        "crypto": 8,
        "startup": 7,
        "management": 7,
        "marketing": 8,
        "advertising": 7,
        "seo": 8,
        "roi": 8,
        "ผลประกอบการ": 9,
        "หุ้น": 10,
        "ตลาดหุ้น": 9,
        "วิเคราะห์หุ้น": 10,
        "ลงทุน": 8,
        "การเงิน": 8,
        "บัญชี": 8,
        "งบการเงิน": 9,
        "เงินเฟ้อ": 8,
        "ดอกเบี้ย": 8,
        "รายได้": 7,
        "กำไร": 7,
        "ปันผล": 8,
        "มูลค่าหุ้น": 8,
        "พอร์ตลงทุน": 8,
        "เทคนิคอล": 8,
        "คริปโต": 8,
        "บิตคอยน์": 8,
        "ธุรกิจ": 8,
        "บริหาร": 7,
        "การตลาด": 8,
        "โฆษณา": 7,
        "เอสอีโอ": 8,
    },

    # Arena ref: Legal & Government
    "legal_government": {
        "law": 8,
        "legal": 9,
        "contract": 8,
        "lawsuit": 8,
        "court": 8,
        "copyright": 8,
        "regulation": 8,
        "compliance": 8,
        "constitution": 8,
        "government": 7,
        "public policy": 8,
        "jurisdiction": 8,
        "statute": 8,
        "legal clause": 8,
        "terms of service": 8,
        "privacy policy": 8,
        "tax law": 8,
        "immigration law": 8,
        "กฎหมาย": 10,
        "สัญญา": 9,
        "คดี": 8,
        "ศาล": 8,
        "ฟ้องร้อง": 8,
        "ลิขสิทธิ์": 8,
        "ข้อบังคับ": 8,
        "กฎระเบียบ": 8,
        "รัฐธรรมนูญ": 8,
        "รัฐบาล": 7,
        "นโยบายรัฐ": 8,
        "เขตอำนาจศาล": 8,
        "ข้อกฎหมาย": 8,
        "ผิดกฎหมาย": 8,
        "ภาษีตามกฎหมาย": 8,
        "กฎหมายคนเข้าเมือง": 8,
    },

    # Arena ref: Medicine & Healthcare
    "medicine_healthcare": {
        "healthcare": 8,
        "medical": 8,
        "medicine": 8,
        "doctor": 7,
        "hospital": 7,
        "patient": 7,
        "symptom": 8,
        "symptoms": 8,
        "diagnosis": 8,
        "treatment": 8,
        "medication": 8,
        "pharmacology": 8,
        "dosage": 8,
        "fever": 8,
        "infection": 8,
        "blood pressure": 8,
        "diabetes": 8,
        "cancer": 8,
        "vaccine": 7,
        "mental health": 8,
        "clinical": 7,
        "การแพทย์": 9,
        "แพทย์": 8,
        "โรงพยาบาล": 8,
        "ผู้ป่วย": 8,
        "อาการป่วย": 8,
        "วินิจฉัย": 8,
        "การรักษา": 8,
        "ยา": 7,
        "ขนาดยา": 8,
        "ไข้": 8,
        "ติดเชื้อ": 8,
        "ความดันโลหิต": 8,
        "เบาหวาน": 8,
        "มะเร็ง": 8,
        "วัคซีน": 7,
        "สุขภาพจิต": 8,
    },

    # Arena refs: Writing/Literature/Language, Creative Writing, Language,
    # English/Non-English/language-specific boards
    "writing_language": {
        "writing": 8,
        "rewrite": 8,
        "proofread": 8,
        "grammar": 8,
        "literature": 8,
        "poem": 8,
        "poetry": 8,
        "novel": 8,
        "fiction": 8,
        "creative writing": 9,
        "translation": 9,
        "translate": 9,
        "translator": 8,
        "synonym": 7,
        "pronunciation": 7,
        "roleplay": 7,
        "article": 8,
        "บทความ": 8,
        "เขียนบทความ": 8,
        "เขียนนิยาย": 9,
        "นิยาย": 9,
        "แต่งเรื่อง": 8,
        "เรื่องสั้น": 8,
        "วรรณกรรม": 8,
        "บทกวี": 8,
        "กลอน": 8,
        "รีไรต์": 8,
        "ตรวจแกรมม่า": 8,
        "แก้ภาษา": 8,
        "แปล": 10,
        "แปลว่า": 9,
        "แปลเป็น": 9,
        "คำพ้องความหมาย": 7,
        "การออกเสียง": 7,
        "สวมบท": 7,
        "โรลเพลย์": 7,
    },

    # Arena ref: Entertainment, Sports, & Media
    "entertainment_media": {
        "movie": 8,
        "film": 8,
        "tv show": 7,
        "anime": 9,
        "manga": 8,
        "video game": 8,
        "gaming": 8,
        "music": 7,
        "song": 7,
        "album": 7,
        "celebrity": 7,
        "sports": 8,
        "football": 8,
        "soccer": 8,
        "basketball": 8,
        "tennis": 7,
        "esports": 8,
        "pop culture": 8,
        "หนัง": 9,
        "ภาพยนตร์": 9,
        "ซีรีส์": 8,
        "อนิเมะ": 9,
        "มังงะ": 8,
        "วิดีโอเกม": 8,
        "เกมมิ่ง": 8,
        "เพลง": 7,
        "อัลบั้ม": 7,
        "ดารา": 7,
        "กีฬา": 8,
        "ฟุตบอล": 8,
        "บาสเกตบอล": 8,
        "เทนนิส": 7,
        "อีสปอร์ต": 8,
        "ป๊อปคัลเจอร์": 8,
    },
}


ACTION_THRESHOLD = 0.45
TECHNICAL_THRESHOLD = 0.38
ACTION_MARGIN = 0.12
SUBJECT_THRESHOLD = 0.30

# Extensible action registry. Future categories such as TOOL_USE_ACTION,
# RESEARCH_ACTION, MULTIMODAL_ACTION, and AGENTIC_ACTION can be added here
# without changing the routing pipeline.
ACTION_CATEGORIES: dict[str, ActionCategory] = {
    "technical": ActionCategory(
        name="technical",
        priority=100,
        route="software_it",
        keywords={
            "แก้": 7,
            "แก้ไข": 8,
            "เปลี่ยน": 7,
            "ปรับ": 5,
            "fix": 9,
            "debug": 9,
            "ดีบัก": 9,
            "รัน": 8,
            "run": 7,
            "deploy": 8,
            "config": 9,
            "configure": 8,
            "configuration": 8,
            "install": 8,
            "ติดตั้ง": 8,
            "port": 9,
            "พอร์ต": 9,
            "server": 9,
            "เซิร์ฟเวอร์": 9,
            "build": 8,
            "code": 8,
            "coding": 8,
            "เขียนโค้ด": 10,
            "implement": 8,
            "refactor": 8,
            "เทส": 8,
            "test": 7,
            "error": 8,
            "bug": 8,
            "crash": 8,
            "yaml": 8,
            "json": 7,
            "dockerfile": 9,
            "docker": 8,
            "script": 10,
            "สคริปต์": 10,
            "function": 8,
            "class": 7,
            "api": 9,
            "database": 8,
            "parser": 8,
            "plugin": 8,
            "model ใน config": 10,
        },
        negative_patterns=(
            "commit และ push ได้เลย",
            "commit and push",
            "push ได้เลย",
            "commit ได้เลย",
            "โอเค",
            "โอเคครับ",
            "ขอบคุณ",
            "thanks",
            "thank you",
        ),
    ),
    "analytical": ActionCategory(
        name="analytical",
        priority=70,
        keywords={
            "วิเคราะห์": 9,
            "คำนวณ": 9,
            "calculate": 9,
            "solve": 8,
            "proof": 8,
            "พิสูจน์": 8,
            "อธิบาย": 7,
            "explain": 7,
            "forecast": 7,
            "ทำนาย": 7,
            "roi": 8,
        },
    ),
    "creative": ActionCategory(
        name="creative",
        priority=60,
        keywords={
            "เขียน": 6,
            "แต่ง": 8,
            "สร้าง creative content": 9,
            "creative content": 8,
            "แปล": 8,
            "translate": 8,
            "draft": 8,
            "compose": 8,
            "rewrite": 7,
            "รีไรต์": 7,
            "summarize": 6,
            "สรุป": 6,
            "บทความ": 5,
            "report": 6,
        },
    ),
}

CREATIVE_SUBJECT_ROUTES = {
    "legal_government": "legal_government",
    "business_finance": "business_finance",
    "writing_language": "writing_language",
    "entertainment_media": "writing_language",
}

ANALYTICAL_SUBJECT_ROUTES = {
    "math": "math",
    "science": "science",
    "legal_government": "legal_government",
    "business_finance": "business_finance",
    "medicine_healthcare": "medicine_healthcare",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text)).lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _matches(keyword: str, text: str) -> bool:
    """Match keywords conservatively, with phrase/partial support.

    English/ASCII keywords use token boundaries so short words do not match
    inside unrelated words. Thai and other non-ASCII keywords use substring
    matching because whitespace tokenization is unreliable.
    """

    keyword_l = _normalize(keyword)

    if keyword_l.isascii():
        pattern = (
            r"(?<![a-z0-9_])"
            + re.escape(keyword_l)
            + r"(?![a-z0-9_])"
        )
        return re.search(pattern, text) is not None

    return keyword_l in text


def _score_subjects(weighted_messages: list[str]) -> tuple[dict[str, float], str, float]:
    scores = {topic: 0.0 for topic in TOPICS}
    total_weight = 0.0

    for i, msg in enumerate(weighted_messages):
        text = _normalize(msg)
        recency_weight = 0.5 + ((i + 1) ** 1.5)
        total_weight += recency_weight

        for topic, keywords in TOPICS.items():
            for keyword, weight in keywords.items():
                if _matches(keyword, text):
                    scores[topic] += weight * recency_weight

    if total_weight > 0:
        for topic in scores:
            scores[topic] /= total_weight

    best_topic = max(scores, key=scores.get)
    return scores, best_topic, scores[best_topic]


def _score_actions(weighted_messages: list[str]) -> tuple[dict[str, float], str, float, dict[str, list[str]]]:
    scores = {name: 0.0 for name in ACTION_CATEGORIES}
    matched: dict[str, list[str]] = {name: [] for name in ACTION_CATEGORIES}
    total_weight = 0.0

    for i, msg in enumerate(weighted_messages):
        text = _normalize(msg)
        recency_weight = 0.5 + ((i + 1) ** 1.5)
        total_weight += recency_weight

        for name, category in ACTION_CATEGORIES.items():
            if any(_matches(pattern, text) for pattern in category.negative_patterns):
                scores[name] -= 12 * recency_weight
                matched[name].append("negative_pattern")
                continue

            for keyword, weight in category.keywords.items():
                if _matches(keyword, text):
                    scores[name] += weight * recency_weight
                    matched[name].append(keyword)

    if total_weight > 0:
        for name in scores:
            scores[name] = max(scores[name] / total_weight, 0.0)

    best_action = max(scores, key=scores.get)
    return scores, best_action, scores[best_action], matched


def _confidence(score: float) -> float:
    # Cap below 1.0: keyword/heuristic matching should not pretend certainty.
    return min(max(score / 8.0, 0.0), 0.95)


def _close_competition(action_scores: dict[str, float], best_action: str, best_score: float) -> bool:
    if best_score <= 0:
        return False
    competitors = [
        score for action, score in action_scores.items()
        if action != best_action and score > 0
    ]
    if not competitors:
        return False
    return best_score - max(competitors) < ACTION_MARGIN


def _route_from_action(action: str, subject: str, subject_score: float, combined_text: str = "") -> tuple[str, str]:
    if action == "technical":
        return "software_it", "technical_override"

    if action == "analytical":
        if subject in ANALYTICAL_SUBJECT_ROUTES and subject_score >= SUBJECT_THRESHOLD:
            return ANALYTICAL_SUBJECT_ROUTES[subject], "analytical_subject_route"
        return "none", "analytical_unclear_subject"

    if action == "creative":
        # Writing an article remains a writing/language task even when the
        # article topic is finance/science/etc. Report/contract drafting are
        # domain-shaped deliverables, so they keep their domain route.
        if _matches("บทความ", combined_text) or _matches("article", combined_text):
            return "writing_language", "creative_article_writing"
        if _matches("report", combined_text) or _matches("รายงาน", combined_text):
            if subject in ("business_finance", "legal_government", "science", "medicine_healthcare"):
                return subject, "creative_domain_report"
        if subject in CREATIVE_SUBJECT_ROUTES and subject_score >= SUBJECT_THRESHOLD:
            return CREATIVE_SUBJECT_ROUTES[subject], "creative_subject_route"
        return "writing_language", "creative_default_writing"

    return "none", "no_action_route"


def classify(messages: list[str]) -> ClassificationResult:
    if not messages:
        return ClassificationResult("none", 0.0, {}, final_route_reason="empty")

    weighted_messages = list(messages[-5:])
    subject_scores, subject, subject_score = _score_subjects(weighted_messages)
    action_scores, action, action_score, action_matches = _score_actions(weighted_messages)

    debug = {
        "action_scores": {k: round(v, 3) for k, v in action_scores.items() if v > 0},
        "action_matches": {k: v for k, v in action_matches.items() if v},
        "subject_score": round(subject_score, 3),
        "subject_detected": subject if subject_score > 0 else "none",
    }

    # Priority 1: technical action overrides every subject.
    if action == "technical" and action_score >= TECHNICAL_THRESHOLD:
        return ClassificationResult(
            "software_it",
            _confidence(action_score),
            subject_scores,
            action_detected=action,
            action_score=action_score,
            subject_detected=subject if subject_score > 0 else "none",
            final_route_reason="technical_override",
            debug=debug,
        )

    # Priority 2-3: analytical/creative actions route through subject table.
    if action_score >= ACTION_THRESHOLD:
        if _close_competition(action_scores, action, action_score):
            return ClassificationResult(
                "none",
                0.0,
                subject_scores,
                action_detected=action,
                action_score=action_score,
                subject_detected=subject if subject_score > 0 else "none",
                final_route_reason="ambiguous_action_margin",
                debug=debug,
            )

        routed_topic, reason = _route_from_action(
            action,
            subject,
            subject_score,
            _normalize("\n".join(weighted_messages)),
        )
        return ClassificationResult(
            routed_topic,
            _confidence(action_score if routed_topic != "none" else 0.0),
            subject_scores,
            action_detected=action,
            action_score=action_score,
            subject_detected=subject if subject_score > 0 else "none",
            final_route_reason=reason,
            debug=debug,
        )

    # Priority 4: action unclear, fall back to subject-based routing.
    if subject_score > 0:
        return ClassificationResult(
            subject,
            _confidence(subject_score),
            subject_scores,
            action_detected="none",
            action_score=action_score,
            subject_detected=subject,
            final_route_reason="subject_fallback",
            debug=debug,
        )

    # Priority 5: none is safe.
    return ClassificationResult(
        "none",
        0.0,
        subject_scores,
        action_detected="none",
        action_score=action_score,
        subject_detected="none",
        final_route_reason="none_safe",
        debug=debug,
    )
