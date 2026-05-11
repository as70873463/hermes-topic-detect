from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    topic: str
    confidence: float
    scores: dict[str, float]


# Arena.ai-aligned primary topics.
#
# Design rule for keyword routing:
# - Keep only common, high-signal EN/TH keywords for each domain.
# - Avoid broad words that are common across domains (app, review, policy,
#   market, theory, terms, story, health, language, media, etc.).
# - No "general" topic: unclear prompts return "none" and Hermes keeps the
#   main/default model.
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


def _matches(keyword: str, text: str) -> bool:
    """Match keywords conservatively.

    English/ASCII keywords use token boundaries so short words do not match
    inside unrelated words. Thai and other non-ASCII keywords use substring
    matching because whitespace tokenization is unreliable.
    """

    keyword_l = keyword.lower()

    if keyword_l.isascii():
        pattern = (
            r"(?<![a-z0-9_])"
            + re.escape(keyword_l)
            + r"(?![a-z0-9_])"
        )
        return re.search(pattern, text) is not None

    return keyword_l in text


def classify(messages: list[str]) -> ClassificationResult:
    if not messages:
        return ClassificationResult("none", 0.0, {})

    weighted_messages = list(messages[-5:])
    scores = {topic: 0.0 for topic in TOPICS}
    total_weight = 0.0

    for i, msg in enumerate(weighted_messages):
        text = str(msg).lower()
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
    best_score = scores[best_topic]

    if best_score <= 0:
        return ClassificationResult("none", 0.0, scores)

    # Cap confidence below 1.0: keyword matching should not pretend certainty.
    confidence = min(best_score / 8.0, 0.95)

    return ClassificationResult(best_topic, confidence, scores)
