# ⚡ Hermes ARC — Adaptive Routing Core

> **Reference implementation สำหรับ topic-aware runtime model routing บน Hermes Agent**  
> ARC ตรวจว่าผู้ใช้กำลังคุยเรื่องอะไร แล้ว route turn นั้นไปยัง model/persona ที่เหมาะกับหัวข้อนั้นที่สุด

<p align="center">
  <strong>Topic-aware routing</strong> · <strong>Runtime model switching</strong> · <strong>Arena-aligned taxonomy</strong> · <strong>Hermes plugin</strong>
</p>

<p align="center">
  <strong>ไทย</strong> · <a href="README.md">English</a>
</p>

---

## ทำไม ARC ถึงมีอยู่

Hermes ใช้ main model ตัวเดียวตอบทุกงานได้ แต่ในโลกจริงมันไม่ใช่ทางเลือกที่ดีที่สุดเสมอไป:

- คำถาม coding อาจเหมาะกับโมเดลที่แข็งด้าน coding มากกว่า
- คำถาม finance อาจเหมาะกับโมเดลด้าน business/finance มากกว่า
- งาน creative/media อาจไม่จำเป็นต้องใช้ reasoning model แพง ๆ
- แชตทั่วไปควรอยู่กับ main model โดยไม่สลับมั่ว

**Hermes ARC ทำให้ model routing เป็น plugin-level capability:**

```text
User message
  → classify topic
  → choose configured model/persona
  → call Hermes with a runtime override
  → append a small routing signature
```

ARC ตั้งใจให้เล็ก ใช้งานจริง และเป็นฐานสำหรับ smart routing ในอนาคต ไม่ได้พยายามเป็น router อัจฉริยะครบทุกอย่างตั้งแต่แรก

---

## ทำอะไรได้

- **ตรวจจับหัวข้อ** ด้วย keyword, semantic หรือ hybrid routing
- **สลับ model/provider แบบ runtime** ตาม `topic_detect.topics`
- **ใส่ persona เฉพาะหัวข้อ** จาก `AGENTS.md`
- **fallback ปลอดภัย** กลับ main Hermes model ถ้าหัวข้อไม่ชัดพอ
- **แสดง signature** เพื่อให้เห็นว่า turn นั้น route ไปไหน

ตัวอย่าง signature:

```text
- gemma-4-31b:free [software_it]
- minimax-m2.5:free [business_finance]
- glm-4.5-air:free [entertainment_media]
- gpt-5.5 [general]
```

ภายใน ARC ยังใช้ `none` เพื่อหมายถึง “ไม่มี specialized topic ที่มั่นใจพอ” แต่ฝั่ง user-facing signature จะแสดงเป็น `[general]` เพราะเข้าใจง่ายกว่า

---

## ความสัมพันธ์กับ Hermes Core

ตอนนี้ ARC ทำงานเป็น Hermes plugin และอาจต้องใช้ compatibility patch ใน Hermes version ที่ `pre_llm_call` ยัง apply runtime override ไม่ได้

งาน upstream ที่เกี่ยวข้อง:

- Smart routing discussion: https://github.com/NousResearch/hermes-agent/issues/21827
- Core primitive proposal: https://github.com/NousResearch/hermes-agent/issues/23739

ถ้า Hermes core เพิ่ม native `pre_llm_call` runtime override, ARC จะถอดทาง monkey-patch ออก แล้วใช้ hook นั้นได้โดยตรง

Architecture เป้าหมาย:

```text
Hermes core pre_llm_call runtime override
  → router plugins/providers
  → topic routing, complexity routing, Manifest-style smart routing
```

---

## ติดตั้งเร็ว

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash
```

เช็ค update โดยยังไม่ติดตั้ง:

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --check
```

อัปเดตแบบ explicit:

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --update
```

หลังติดตั้ง ใส่ provider key เช่น OpenRouter:

```bash
echo 'OPENROUTER_API_KEY=<your-key>' >> ~/.hermes/.env
hermes gateway restart
```

---

## Config แนะนำ

เพิ่มหรืออัปเดต section นี้ใน `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - topic_detect

topic_detect:
  enabled: true
  routing_mode: hybrid
  inertia: 2
  min_confidence: 0.45
  agents_file: ~/.hermes/plugins/topic_detect/AGENTS.md
  semantic:
    enabled: true
    provider: openrouter
    model: baidu/cobuddy:free
    min_confidence: 0.7
    base_url: https://openrouter.ai/api/v1
    api_key: ${OPENROUTER_API_KEY}
  signature:
    enabled: true
  update_check:
    enabled: true
    url: https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/plugin.yaml
    timeout_seconds: 2.5
  topics:
    software_it:
      provider: openrouter
      model: google/gemma-4-31b:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    math:
      provider: openrouter
      model: google/gemma-4-31b:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    science:
      provider: openrouter
      model: google/gemma-4-31b:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    business_finance:
      provider: openrouter
      model: minimax/minimax-m2.5:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    legal_government:
      provider: openrouter
      model: minimax/minimax-m2.5:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    medicine_healthcare:
      provider: openrouter
      model: minimax/minimax-m2.5:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    writing_language:
      provider: openrouter
      model: google/gemma-4-31b:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
    entertainment_media:
      provider: openrouter
      model: z-ai/glm-4.5-air:free
      base_url: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
```

นี่เป็นแค่ตัวอย่าง default ที่ใช้งานได้จริง ARC **ไม่ดึงคะแนน Arena และไม่เลือกโมเดลให้อัตโนมัติ** ผู้ใช้ยังเป็นคนกำหนด mapping เอง

---

## Topics ที่รองรับ

ARC ใช้ primary topic taxonomy ที่ align กับ Arena:

| Topic | ใช้กับอะไร |
|---|---|
| `software_it` | programming, debugging, infra, software/IT systems |
| `math` | calculation, proofs, symbolic reasoning, quantitative problems |
| `science` | science explanation, mechanisms, research-style questions |
| `business_finance` | markets, finance, accounting, business operations, strategy |
| `legal_government` | legal, policy, compliance, public-sector questions |
| `medicine_healthcare` | medical/healthcare information และคำตอบที่ระวัง safety |
| `writing_language` | writing, editing, translation, literature, language nuance |
| `entertainment_media` | movies, games, sports, media analysis, pop culture |

หมวด Arena เช่น Expert, Hard Prompts, Instruction Following, Multi-Turn, Longer Query และ language-specific boards ถือเป็น future metadata/modifier ไม่ใช่ primary route ใน version นี้

---

## Routing Modes

| Mode | พฤติกรรม |
|---|---|
| `keyword` | deterministic keyword matching เร็วที่สุด |
| `semantic` | ใช้ LLM classification |
| `hybrid` | แนะนำ: keyword ก่อน semantic fallback |

ค่าที่ควรรู้:

- `min_confidence`: เพิ่มเพื่อลดการ route พลาด, ลดเพื่อ route ให้ aggressive ขึ้น
- `inertia`: เพิ่มเพื่อลดการสลับหัวข้อถี่ใน multi-turn conversation
- `semantic.min_confidence`: confidence ขั้นต่ำของ semantic classifier

---

## ตรวจสอบ

```bash
hermes plugins list | grep topic_detect
hermes logs | grep topic_detect
```

ตัวอย่าง log:

```text
topic_detect: loaded
topic_detect: switching provider=openrouter model=google/gemma-4-31b:free
topic_detect: signature=- gemma-4-31b:free [software_it]
```

---

## แก้ปัญหา

| ปัญหา | วิธีแก้ |
|---|---|
| Plugin ไม่โหลด | เช็ค `plugins.enabled` มี `topic_detect` แล้ว restart Hermes |
| หัวข้อไม่สลับ | ลด `min_confidence` หรือใช้ `routing_mode: semantic` |
| สลับบ่อยเกินไป | เพิ่ม `inertia` เป็น `3` หรือ `4` |
| prompt ทั่วไปถูก route ผิด | เพิ่ม `min_confidence`; prompt ไม่ชัดควรเป็น internal `none` / display `[general]` |
| model/provider ไม่สลับ | รัน `python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --check` แล้ว apply compatibility patch ถ้าจำเป็น |
| persona ไม่ถูกใส่ | เหมือนด้านบน; Hermes core รุ่นเก่าต้องรองรับ runtime system-prompt override |

---

## Roadmap

- **v1:** Topic-aware runtime model routing
- **v1.x:** Compatibility ที่สะอาดขึ้นหลัง upstream `pre_llm_call` runtime override ถูก merge
- **v2:** Complexity-aware routing: simple vs hard prompts, latency/cost preference, reasoning depth
- **v3:** Smart-router interface ที่ต่อ external router แบบ Manifest-style ได้

---

## Design Principles

- **Configurable, not magical.** ผู้ใช้เลือก model mapping เอง
- **Main model is the safe fallback.** ไม่มั่นใจหัวข้อ → ไม่ override
- **Transparent but quiet.** มี signature เล็ก ๆ ไม่รก chat
- **Plugin first, core-friendly later.** ARC พิสูจน์ behavior วันนี้ และ align กับ Hermes core hook ที่สะอาดกว่าในอนาคต

---

## License

MIT
