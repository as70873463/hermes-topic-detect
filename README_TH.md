# ⚡ Hermes ARC — Adaptive Routing Core

> **ระบบ orchestration อัจฉริยะสำหรับ Hermes Agent**<br>
> จัดเส้นทางบทสนทนาตามหัวข้อที่ align กับ Arena.ai — สลับโมเดล, persona และ prompt แบบ real-time

[English](README.md) · **ไทย**

---

## ทำอะไรได้

ARC ดูว่าคุณกำลังคุยเรื่องอะไร แล้ว:

- **สลับโมเดลอัตโนมัติ** — คำถาม software/coding ไปโมเดล software, เรื่อง business/finance ไปโมเดล business/finance ฯลฯ
- **ใส่ persona** — แต่ละหัวข้อได้ system prompt เฉพาะทาง
- **แสดง signature** — แท็กเล็ก ๆ ท้ายข้อความบอกว่าใช้โมเดล/หัวข้ออะไร

หัวข้อถูกจัดให้ align กับหมวด leaderboard ของ Arena.ai เพื่อให้ user ไปดูเองได้ว่าโมเดลที่ใช้อยู่เก่งหมวดไหน แล้วเอา model มาใส่ config ได้ตรง ๆ ARC **ไม่ดึงคะแนน Arena และไม่เลือกโมเดลให้อัตโนมัติ**

ถ้า prompt ไม่เข้า specialized topic ด้วยความมั่นใจพอ ARC จะคืน `none` แล้วให้ Hermes ใช้ main/default model ทันที จงใจไม่มีหัวข้อ `general`

---

## ติดตั้ง

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash
```

Installer จัดการทุกอย่าง: plugin, config, และเช็ค runtime compatibility

เช็คว่ามีอัปเดตไหมโดยยังไม่ติดตั้ง:

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --check
```

อัปเดตแบบ explicit:

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash -s -- --update
```

หลังติดตั้ง ใส่ API key:

```bash
echo 'OPENROUTER_API_KEY=<your-key>' >> ~/.hermes/.env
hermes gateway restart
```

---

## ตั้งค่า

`~/.hermes/config.yaml` ขั้นต่ำ:

```yaml
plugins:
  enabled:
    - topic_detect

topic_detect:
  enabled: true
  routing_mode: hybrid
  signature:
    enabled: true
  update_check:
    enabled: true
    # เช็คครั้งเดียวหลัง Hermes restart; เขียน log เท่านั้น ไม่แปะท้าย chat
    url: https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/plugin.yaml
    timeout_seconds: 2.5
  topics:
    software_it:
      # Arena refs: Software & IT Services, Coding
      provider: openrouter
      model: your/software-model
    business_finance:
      # Arena ref: Business, Management, & Financial Ops
      provider: openrouter
      model: your/business-finance-model
```

### วิธีเลือกโมเดล

1. เปิด Arena.ai
2. เลือก leaderboard/category ที่ใกล้กับหัวข้อที่ต้องการ
3. เลือก model ที่เชื่อถือจากหมวดนั้น
4. เอา model มาใส่ที่ `topic_detect.topics.<topic>.model`

ARC ใช้ Arena เป็น **reference taxonomy** ไม่ใช่ live data source

### การอัปเดต

ARC มี 2 ทางให้รู้ว่ามีอัปเดต:

- Manual: รัน installer ด้วย `--check` เพื่อเทียบ version local กับ GitHub `plugin.yaml`
- Runtime: หลัง Hermes restart, ARC จะเช็ค GitHub ครั้งเดียวแล้วเขียน log ถ้ามีเวอร์ชันใหม่กว่า โดยจะ **ไม่ spam ในข้อความ chat**

ปิด runtime update check:

```yaml
topic_detect:
  update_check:
    enabled: false
```

ถ้าลบ topic block ออก หรือ topic นั้นไม่มี `provider`/`model` ARC จะไม่ส่ง
runtime override สำหรับหัวข้อนั้น และ Hermes จะใช้ main/default model ต่อทันที
นี่เป็นพฤติกรรมที่ตั้งใจไว้ เพื่อให้หมวดที่ specialist model ไม่คุ้มยัง fallback
ได้อย่างปลอดภัย

### Routing Modes

| Mode | พฤติกรรม |
|------|----------|
| `keyword` | เร็ว — จับคู่คำสำคัญ |
| `semantic` | ฉลาด — ใช้ LLM จำแนก |
| `hybrid` | แนะนำ — keyword ก่อน, semantic เป็น fallback |

### หัวข้อหลักที่รองรับ

- `software_it` — Arena refs: Software & IT Services, Coding
- `math` — Arena refs: Mathematical, Math
- `science` — Arena ref: Life, Physical, & Social Science
- `business_finance` — Arena ref: Business, Management, & Financial Ops
- `legal_government` — Arena ref: Legal & Government
- `medicine_healthcare` — Arena ref: Medicine & Healthcare
- `writing_language` — Arena refs: Writing/Literature/Language, Creative Writing, Language, English, Non-English, language-specific boards
- `entertainment_media` — Arena ref: Entertainment, Sports, & Media

หมวด Arena อย่าง Expert, Hard Prompts, Instruction Following, Multi-Turn, Longer Query และ language-specific boards ถือเป็น modifier/future metadata ไม่ใช่ primary route ในเวอร์ชันนี้

ข้อควรระวังของบางหมวด:

- `entertainment_media` ควรถือเป็น optional เพราะคำถามหนัง/เกม/กีฬา/สื่อในชีวิตจริง
  มักไม่จำเป็นต้องใช้ specialist model ถ้า main model ตอบได้ดีอยู่แล้ว สามารถไม่ใส่
  model ของหมวดนี้เพื่อ fallback กลับ main model ได้
- `writing_language` กว้างโดยตั้งใจ และมี tension ภายใน: creative writing ต้องการ
  creativity/style ส่วน translation ต้องการ multilingual accuracy ถ้าอนาคตมี complaint
  เรื่อง route ไม่ตรง หมวดนี้คือ candidate แรกที่ควร split หรือเพิ่ม metadata route

`Exclude Ties` เป็น leaderboard filter ไม่เกี่ยวกับ ARC

### Provider ที่ใช้ได้

ทุก provider ที่ Hermes รองรับ:

- **OpenRouter** — ใส่ `provider: openrouter` + `model:`
- **OpenAI-compatible** (DeepSeek, vLLM, etc.) — ใส่ `provider:` + `base_url:` + `api_key:`
- **OAuth provider** — ใส่ `provider:` อย่างเดียวได้ ถ้า Hermes จัดการ auth ให้ provider นั้น

---

## Signature

เมื่อเปิดใช้งาน ท้ายแต่ละข้อความจะมีแท็ก:

```text
- nemotron-3-super-120b-a12b [software_it]
- owl-alpha [business_finance]
- owl-alpha [none]
```

ปิดด้วย `signature.enabled: false`

---

## ตรวจสอบ

```bash
hermes plugins list | grep topic_detect
hermes logs | grep topic_detect
```

Log ที่คาดหวัง:

```text
topic_detect: loaded
topic_detect: switching provider=openrouter model=nvidia/nemotron-3-super-120b-a12b:free
topic_detect: signature=- nemotron-3-super-120b-a12b [software_it]
```

---

## แก้ปัญหา

| ปัญหา | วิธีแก้ |
|-------|--------|
| Plugin ไม่โหลด | เช็ค `plugins.enabled` มี `topic_detect` และ `enabled: true` แล้ว restart |
| หัวข้อไม่สลับ | ลด `min_confidence` เป็น `0.3` หรือใช้ `routing_mode: semantic` |
| สลับบ่อยเกินไป | เพิ่ม `inertia` เป็น `3` หรือ `4` |
| prompt ทั่วไปถูก route ผิด | ควรคืน `none`; เพิ่ม `min_confidence` ถ้าจำเป็น |
| โมเดลไม่สลับ provider | รัน `python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --check` แล้ว patch ถ้าจำเป็น |
| Persona ไม่ถูกใส่ | เหมือนด้านบน — patch Hermes core เพื่อรองรับ `system_prompt` override |

---

## License

MIT
