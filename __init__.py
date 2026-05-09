"""
__init__.py — hermes-topic-detect plugin

Detects conversation topic from keyword signals and phrase boosts,
then overrides the active LLM model via pre_llm_call hook.

Log format:
    ✓ TOPIC: PROGRAMMING | MODEL: ring-2.6-1t | CONFIDENCE: 0.95
"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("topic_detect")

# ─── Config ──────────────────────────────────────────────────────

WINDOW = 3
MIN_SCORE = 1.5
MIN_CONFIDENCE = 0.65
CONFIDENCE_CAP = 0.95
HIGH_CONF_THRESHOLD = 0.90
DEFAULT_MODEL = "openrouter/owl-alpha"

TOPIC_MODELS: dict[str, str] = {
    "programming":  "inclusionai/ring-2.6-1t:free",
    "finance":      "inclusionai/ring-2.6-1t:free",
    "science":      "inclusionai/ring-2.6-1t:free",
    "academia":     "inclusionai/ring-2.6-1t:free",
    "health":       "openrouter/owl-alpha",
    "legal":        "openrouter/owl-alpha",
    "seo":          "openrouter/owl-alpha",
    "translation":  "openrouter/owl-alpha",
    "technology":   "openrouter/owl-alpha",
    "marketing":    "openrouter/cobuddy:free",
    "roleplay":     "openrouter/cobuddy:free",
    "trivia":       "openrouter/cobuddy:free",
}

# ─── Phrase Boosts ───────────────────────────────────────────────

PHRASE_BOOSTS: dict[str, list[tuple[str, float]]] = {
    "programming": [
        ("stack trace", 8.0), ("null pointer", 7.0), ("type error", 7.0),
        ("infinite loop", 7.0), ("segmentation fault", 7.0), ("memory leak", 7.0),
        ("race condition", 7.0), ("deadlock", 7.0), ("callback hell", 6.0),
        ("unit test", 6.0), ("integration test", 6.0), ("rest api", 6.0),
        ("graphql", 6.0), ("microservices", 6.0), ("docker", 6.0),
        ("kubernetes", 6.0), ("ci/cd", 6.0), ("git merge conflict", 6.0),
        ("pull request", 5.0), ("code review", 5.0), ("refactor", 5.0),
        ("technical debt", 5.0), ("big o notation", 5.0), ("data structure", 5.0),
        ("hash map", 5.0), ("binary tree", 5.0),
    ],
    "finance": [
        ("earnings call", 8.0), ("price target", 7.0), ("market cap", 7.0),
        ("stop loss", 6.0), ("take profit", 6.0), ("dividend yield", 6.0),
        ("price to earnings", 6.0), ("free cash flow", 6.0), ("compound interest", 5.0),
        ("asset allocation", 5.0), ("bull market", 5.0), ("bear market", 5.0),
    ],
    "health": [
        ("side effect", 7.0), ("chronic disease", 7.0), ("mental health", 7.0),
        ("cardiovascular", 6.0), ("immune system", 6.0), ("blood pressure", 6.0),
        ("body mass index", 5.0), ("calorie deficit", 5.0), ("sleep disorder", 5.0),
    ],
    "legal": [
        ("breach of contract", 8.0), ("intellectual property", 7.0),
        ("terms of service", 6.0), ("liability clause", 6.0),
        ("class action", 7.0), ("due diligence", 6.0),
    ],
    "technology": [
        ("machine learning", 8.0), ("neural network", 8.0),
        ("large language model", 8.0), ("artificial intelligence", 7.0),
        ("quantum computing", 7.0), ("edge computing", 6.0),
        ("internet of things", 6.0), ("blockchain", 5.0),
    ],
    "seo": [
        ("search engine optimization", 8.0), ("backlink profile", 7.0),
        ("organic traffic", 7.0), ("page authority", 6.0), ("bounce rate", 6.0),
        ("conversion rate", 6.0), ("core web vitals", 5.0),
    ],
    "marketing": [
        ("brand awareness", 7.0), ("customer acquisition", 7.0),
        ("conversion funnel", 7.0), ("return on ad spend", 7.0),
        ("a/b testing", 6.0), ("landing page", 6.0), ("email campaign", 6.0),
        ("influencer marketing", 5.0), ("growth hacking", 5.0),
        ("customer lifetime value", 6.0), ("churn rate", 6.0),
    ],
    "science": [
        ("quantum mechanics", 8.0), ("general relativity", 8.0),
        ("thermodynamics", 7.0), ("molecular biology", 7.0),
        ("genome sequencing", 7.0), ("chemical reaction", 6.0),
        ("string theory", 6.0), ("dark matter", 6.0), ("neuroscience", 6.0),
    ],
    "academia": [
        ("literature review", 7.0), ("research methodology", 7.0),
        ("peer reviewed", 7.0), ("citation format", 6.0),
        ("thesis statement", 6.0), ("doctoral dissertation", 7.0),
    ],
    "translation": [
        ("translation memory", 7.0), ("localization", 7.0),
        ("neural machine translation", 8.0), ("idiomatic expression", 6.0),
    ],
    "roleplay": [
        ("character sheet", 7.0), ("roleplay", 7.0), ("dungeon master", 7.0),
        ("campaign setting", 7.0), ("non-player character", 6.0),
        ("hit points", 6.0), ("skill check", 6.0), ("critical hit", 6.0),
        ("in-character", 6.0), ("out-of-character", 6.0),
        ("world building", 5.0), ("immersive storytelling", 5.0),
    ],
    "trivia": [
        ("trivia question", 7.0), ("fun fact", 7.0), ("quiz", 7.0),
        ("did you know", 6.0), ("general knowledge", 6.0),
        ("brain teaser", 6.0), ("riddle", 6.0), ("pub quiz", 5.0),
    ],
}

# ─── Keyword Signals ─────────────────────────────────────────────
# Non-Latin scripts: plain strings, NO \b word boundary

TOPIC_SIGNALS: dict[str, list[tuple[str, float]]] = {
    "programming": [
        (r"(?i)\bdef\s+\w+", 3.0), (r"(?i)\bclass\s+\w+", 3.0),
        (r"(?i)\bfunction\b", 2.5), (r"(?i)\bvariable\b", 2.0),
        (r"(?i)\bloop\b", 2.0), (r"(?i)\bfor\s+loop\b", 2.5),
        (r"(?i)\bwhile\s+loop\b", 2.5), (r"(?i)\bif\s+else\b", 2.0),
        (r"(?i)\bimport\b", 2.0), (r"(?i)\bmodule\b", 2.0),
        (r"(?i)\bpackage\b", 2.0), (r"(?i)\blibrary\b", 2.5),
        (r"(?i)\bframework\b", 2.5), (r"(?i)\bapi\b", 2.5),
        (r"(?i)\bjson\b", 2.0), (r"(?i)\bxml\b", 2.0),
        (r"(?i)\bregex\b", 2.5), (r"(?i)\brecursion\b", 3.0),
        (r"(?i)\balgorithm\b", 3.0), (r"(?i)\bdebug\b", 2.5),
        (r"(?i)\bcompiler\b", 3.0), (r"(?i)\bsyntax\b", 2.5),
        (r"(?i)\bruntime\b", 2.5), (r"(?i)\bexception\b", 2.5),
        (r"(?i)\btry\s+except\b", 3.0), (r"(?i)\breturn\b", 1.5),
        (r"(?i)\bprint\b", 1.0), (r"(?i)\bpython\b", 3.0),
        (r"(?i)\bjavascript\b", 3.0), (r"(?i)\btypescript\b", 3.0),
        (r"(?i)\bjava\b", 3.0), (r"(?i)\bc\+\+", 3.0),
        (r"(?i)\bc#\b", 3.0), (r"(?i)\bgo\b", 2.5),
        (r"(?i)\brust\b", 2.5), (r"(?i)\bgit\b", 2.0),
        (r"(?i)\bgithub\b", 2.0), (r"(?i)\bterminal\b", 2.0),
        (r"(?i)\bshell\b", 2.0), (r"(?i)\bbash\b", 2.5),
        (r"(?i)\bsql\b", 2.5), (r"(?i)\bdatabase\b", 2.5),
        (r"(?i)\bserver\b", 2.0), (r"(?i)\bclient\b", 2.0),
        (r"(?i)\bfrontend\b", 2.5), (r"(?i)\bbackend\b", 2.5),
        (r"(?i)\bfullstack\b", 2.5), (r"(?i)\breact\b", 3.0),
        (r"(?i)\bnode\b", 3.0), (r"(?i)\bdjango\b", 3.0),
        (r"(?i)\bflask\b", 3.0), (r"(?i)\bfastapi\b", 3.0),
        (r"(?i)\bhtml\b", 2.5), (r"(?i)\bcss\b", 2.5),
        # Thai
        ("เขียนโปรแกรม", 3.0), ("โค้ด", 3.0), ("โปรแกรม", 3.0),
        ("Python", 3.0), ("เว็บไซต์", 2.5), ("เว็บ", 2.5),
        ("แอป", 2.5), ("แอปพลิเคชัน", 2.5), ("ข้อผิดพลาด", 2.5),
        ("bug", 2.5), ("error", 2.5), ("แก้โค้ด", 2.5),
        ("deploy", 2.5), ("เซิร์ฟเวอร์", 2.5),
    ],
    "finance": [
        (r"(?i)\bstock\b", 3.0), (r"(?i)\bequity\b", 3.0),
        (r"(?i)\bshare\b", 2.0), (r"(?i)\binvest\b", 2.5),
        (r"(?i)\binvestment\b", 2.5), (r"(?i)\bportfolio\b", 3.0),
        (r"(?i)\bdividend\b", 3.0), (r"(?i)\brevenue\b", 2.5),
        (r"(?i)\bprofit\b", 2.5), (r"(?i)\bloss\b", 2.0),
        (r"(?i)\bearnings\b", 3.0), (r"(?i)\bmarket\b", 2.5),
        (r"(?i)\btrading\b", 2.5), (r"(?i)\bprice\b", 2.0),
        (r"(?i)\bIPO\b", 3.0), (r"(?i)\bETF\b", 3.0),
        (r"(?i)\bS&P\s*500\b", 3.0), (r"(?i)\bNASDAQ\b", 3.0),
        (r"(?i)\bfinancial\b", 2.5), (r"(?i)\bbudget\b", 2.5),
        (r"(?i)\btax\b", 2.0), (r"(?i)\binflation\b", 2.5),
        (r"(?i)\binterest\s*rate\b", 2.5), (r"(?i)\bGDP\b", 3.0),
        (r"(?i)\bcrypto\b", 2.5), (r"(?i)\bbitcoin\b", 2.5),
        (r"(?i)\bfinance\b", 3.0),
        # Thai
        ("หุ้น", 3.0), ("ลงทุน", 3.0), ("กำไร", 2.5),
        ("ขาดทุน", 2.5), ("เงินปันผล", 3.0), ("ตลาดหุ้น", 3.0),
        ("พอร์ต", 2.5), ("เงิน", 1.5), ("ราคา", 2.0),
        ("ซื้อ", 1.5), ("ขาย", 1.5), ("เศรษฐกิจ", 2.5),
        ("บิตคอยน์", 2.5), ("คริปโต", 2.5),
        ("NEE", 3.0), ("EOSE", 3.0), ("SOUN", 3.0), ("GRAB", 3.0),
    ],
    "science": [
        (r"(?i)\bphysics\b", 3.0), (r"(?i)\bchemistry\b", 3.0),
        (r"(?i)\bbiology\b", 3.0), (r"(?i)\bexperiment\b", 3.0),
        (r"(?i)\bhypothesis\b", 3.0), (r"(?i)\btheory\b", 2.5),
        (r"(?i)\blaboratory\b", 3.0), (r"(?i)\bmolecule\b", 3.0),
        (r"(?i)\batom\b", 3.0), (r"(?i)\bquantum\b", 3.0),
        (r"(?i)\brelativity\b", 3.0), (r"(?i)\bevolution\b", 3.0),
        (r"(?i)\bgenetics\b", 3.0), (r"(?i)\bDNA\b", 3.0),
        (r"(?i)\bcell\b", 2.0), (r"(?i)\bchemical\b", 2.5),
        (r"(?i)\bthermodynamics\b", 3.0), (r"(?i)\bentropy\b", 3.0),
        (r"(?i)\bvelocity\b", 2.5), (r"(?i)\bforce\b", 2.5),
        (r"(?i)\benergy\b", 2.5), (r"(?i)\bcosmos\b", 3.0),
        (r"(?i)\bgalaxy\b", 3.0), (r"(?i)\bblack\s*hole\b", 3.0),
        (r"(?i)\bclimate\b", 2.5),
        # Thai
        ("ฟิสิกส์", 3.0), ("เคมี", 3.0), ("ชีววิทยา", 3.0),
        ("วิทยาศาสตร์", 3.0), ("ทดลอง", 2.5), ("ทฤษฎี", 2.5),
        ("วิจัย", 2.5), ("จักรวาล", 3.0), ("ดาว", 2.5),
        ("แรงโน้มถ่วง", 2.5), ("ธรรมชาติ", 2.0),
    ],
    "academia": [
        (r"(?i)\bthesis\b", 3.0), (r"(?i)\bdissertation\b", 3.0),
        (r"(?i)\bcitation\b", 2.5), (r"(?i)\breference\b", 2.5),
        (r"(?i)\bliterature\s*review\b", 3.0), (r"(?i)\bmethodology\b", 3.0),
        (r"(?i)\bpeer\s*review\b", 3.0), (r"(?i)\bjournal\b", 2.5),
        (r"(?i)\bpaper\b", 2.5), (r"(?i)\bconference\b", 2.5),
        (r"(?i)\bacademic\b", 3.0), (r"(?i)\buniversity\b", 2.5),
        (r"(?i)\bprofessor\b", 2.5), (r"(?i)\blecture\b", 2.5),
        (r"(?i)\bPhD\b", 3.0), (r"(?i)\btenure\b", 3.0),
        (r"(?i)\bpublish\b", 2.5), (r"(?i)\bplagiarism\b", 3.0),
        (r"(?i)\babstract\b", 2.5), (r"(?i)\bstatistical\b", 2.5),
        # Thai
        ("วิทยานิพนธ์", 3.0), ("อ้างอิง", 2.5), ("งานวิจัย", 2.5),
        ("วิธีวิจัย", 3.0), ("มหาวิทยาลัย", 2.5), ("สอบ", 2.0),
        ("เรียน", 2.0), ("อาจารย์", 2.0), ("โครงงาน", 2.5),
        ("บทความ", 2.5),
    ],
    "health": [
        (r"(?i)\bdoctor\b", 2.5), (r"(?i)\bmedical\b", 3.0),
        (r"(?i)\bhospital\b", 3.0), (r"(?i)\bdisease\b", 3.0),
        (r"(?i)\bsymptom\b", 3.0), (r"(?i)\btreatment\b", 3.0),
        (r"(?i)\bdiagnosis\b", 3.0), (r"(?i)\btherapy\b", 3.0),
        (r"(?i)\bmedicine\b", 3.0), (r"(?i)\bmedication\b", 3.0),
        (r"(?i)\bprescription\b", 3.0), (r"(?i)\bfitness\b", 2.5),
        (r"(?i)\bexercise\b", 2.5), (r"(?i)\bworkout\b", 2.5),
        (r"(?i)\bdiet\b", 2.5), (r"(?i)\bnutrition\b", 2.5),
        (r"(?i)\bmental\s*health\b", 3.0), (r"(?i)\bdepression\b", 3.0),
        (r"(?i)\banxiety\b", 3.0), (r"(?i)\bstress\b", 2.5),
        (r"(?i)\bsleep\b", 2.5), (r"(?i)\binsomnia\b", 3.0),
        (r"(?i)\bhealth\b", 3.0),
        # Thai
        ("อาการ", 3.0), ("โรค", 3.0), ("หมอ", 3.0),
        ("โรงพยาบาล", 3.0), ("ยา", 2.5), ("กินยา", 2.5),
        ("ปวด", 2.5), ("ไข้", 2.5), ("ไม่สบาย", 2.5),
        ("ออกกำลังกาย", 2.5), ("สุขภาพ", 3.0),
        ("ตรวจสุขภาพ", 3.0), ("นอนไม่หลับ", 3.0),
        ("เครียด", 2.5), ("ซึมเศร้า", 3.0),
    ],
    "legal": [
        (r"(?i)\blaw\b", 3.0), (r"(?i)\blegal\b", 3.0),
        (r"(?i)\bcontract\b", 3.0), (r"(?i)\bagreement\b", 2.5),
        (r"(?i)\bpatent\b", 3.0), (r"(?i)\btrademark\b", 3.0),
        (r"(?i)\bcopyright\b", 3.0), (r"(?i)\bintellectual\s*property\b", 3.0),
        (r"(?i)\bplaintiff\b", 3.0), (r"(?i)\bdefendant\b", 3.0),
        (r"(?i)\bcourt\b", 2.5), (r"(?i)\bjudge\b", 2.5),
        (r"(?i)\blawyer\b", 2.5), (r"(?i)\bcompliance\b", 3.0),
        (r"(?i)\bregulation\b", 2.5), (r"(?i)\brights\b", 2.5),
        (r"(?i)\bliability\b", 3.0), (r"(?i)\bfraud\b", 3.0),
        (r"(?i)\bevidence\b", 2.5),
        # Thai
        ("กฎหมาย", 3.0), ("สัญญา", 3.0), ("ละเมิด", 3.0),
        ("ฟ้อง", 2.5), ("ศาล", 2.5), ("ทนาย", 2.5),
        ("กรรมสิทธิ์", 2.5), ("ภาษี", 2.5),
    ],
    "seo": [
        (r"(?i)\bSEO\b", 3.0), (r"(?i)\bsearch\s*engine\b", 3.0),
        (r"(?i)\branking\b", 2.5), (r"(?i)\bkeyword\b", 2.5),
        (r"(?i)\bbacklink\b", 3.0), (r"(?i)\borganic\s*traffic\b", 3.0),
        (r"(?i)\bpage\s*authority\b", 2.5), (r"(?i)\bGoogle\b", 2.5),
        (r"(?i)\bSERP\b", 2.5), (r"(?i)\bCTR\b", 2.5),
        (r"(?i)\bconversion\s*rate\b", 2.5), (r"(?i)\bbounce\s*rate\b", 2.5),
        (r"(?i)\bcontent\s*marketing\b", 2.5),
        # Thai
        ("ทำ SEO", 3.0), ("ค้นหา", 2.5), ("เว็บไซต์", 2.0),
        ("การตลาดออนไลน์", 2.5), ("โฆษณา", 2.0),
        ("ผู้เข้าชม", 2.5), ("อันดับ", 2.5),
    ],
    "translation": [
        (r"(?i)\btranslate\b", 3.0), (r"(?i)\btranslation\b", 3.0),
        (r"(?i)\btranslat\b", 2.5), (r"(?i)\binterpret\b", 2.5),
        (r"(?i)\bmultilingual\b", 2.5), (r"(?i)\bbilingual\b", 2.5),
        (r"(?i)\bdictionary\b", 2.0), (r"(?i)\bvocabulary\b", 2.0),
        (r"(?i)\bgrammar\b", 2.0), (r"(?i)\blanguage\b", 2.0),
        (r"(?i)\blocalization\b", 2.5),
        # Thai
        ("แปล", 3.0), ("แปลภาษา", 3.0), ("ภาษาอังกฤษ", 2.5),
        ("คำศัพท์", 2.0), ("ไวยากรณ์", 2.0), ("สำนวน", 2.0),
    ],
    "technology": [
        (r"(?i)\btechnology\b", 3.0), (r"(?i)\btech\b", 2.5),
        (r"(?i)\bgadget\b", 2.0), (r"(?i)\bdevice\b", 2.0),
        (r"(?i)\bhardware\b", 2.5), (r"(?i)\bsoftware\b", 2.5),
        (r"(?i)\bchip\b", 2.5), (r"(?i)\bprocessor\b", 2.5),
        (r"(?i)\bGPU\b", 3.0), (r"(?i)\bCPU\b", 3.0),
        (r"(?i)\bAI\b", 3.0), (r"(?i)\bartificial\s+intelligence\b", 3.0),
        (r"(?i)\bLLM\b", 3.0), (r"(?i)\bGPT\b", 3.0),
        (r"(?i)\bChatGPT\b", 3.0), (r"(?i)\bOpenAI\b", 2.5),
        (r"(?i)\blaptop\b", 2.0), (r"(?i)\bphone\b", 2.0),
        (r"(?i)\bcybersecurity\b", 2.5), (r"(?i)\bhacking\b", 2.5),
        # Thai
        ("เทคโนโลยี", 3.0), ("ไอที", 2.5), ("คอมพิวเตอร์", 2.5),
        ("โทรศัพท์", 2.0), ("AI", 3.0), ("ปัญญาประดิษฐ์", 3.0),
        ("หุ่นยนต์", 2.5),
    ],
    "marketing": [
        (r"(?i)\bmarketing\b", 3.0), (r"(?i)\bcampaign\b", 3.0),
        (r"(?i)\bbrand\b", 2.5), (r"(?i)\badvertis\b", 2.5),
        (r"(?i)\bPPC\b", 3.0), (r"(?i)\bCPC\b", 3.0),
        (r"(?i)\bROI\b", 2.5), (r"(?i)\bconversion\b", 2.5),
        (r"(?i)\blead\b", 2.0), (r"(?i)\bfunnel\b", 2.5),
        (r"(?i)\bsales\b", 2.5), (r"(?i)\bcustomer\b", 2.0),
        (r"(?i)\bsocial\s*media\b", 2.5), (r"(?i)\bcopywriting\b", 2.5),
        (r"(?i)\bCTA\b", 2.5), (r"(?i)\bemail\s*marketing\b", 2.5),
        # Thai
        ("การตลาด", 3.0), ("โฆษณา", 2.5), ("โปรโมชั่น", 2.5),
        ("ลูกค้า", 2.0), ("ขาย", 2.0), ("แบรนด์", 2.5),
        ("โซเชียล", 2.5), ("คอนเทนต์", 2.0), ("แคมเปญ", 3.0),
    ],
    "roleplay": [
        (r"(?i)\broleplay\b", 3.0), (r"(?i)\brole\s*play\b", 3.0),
        (r"(?i)\bRP\b", 2.5), (r"(?i)\bcharacter\b", 2.5),
        (r"(?i)\bfiction\b", 2.5), (r"(?i)\bfantasy\b", 2.0),
        (r"(?i)\bstory\b", 2.0), (r"(?i)\bplot\b", 2.0),
        (r"(?i)\bnarrative\b", 2.5), (r"(?i)\bdialogue\b", 2.0),
        (r"(?i)\bworld\s*building\b", 2.5), (r"(?i)\bOC\b", 2.5),
        (r"(?i)\badventure\b", 2.0), (r"(?i)\bquest\b", 2.0),
        (r"(?i)\bhero\b", 2.0), (r"(?i)\bvillain\b", 2.0),
        # Thai
        ("roleplay", 3.0), ("ตัวละคร", 3.0), ("นิยาย", 2.5),
        ("เรื่องราว", 2.0), ("จินตนาการ", 2.5), ("ผจญภัย", 2.0),
        ("แสดงบทบาท", 3.0),
    ],
    "trivia": [
        (r"(?i)\btrivia\b", 3.0), (r"(?i)\bfact\b", 2.5),
        (r"(?i)\bquiz\b", 3.0), (r"(?i)\bquestion\b", 2.0),
        (r"(?i)\banswer\b", 2.0), (r"(?i)\bgame\b", 2.0),
        (r"(?i)\bfun\s*fact\b", 3.0), (r"(?i)\bdid\s*you\s*know\b", 3.0),
        (r"(?i)\bpuzzle\b", 2.5), (r"(?i)\brain\s*teaser\b", 2.5),
        (r"(?i)\briddle\b", 2.5), (r"(?i)\bIQ\b", 2.5),
        (r"(?i)\bgeneral\s*knowledge\b", 2.5), (r"(?i)\bpub\s*quiz\b", 3.0),
        (r"(?i)\btrue\s*or\s*false\b", 2.5),
        # Thai
        ("เกร็ดความรู้", 3.0), ("คำถาม", 2.5), ("ตอบคำถาม", 2.5),
        ("ทาย", 2.0), ("ความรู้ทั่วไป", 2.5), ("ทายปัญหา", 2.5),
        ("เฉลย", 2.0), ("จริงหรือเท็จ", 2.5),
    ],
}

# ─── State ───────────────────────────────────────────────────────

@dataclass
class TopicResult:
    topic: str
    confidence: float
    score: float
    details: dict = field(default_factory=dict)


class _State:
    def __init__(self):
        self.reset()

    def reset(self):
        self.current_topic: str | None = None
        self.current_model: str | None = None
        self.pending_topic: str | None = None
        self.consecutive_count: int = 0


_state = _State()


# ─── Scoring ─────────────────────────────────────────────────────

def _score_topic(text: str, signals: list[tuple[str, float]],
                 phrases: list[tuple[str, float]]) -> float:
    score = 0.0
    text_lower = text.lower()

    for phrase, boost in phrases:
        if phrase.lower() in text_lower:
            score += boost

    for pattern, weight in signals:
        if re.search(pattern, text):
            score += weight

    return score


def classify_context(messages: list[dict], window: int = WINDOW) -> TopicResult:
    user_messages = []
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_messages.append(msg.get("content", ""))
            if len(user_messages) >= window:
                break

    if not user_messages:
        return TopicResult(topic="none", confidence=0.0, score=0.0)

    weighted_scores: dict[str, float] = {}

    for idx, text in enumerate(reversed(user_messages)):
        if not text or not isinstance(text, str):
            continue
        weight = 0.5 + ((idx + 1) ** 1.5)

        for topic in TOPIC_SIGNALS:
            phrases = PHRASE_BOOSTS.get(topic, [])
            s = _score_topic(text, TOPIC_SIGNALS[topic], phrases)
            weighted_scores[topic] = weighted_scores.get(topic, 0.0) + (s * weight)

    if not weighted_scores:
        return TopicResult(topic="none", confidence=0.0, score=0.0)

    best_topic = max(weighted_scores, key=weighted_scores.get)
    best_score = weighted_scores[best_topic]
    total = sum(weighted_scores.values())
    confidence = min(best_score / total, CONFIDENCE_CAP) if total > 0 else 0.0

    return TopicResult(
        topic=best_topic,
        confidence=round(confidence, 4),
        score=round(best_score, 4),
    )


def should_switch_topic(
    current_topic: str | None,
    new_result: TopicResult,
    consecutive_count: int,
) -> tuple[bool, str]:
    new_topic = new_result.topic

    if new_result.confidence == 0.00:
        return True, "zero_confidence"

    if new_topic == (current_topic or "none"):
        return False, "same_topic"

    if new_result.score < MIN_SCORE:
        return False, "below_min_score"
    if new_result.confidence < MIN_CONFIDENCE:
        return False, "below_min_confidence"

    if new_result.confidence >= HIGH_CONF_THRESHOLD:
        return True, "high_confidence"

    if consecutive_count >= 2:
        return True, "confirmed"

    return False, "pending_confirmation"


# ─── Plugin Hooks ────────────────────────────────────────────────

def _pre_llm_call(**kwargs):
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

    result = classify_context(messages, window=WINDOW)
    new_topic = result.topic

    if new_topic == (_state.pending_topic or "none"):
        _state.consecutive_count += 1
    else:
        _state.pending_topic = new_topic
        _state.consecutive_count = 1

    should_switch, reason = should_switch_topic(
        _state.current_topic, result, _state.consecutive_count
    )

    if should_switch:
        _state.current_topic = result.topic
        _state.consecutive_count = 0
        _state.pending_topic = None

    active_topic = _state.current_topic or "none"
    target_model = TOPIC_MODELS.get(active_topic, DEFAULT_MODEL)
    _state.current_model = target_model

    short_name = target_model.split("/")[-1] if "/" in target_model else target_model
    short_name = short_name.split(":")[0]

    logger.info(
        "✓ TOPIC: %s | MODEL: %s | CONFIDENCE: %.2f",
        active_topic.upper(), short_name, result.confidence,
    )

    if active_topic != "none":
        sig = f"— {short_name} [{active_topic}]"
        context_text = (
            f"[topic_detect] Detected topic: {active_topic}. "
            f"Active model: {short_name}. "
            f"Confidence: {result.confidence:.2f}. "
            f"End your response with: {sig}"
        )
        return {"context": context_text, "model": target_model}

    return {"model": DEFAULT_MODEL}


def _on_session_start(**kwargs):
    _state.reset()


def register(ctx):
    cfg_enabled = True  # Could read from config.yaml here
    if not cfg_enabled:
        return
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("on_session_reset", _on_session_start)
    logger.info("topic_detect plugin loaded")
