# ⚡ Hermes ARC — Adaptive Routing Core

> **ระบบ orchestration อัจฉริยะสำหรับ Hermes Agent**<br>
> จัดเส้นทางบทสนทนาตามหัวข้อ — สลับโมเดล, persona และ prompt แบบ real-time

[English](README.md) · **ไทย**

---

## ทำอะไรได้

ARC ดูว่าคุณกำลังคุยเรื่องอะไร แล้ว:

- **สลับโมเดลอัตโนมัติ** — คำถามเรื่อง coding ไปโมเดล coding, เรื่องการเงินไปโมเดลการเงิน
- **ใส่ persona** — แต่ละหัวข้อได้ system prompt เฉพาะทาง
- **แสดง signature** — แท็กเล็กๆ ท้ายข้อความบอกว่าใช้โมเดล/หัวข้ออะไร

หัวข้อไม่สลับทันที — ARC สะสมความมั่นใจข้ามหลาย turn ทำให้ routing รู้สึกเป็นธรรมชาติ

---

## ติดตั้ง

```bash
curl -fsSL https://raw.githubusercontent.com/ShockShoot/hermes-arc/main/install.sh | bash
```

Installer จัดการทุกอย่าง: plugin, config, และเช็ค runtime compatibility

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
  - topic_detect

topic_detect:
  enabled: true
  routing_mode: hybrid
  signature:
    enabled: true
  topics:
    programming:
      provider: openrouter
      model: inclusionai/ring-2.6-1t:free
    finance:
      provider: openrouter
      model: openrouter/owl-alpha
```

แค่นี้ ARC ทำงานได้ทันที — installer เติมค่าเริ่มต้นให้

### Routing Modes

| Mode | พฤติกรรม |
|------|----------|
| `keyword` | เร็ว — จับคู่คำสำคัญ |
| `semantic` | ฉลาด — ใช้ LLM จำแนก |
| `hybrid` | แนะนำ — keyword ก่อน, semantic เป็น fallback |

### หัวข้อที่รองรับ

`programming` · `finance` · `marketing` · `translation` · `legal` · `health` · `roleplay` · `seo` · `science` · `technology` · `academia` · `trivia`

แต่ละหัวข้อมี persona ในตัวจาก `AGENTS.md`

### Provider ที่ใช้ได้

ทุก provider ที่ Hermes รองรับ:

- **OpenRouter** — ใส่ `provider: openrouter` + `model:`
- **OpenAI-compatible** (DeepSeek, vLLM, etc.) — ใส่ `provider:` + `base_url:` + `api_key:`
- **OAuth** (OpenAI Codex, Anthropic) — ใส่ `provider:` อย่างเดียว, ไม่ต้องใส่ `api_key`

---

## Signature

เมื่อเปิดใช้งาน ท้ายแต่ละข้อความจะมีแท็ก:

```
- ring-2.6-1t [programming]
- owl-alpha [finance]
- ring-2.6-1t [programming → finance]
```

ปิดด้วย `signature.enabled: false`

---

## ตรวจสอบ

```bash
hermes plugins list | grep topic_detect
hermes logs | grep topic_detect
```

Log ที่คาดหวัง:

```
topic_detect: loaded
topic_detect: switching provider=openrouter model=inclusionai/ring-2.6-1t:free
topic_detect: signature=- ring-2.6-1t [programming]
```

---

## แก้ปัญหา

| ปัญหา | วิธีแก้ |
|-------|--------|
| Plugin ไม่โหลด | เช็ค `plugins: [topic_detect]` และ `enabled: true` ใน config แล้ว restart |
| หัวข้อไม่สลับ | ลด `min_confidence` เป็น `0.3` หรือใช้ `routing_mode: semantic` |
| สลับบ่อยเกินไป | เพิ่ม `inertia` เป็น `3` หรือ `4` |
| โมเดลไม่สลับ provider | รัน `python3 ~/.hermes/plugins/topic_detect/patch_run_agent.py --check` แล้ว patch ถ้าจำเป็น |
| Persona ไม่ถูกใส่ | เหมือนด้านบน — patch Hermes core เพื่อรองรับ `system_prompt` override |

---

## License

MIT
