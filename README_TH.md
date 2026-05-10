# ⚡ Hermes ARC — Adaptive Routing Core

> **ระบบ orchestration หลายเอเจนต์แบบฉลาดสำหรับ Hermes Agent**<br>
> จัดเส้นทางบทสนทนาตามหัวข้อ — สลับโมเดล persona และ prompt แบบ real-time พร้อมแรงเฉื่อยของบริบทที่ให้ความรู้สึกเป็นธรรมชาติ

[English](README.md) · **ไทย**

![License](https://img.shields.io/badge/license-MIT-green)
![Hermes Plugin](https://img.shields.io/badge/Hermes-plugin-blue)
![Status](https://img.shields.io/badge/status-v2.1--beta-orange)

**ชื่อผลิตภัณฑ์:** Hermes ARC (Adaptive Routing Core)<br>
**ชื่อปลั๊กอินภายใน:** `topic_detect` — คงไว้เพื่อ backward compatibility<br>
**Config key:** `topic_detect:` — ยัง **ห้าม rename** ตอนนี้

Hermes ARC คือ adaptive conversational orchestration layer สำหรับ [Hermes Agent](https://hermes-agent.nousresearch.com) เดิมเริ่มจากระบบตรวจจับหัวข้อ แต่พัฒนาเป็น runtime น้ำหนักเบาสำหรับ route บทสนทนาไปยังโมเดล persona prompt และในอนาคตจะรวมถึง policy ของ tools/memory ด้วย

---

## 🚀 การติดตั้ง

### ติดตั้งแบบคำสั่งเดียว

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash
```

Folderที่อยู่ Plugin:

```txt
~/.hermes/plugins/topic_detect
```

ระหว่างติดตั้ง ARC จะอัปเดต `~/.hermes/config.yaml` ให้มี `plugins:` และ block `topic_detect:` ที่จำเป็นครบถ้ายังไม่มี โดยจะไม่ทับค่าที่ user ตั้งเองอยู่แล้ว แค่เติม field ที่ขาด และสร้าง backup config แบบ timestamp ก่อนเขียนไฟล์

จากนั้น ARC จะหา location ของ Hermes `run_agent.py` ก่อน แล้วค่อยตรวจว่า runtime รองรับ override สำหรับ `system_prompt` และ `response_suffix` หรือยัง ถ้าเจอ Hermes runtime มากกว่า 1 ตัว installer จะให้เลือกก่อนว่าจะ check/patch ตัวไหน ถ้ายังไม่รองรับจะถามก่อน patch Hermes core และสร้าง backup แบบ timestamp ไว้ก่อนเสมอ

สำหรับ unattended install:

```bash
# Auto-patch runtime ถ้าจำเป็น
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --patch-runtime

# ติดตั้งโดยไม่แก้ config.yaml
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --no-config

# ติดตั้งกับ config path ที่กำหนดเอง
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --config-path /path/to/config.yaml

# Auto-patch runtime เฉพาะ path กรณีมีหลาย Hermes installs
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --patch-runtime --run-agent-path /path/to/run_agent.py

# ห้าม patch runtime
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --no-patch-runtime
```

### ติดตั้งด้วยตัวเอง

```bash
# 1. Clone repo
git clone https://github.com/ShockShoot/hermes-arc.git
cd hermes-arc

# 2. Copy plugin files
mkdir -p ~/.hermes/plugins/topic_detect
cp __init__.py state.py classifier.py semantic.py config.py \
   agent_loader.py signature.py patch_run_agent.py AGENTS.md plugin.yaml README.md README_TH.md \
   ~/.hermes/plugins/topic_detect/

# 3. Enable plugin
hermes plugins enable topic_detect

# 4. Restart Hermes gateway หรือปิด/เปิด Hermes CLI ใหม่
hermes gateway restart
```

### ตรวจสอบการติดตั้ง

```bash
hermes plugins list | grep topic_detect
hermes logs | grep topic_detect
```

ตัวอย่าง log ที่อาจเห็น:

```txt
topic_detect: loaded
topic_detect: switching provider=openrouter model=inclusionai/ring-2.6-1t:free
topic_detect: signature=- ring-2.6-1t [programming]
```

---

## ✅ Runtime Compatibility Check

ARC มี checker/patcher สำหรับตรวจ runtime override support ของ Hermes core โดย installer จะรัน check ให้อัตโนมัติ และถามก่อน patch ถ้าพบว่ายังไม่ compatible

Manual discovery/check:

```bash
# list Hermes runtime ที่ค้นเจอ
python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --list

# check runtime ที่เลือกอัตโนมัติ หรือถามถ้าเจอหลายตัว
python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --check

# check runtime เฉพาะ path
python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --check --path /path/to/run_agent.py
```

ผลลัพธ์ที่ควรได้เมื่อ compatible ครบ:

```txt
pre_llm_call hook: ✅
reads runtime_override: ✅
applies model override: ✅
applies provider override: ✅
applies system_prompt override: ✅
uses switch_model runtime: ✅
handles response_suffix: ✅
```

ถ้า `system_prompt` หรือ `response_suffix` ยังไม่รองรับ model routing อาจยังทำงานได้ แต่ persona injection/signature behavior จะถูกจำกัดจนกว่า `run_agent.py` จะถูก patch

Patch runtime ที่รองรับได้ด้วย:

```bash
# auto-select/prompt
python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --patch

# หรือ patch runtime เฉพาะ path
python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --patch --path /path/to/run_agent.py
```

จากนั้น restart Hermes

---

## 🤔 ปัญหาที่ Hermes ARC แก้

ระบบ multi-agent หลายตัวสลับโมเดลแบบทันทีทันใด ข้อความหนึ่งถูกส่งให้ coding expert แต่อีกข้อความถูกส่งไปอีกโมเดลแบบเงียบๆ ทำให้บทสนทนารู้สึกกระตุก ไม่ต่อเนื่อง และเสีย flow

Hermes ARC แก้ด้วยการ classify intent สะสม confidence ข้าม turn และจะเปลี่ยน route เมื่อสัญญาณแรงพอเท่านั้น ผลลัพธ์คือ routing ที่รู้สึกเป็นธรรมชาติ ไม่ใช่กลไกแข็งๆ

---

## ✨ Features

### 🔀 Runtime Model Routing

สลับ provider, model, base URL และ API key แยกตาม topic ผ่าน `config.yaml` เมื่อ active topic เปลี่ยน Hermes จะโหลดโมเดลที่เหมาะสมทันทีโดยไม่ต้องเปิด model picker หรือ restart ทุกครั้ง

ตัวอย่าง:

```yaml
topic_detect:
  topics:
    programming:
      provider: openrouter
      model: inclusionai/ring-2.6-1t:free

    marketing:
      provider: openrouter
      model: openrouter/owl-alpha
```

### 🧠 Smart Inertia Engine

Topic จะ **ไม่ switch ทันที** แต่จะสะสม confidence ข้าม turn:

```txt
threshold = max(1.5, inertia × 0.8)
```

พฤติกรรม:

- Topic เดิมจะ reinforce route ปัจจุบัน
- Topic คู่แข่งจะสะสมคะแนนข้าม turn
- Switch จะเกิดเมื่อคะแนนสะสมถึง threshold เท่านั้น

ตัวอย่าง:

```txt
finance 0.82
finance 0.91
total = 1.73
→ switch
```

ผลลัพธ์: continuity นุ่มขึ้น แทนที่จะ ping-pong routing

ไฟล์หลัก: `state.py`

### ⚡ Hybrid Routing

| Mode | Behavior |
|------|----------|
| `keyword` | เร็วที่สุด — deterministic keyword/phrase scoring |
| `semantic` | ฉลาดที่สุด — LLM-based classification ผ่าน OpenRouter |
| `hybrid` | แนะนำสำหรับ production — keyword ก่อน แล้ว fallback เป็น semantic เมื่อ confidence ต่ำ |

โหมดที่แนะนำ:

```txt
keyword first → semantic fallback
```

### 🎭 Persona Injection

Topic-specific expert persona โหลดจาก `AGENTS.md` และ inject เป็น `system_prompt` ตอน runtime

Topic ที่รองรับ:

```txt
programming · finance · marketing · translation · legal · health
roleplay · seo · science · technology · academia · trivia
```

ตัวอย่าง persona:

```md
# finance

You are a careful finance analyst.

Rules:
- Focus on downside risk.
- Separate facts from opinions.
- Avoid emotional investing advice.
```

### 🔍 Signature Transparency Layer

แต่ละ response สามารถแนบ routing tag สั้นๆ เพื่อให้เห็นว่า ARC กำลัง route อะไรอยู่:

```txt
- ring-2.6-1t [programming]
- owl-alpha [marketing]
- ring-2.6-1t [programming → finance]
```

เปิด/ปิดได้ด้วย:

```yaml
topic_detect:
  signature:
    enabled: true
```

### 🧩 Runtime Prompt Injection

ARC สามารถ return runtime override แบบนี้:

```python
runtime_override = {
    "provider": "openrouter",
    "model": "inclusionai/ring-2.6-1t:free",
    "base_url": "https://openrouter.ai/api/v1",
    "api_key": "${OPENROUTER_API_KEY}",
    "system_prompt": "You are an expert software engineer...",
}
```

สิ่งนี้ทำให้ model routing + persona routing ถูกควบคุมจาก decision layer เดียวกัน

ถ้าไม่มี topic target ที่ match, ARC จะคืน `restore_main: true` แทนการเลือก model ของ plugin เอง compatibility patch จะ restore runtime หลักเดิมของ Hermes ใน session นั้น ตอนนี้ ARC ไม่มี `topic_detect.default` แยกแล้ว เพราะ default ของ plugin อาจตีกับ main default model ของ Hermes ได้

> Compatibility note: ARC compatibility รุ่นใหม่ใช้ provider resolver ของ Hermes และเรียก `switch_model()` โดยตรง เพื่อรองรับ cross-provider routing, การเปลี่ยน `api_mode`, OAuth/subscriber credentials, provider-specific headers, client rebuild และ context-compressor metadata ใช้ checker ด้านบนเพื่อตรวจสอบ

---

## 🏗 Architecture

```txt
User Input
   ↓
Keyword Classifier       ← fast, deterministic
   ↓
Semantic Router          ← LLM-based fallback via OpenRouter
   ↓
Smart Inertia Engine     ← confidence accumulation across turns
   ↓
Topic State              → model routing + persona selection
   ↓
Runtime Override         → provider / model / base_url / api_key / system_prompt
   ↓
Signature Layer          → transparency tag appended to response
```

ตอนนี้ Hermes ARC ไม่ใช่แค่ *topic detection* แล้ว แต่มันใกล้เคียง adaptive conversational orchestration framework — lightweight multi-agent runtime สำหรับ models, personas, tools, memory และ behavior

---

## ⚙️ Configuration

ตัวอย่างเต็ม (`~/.hermes/config.yaml`):

```yaml
plugins:
  - topic_detect

topic_detect:
  enabled: true
  inertia: 2
  min_confidence: 0.45
  routing_mode: hybrid        # keyword | semantic | hybrid

  signature:
    enabled: true

  semantic:
    enabled: true
    provider: openrouter
    model: baidu/cobuddy:free
    min_confidence: 0.7
    base_url: https://openrouter.ai/api/v1
    api_key: ${OPENROUTER_API_KEY}

  # Per-topic model routing
  topics:
    programming:
      provider: openrouter
      model: inclusionai/ring-2.6-1t:free
    finance:
      provider: openrouter
      model: inclusionai/ring-2.6-1t:free
    science:
      provider: openrouter
      model: inclusionai/ring-2.6-1t:free
    academia:
      provider: openrouter
      model: inclusionai/ring-2.6-1t:free
    health:
      provider: openrouter
      model: openrouter/owl-alpha
    legal:
      provider: openrouter
      model: openrouter/owl-alpha
    seo:
      provider: openrouter
      model: openrouter/owl-alpha
    translation:
      provider: openrouter
      model: openrouter/owl-alpha
    technology:
      provider: openrouter
      model: openrouter/owl-alpha
    marketing:
      provider: openrouter
      model: openrouter/owl-alpha
    roleplay:
      provider: openrouter
      model: baidu/cobuddy:free
    trivia:
      provider: openrouter
      model: baidu/cobuddy:free
```

Secret ควรอยู่ใน `~/.hermes/.env` ไม่ใช่ใส่ตรงๆ ใน `config.yaml` ให้เก็บ OpenRouter key ไว้ในตัวแปรมาตรฐาน `OPENROUTER_API_KEY`

---

## 🧭 Routing Mode Logic

```python
if mode == "keyword":
    result = keyword_classify(messages)

elif mode == "semantic":
    result = semantic_classify(messages)

elif mode == "hybrid":
    result = keyword_classify(messages)
    if result.confidence < semantic.min_confidence:
        semantic_result = semantic_classify(messages)
        if semantic_result.confidence > result.confidence:
            result = semantic_result

state.decide(result.topic, result.confidence, inertia, min_confidence)
```

---

## 📁 Plugin Files

| File | Purpose |
|------|---------|
| `__init__.py` | Plugin entry point: register `pre_llm_call` hook และ return runtime overrides |
| `classifier.py` | Keyword classifier พร้อม weighted scoring, phrase boosts และ recency weighting |
| `semantic.py` | LLM-based semantic classifier ผ่าน OpenRouter API |
| `state.py` | Smart Inertia Engine — confidence accumulation และ topic switching |
| `config.py` | โหลด `topic_detect:` config เป็น typed dataclasses |
| `agent_loader.py` | parse `AGENTS.md` เป็น mapping topic-to-persona |
| `signature.py` | สร้าง transparency signature tag |
| `patch_run_agent.py` | Compatibility checker/patcher สำหรับ Hermes core runtime override support |
| `AGENTS.md` | Persona definitions สำหรับทุก topic ที่รองรับ |
| `plugin.yaml` | Plugin metadata |
| `README.md` | เอกสารภาษาอังกฤษ |
| `README_TH.md` | เอกสารภาษาไทย |

---

## 🔑 Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENROUTER_API_KEY` | จำเป็นสำหรับ semantic mode และ OpenRouter topic models | API key สำหรับ OpenRouter |

เก็บ keys ใน `~/.hermes/.env` อย่า commit secrets, tokens, logs, cache files หรือ `.env`

---

## 🛠 Troubleshooting

### Plugin ไม่โหลด

```bash
hermes plugins list | grep topic_detect
hermes logs | grep topic_detect
```

ตรวจว่ามี config ทั้งสองส่วนนี้:

```yaml
plugins:
  - topic_detect

topic_detect:
  enabled: true
```

จากนั้น restart Hermes gateway หรือเปิด CLI ใหม่:

```bash
hermes gateway restart
```

### Topic ไม่ switch

- ลด `min_confidence` ชั่วคราว เช่น `0.3`
- ใช้ `routing_mode: semantic` ถ้าต้องการ classification ที่เข้าใจบริบทละเอียดขึ้น
- ตรวจ logs เพื่อดู classifier confidence และ topic ที่เลือก

ถ้าไม่มี topic ไหน match ถือว่าปกติ: ARC จะไม่ส่ง runtime override และ Hermes จะใช้ `model:` หลักต่อไป

### Topic switch แปลกๆ

- เพิ่ม `inertia` เช่น `3` หรือ `4`
- เพิ่ม `min_confidence` ถ้า keyword noisy ทำให้ false positive
- ใช้ `hybrid` แทน semantic ล้วน ถ้าต้องการ behavior ที่ deterministic กว่า

### Semantic classifier fail

- ตรวจว่า `OPENROUTER_API_KEY` มีอยู่ใน `~/.hermes/.env`
- ตรวจว่า semantic model ใช้งานได้บนบัญชี OpenRouter ของคุณ
- ลองเปลี่ยน semantic classifier model ใน `topic_detect.semantic.model`

### Persona injection ไม่ทำงาน

รัน:

```bash
python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --check
```

ถ้า `system_prompt override` ยังไม่รองรับ ให้ patch Hermes core หรือใช้ ARC เฉพาะ model routing/signature behavior

---

## 🗺 Roadmap

| Priority | Feature | Status |
|----------|---------|--------|
| P1 | Persistent state ข้าม sessions (`~/.hermes/state/topic_state.json`) | Planned |
| P2 | Weighted multi-topic routing สำหรับบทสนทนาหลาย domain | Planned |
| P3 | Topic-aware tool sandboxing | Planned |
| P4 | Cost-aware routing ตาม complexity, latency, token budget และ reasoning need | Planned |

Future ecosystem modules อาจรวมถึง:

- Hermes ARC Runtime
- Hermes ARC Memory
- Hermes ARC Agents
- Hermes ARC Router
- Hermes ARC Tools
- Hermes ARC Studio

---

## 🧱 Design Principles

- ใช้ `Hermes ARC` เป็น product/platform name
- คง `topic_detect` เป็น internal plugin name จนกว่าจะมี coordinated migration
- ให้ความสำคัญกับ smooth routing transitions มากกว่า instant switches
- ทำให้ routing มองเห็นและ debug ได้ผ่าน signatures
- เก็บ secrets นอก config และนอก git
- เลือก incremental compatibility กับ Hermes core มากกว่า risky rewrites

---

## 📄 License

MIT — เหมือนกับ [Hermes Agent](https://github.com/NousResearch/hermes-agent)

---

<div align="center">
  <sub>Built for <a href="https://hermes-agent.nousresearch.com">Hermes Agent</a> · Maintained by <a href="https://github.com/ShockShoot">ShockShoot</a></sub>
</div>
