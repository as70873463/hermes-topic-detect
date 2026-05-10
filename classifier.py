from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClassificationResult:
    topic: str
    confidence: float
    scores: dict[str, float]


TOPICS: dict[str, dict[str, int]] = {
    "programming": {
        "python": 9, "javascript": 8, "typescript": 8, "php": 6,
        "java": 5, "c++": 5, "c#": 5, "go": 5, "rust": 5,
        "code": 6, "coding": 6, "script": 6, "program": 5,
        "function": 5, "class": 4, "method": 4, "variable": 4,
        "loop": 5, "for loop": 6, "while": 5, "array": 4,
        "dict": 4, "object": 4, "json": 5, "yaml": 5,
        "api": 5, "http": 4, "request": 4, "response": 4,
        "debug": 7, "bug": 6, "error": 5, "exception": 5,
        "traceback": 6, "stacktrace": 6, "syntax": 4,
        "read file": 7, "write file": 7, "file path": 5,
        "terminal": 5, "bash": 5, "shell": 5, "linux": 5,
        "docker": 6, "git": 5, "github": 5, "deploy": 4,
        "database": 4, "sql": 5, "regex": 5, "server": 3,
        "โค้ด": 9, "เขียนโค้ด": 10, "เขียนโปรแกรม": 9,
        "สคริปต์": 7, "ฟังก์ชัน": 6, "ลูป": 6, "วนลูป": 8,
        "อ่านไฟล์": 8, "เขียนไฟล์": 8, "ไฟล์": 3,
        "แก้บัค": 8, "บัค": 6, "เออเร่อ": 6, "ผิดตรงไหน": 5,
        "รันไม่ได้": 7, "เทอร์มินัล": 5, "คำสั่ง linux": 6,
    },

    "finance": {
        "stock": 7, "stocks": 7, "share": 5, "shares": 5,
        "market": 4, "nasdaq": 7, "nyse": 6, "s&p": 6,
        "sp500": 6, "dow": 5, "fed": 6, "rate cut": 6,
        "interest rate": 6, "inflation": 5, "cpi": 5,
        "earnings": 6, "revenue": 4, "profit": 4, "loss": 4,
        "valuation": 6, "pe ratio": 6, "eps": 5,
        "dividend": 6, "yield": 5, "etf": 6, "portfolio": 6,
        "buy": 3, "sell": 3, "hold": 3, "target price": 7,
        "support": 4, "resistance": 4, "technical analysis": 6,
        "bitcoin": 8, "btc": 8, "ethereum": 7, "eth": 7,
        "crypto": 7, "gold": 6, "oil": 5,
        "nvda": 8, "nvidia": 8, "tsla": 8, "tesla": 8,
        "aapl": 7, "apple stock": 7, "msft": 7, "meta": 7,
        "googl": 7, "goog": 7, "snow": 7, "crwv": 7,
        "rblx": 7, "roblox": 7,
        "หุ้น": 9, "วิเคราะห์หุ้น": 10, "ตลาดหุ้น": 8,
        "หุ้นไทย": 8, "ลงทุน": 7, "พอร์ต": 6, "พอร์ตหุ้น": 7,
        "กำไร": 5, "ขาดทุน": 5, "ราคาเป้าหมาย": 8,
        "งบ": 5, "งบการเงิน": 7, "รายได้": 4,
        "ปันผล": 7, "ดอกเบี้ย": 6, "เงินเฟ้อ": 5,
        "แนวรับ": 7, "แนวต้าน": 7, "กราฟหุ้น": 7,
        "เทคนิคอล": 6, "พื้นฐาน": 4,
        "น่าซื้อ": 8, "ซื้อดีไหม": 8, "น่าซื้อไหม": 9,
        "ซื้อเพิ่ม": 8, "น่าซื้อเพิ่ม": 9, "ขายดีไหม": 8,
        "ควรขาย": 7, "ควรซื้อ": 7, "ถือดีไหม": 8,
        "ถือไว้": 6, "ถือยาว": 7, "ถัว": 7,
        "แบ่งไม้": 6, "เข้าซื้อ": 7, "ราคาเข้า": 6,
        "คริปโต": 7, "บิตคอยน์": 8, "ทอง": 6, "ทองคำ": 7,
    },

    "translation": {
        "translate": 9, "translation": 8, "translator": 6,
        "english": 4, "thai": 4, "japanese": 4, "chinese": 4,
        "korean": 4, "meaning": 3, "pronounce": 4,
        "แปล": 10, "แปลว่า": 9, "แปลเป็น": 9,
        "แปลไทย": 9, "แปลอังกฤษ": 9, "ภาษาอังกฤษ": 6,
        "ภาษาไทย": 6, "ภาษาญี่ปุ่น": 6, "ภาษาจีน": 6,
        "เกาหลี": 4, "ญี่ปุ่น": 4, "อังกฤษ": 4,
        "คำนี้หมายถึง": 6, "อ่านว่า": 5,
    },

    "health": {
        "health": 5, "medical": 6, "doctor": 6, "hospital": 5,
        "symptom": 6, "symptoms": 6, "medicine": 5, "drug": 4,
        "pain": 5, "headache": 7, "fever": 7, "cough": 6,
        "infection": 5, "blood pressure": 6, "diabetes": 6,
        "vitamin": 4, "sleep": 4, "diet": 4,
        "สุขภาพ": 7, "หมอ": 6, "แพทย์": 6, "โรงพยาบาล": 6,
        "อาการ": 7, "ยา": 6, "ปวดหัว": 8, "ไข้": 8,
        "ไอ": 6, "เจ็บคอ": 7, "ปวดท้อง": 7, "ความดัน": 6,
        "เบาหวาน": 6, "นอนไม่หลับ": 6, "วิตามิน": 5,
    },

    "seo": {
        "seo": 10, "serp": 8, "backlink": 8, "keyword": 6,
        "keywords": 6, "ranking": 6, "search ranking": 7,
        "meta title": 6, "meta description": 6, "organic traffic": 7,
        "google search": 5, "คีย์เวิร์ด": 7, "อันดับ google": 8,
        "ติดหน้าแรก": 8, "บทความ seo": 8, "แบ็คลิงก์": 8,
    },

    "marketing": {
        "marketing": 8, "campaign": 7, "branding": 7, "brand": 5,
        "conversion": 6, "ads": 6, "advertising": 6,
        "facebook ads": 7, "google ads": 7, "sales funnel": 7,
        "copywriting": 6, "landing page": 6,
        "การตลาด": 8, "แคมเปญ": 7, "แบรนด์": 7,
        "โฆษณา": 7, "ยิงแอด": 8, "คอนเวอร์ชัน": 6,
        "ยอดขาย": 6, "ลูกค้า": 5, "โปรโมท": 6,
    },

    "science": {
        "science": 6, "physics": 7, "chemistry": 7, "biology": 7,
        "math": 5, "mathematics": 5, "experiment": 6,
        "research": 5, "theory": 4, "quantum": 6, "energy": 4,
        "force": 4, "gravity": 5, "atom": 5, "molecule": 5,
        "วิทยาศาสตร์": 8, "ฟิสิกส์": 8, "เคมี": 8,
        "ชีวะ": 7, "ชีววิทยา": 8, "คณิต": 6,
        "ทดลอง": 6, "ทฤษฎี": 5, "ควอนตัม": 6,
        "แรง": 4, "พลังงาน": 4,
    },

    "technology": {
        "technology": 6, "tech": 5, "ai": 6, "llm": 8,
        "model": 4, "gpu": 6, "cpu": 5, "hardware": 6,
        "software": 5, "server": 5, "cloud": 5, "vps": 6,
        "network": 5, "wifi": 4, "router": 4, "api key": 5,
        "openrouter": 8, "openai": 8, "chatgpt": 8,
        "claude": 7, "gemini": 7, "hermes": 9, "openclaw": 8,
        "docker": 4, "wsl": 6, "tailscale": 7,
        "เทคโนโลยี": 7, "เอไอ": 7, "โมเดล": 6,
        "การ์ดจอ": 6, "เซิร์ฟเวอร์": 6, "คลาวด์": 5,
        "เน็ตเวิร์ค": 5, "คีย์ api": 6,
    },

    "legal": {
        "law": 8, "legal": 8, "contract": 8, "court": 7,
        "lawsuit": 7, "rights": 5, "copyright": 6, "terms": 4,
        "policy": 4, "tax law": 6, "constitution": 7,
        "กฎหมาย": 10, "สัญญา": 8, "ศาล": 7, "ฟ้อง": 7,
        "คดี": 7, "สิทธิ": 6, "ลิขสิทธิ์": 7,
        "รัฐธรรมนูญ": 8, "ภาษี": 5, "ข้อบังคับ": 6,
        "ผิดกฎหมาย": 8,
    },

    "academia": {
        "academic": 7, "paper": 7, "thesis": 8, "citation": 7,
        "reference": 5, "journal": 7, "abstract": 6,
        "methodology": 6, "literature review": 8, "doi": 6,
        "university": 5, "essay": 5,
        "วิชาการ": 8, "งานวิจัย": 8, "วิจัย": 7,
        "论文": 4, "ธีสิส": 8, "อ้างอิง": 7,
        "บรรณานุกรม": 7, "บทคัดย่อ": 7, "วารสาร": 7,
        "มหาวิทยาลัย": 5, "เรียงความ": 5,
    },

    "roleplay": {
        "roleplay": 9, "rp": 6, "pretend": 7, "character": 6,
        "fiction": 6, "novel": 6, "story": 5, "scene": 4,
        "dialogue": 5, "persona": 6, "act as": 7,
        "สวมบท": 9, "โรลเพลย์": 9, "นิยาย": 8,
        "ตัวละคร": 7, "บทสนทนา": 6, "ฉาก": 5,
        "แต่งเรื่อง": 7, "เขียนนิยาย": 8,
    },

    "trivia": {
        "what is": 3, "why": 3, "how many": 4, "fun fact": 7,
        "quiz": 7, "trivia": 8, "history of": 4,
        "คืออะไร": 5, "ทำไม": 4, "มีกี่": 5,
        "ใครคือ": 5, "ประวัติ": 5, "เรื่องน่ารู้": 7,
        "คำถาม": 3,
    },
}


def classify(messages: list[str]) -> ClassificationResult:
    if not messages:
        return ClassificationResult("none", 0.0, {})

    weighted_messages = list(messages[-5:])
    scores = {topic: 0.0 for topic in TOPICS}
    total_weight = 0.0

    for i, msg in enumerate(weighted_messages):
        text = msg.lower()
        recency_weight = 0.5 + ((i + 1) ** 1.5)
        total_weight += recency_weight

        for topic, keywords in TOPICS.items():
            for keyword, weight in keywords.items():
                if keyword.lower() in text:
                    scores[topic] += weight * recency_weight

    if total_weight > 0:
        for topic in scores:
            scores[topic] /= total_weight

    best_topic = max(scores, key=scores.get)
    best_score = scores[best_topic]

    if best_score <= 0:
        return ClassificationResult("none", 0.0, scores)

    confidence = min(best_score / 8.0, 1.0)

    return ClassificationResult(best_topic, confidence, scores)
