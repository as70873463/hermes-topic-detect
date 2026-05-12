# hermes-arc v2.0 Intent-Based Classifier Rewrite Plan

**Goal:** เปลี่ยน ARC จาก topic-based routing เป็น intent/action-first routing เพื่อไม่ให้ subject ของ prompt ลาก route ผิดจาก action ที่ผู้ใช้ต้องการจริง

## Design Principle

Classifier ต้องถามก่อนว่า **ผู้ใช้กำลังขอให้ทำอะไร** ไม่ใช่แค่ **ผู้ใช้พูดถึงเรื่องอะไร**

Routing priority:
1. `TECHNICAL_ACTION`
2. `ANALYTICAL_ACTION`
3. `CREATIVE_ACTION`
4. subject-based topic classification เดิม
5. `none`

`TECHNICAL_ACTION` มี absolute priority override: ถ้า intent คือแก้/รัน/config/debug/build/code/server/script/API/database ให้ route `software_it` เสมอ ไม่ว่า subject จะเป็นนิยาย finance legal healthcare หรืออย่างอื่น

## Files to Modify

- `classifier.py`
  - เพิ่ม action detection layer ก่อน subject detection เสมอ
  - ออกแบบเป็น extensible action registry ไม่ใช่ giant hardcoded if/else
  - ใช้ normalized text, partial matching, lightweight heuristics, keyword groups + weighted confidence
  - ถ้า `TECHNICAL_ACTION` score > threshold → return `software_it` ทันที
  - ถ้ามีหลาย action: prefer technical; otherwise highest score; if score diff < margin → `none`
  - debug fields/logs: `action_detected`, `action_score`, `subject_detected`, `final_route_reason`

- `semantic.py`
  - เปลี่ยน prompt จาก classify topic → classify intent
  - เพิ่ม 5 rules:
    1. Technical action overrides everything
    2. Classify ACTION not SUBJECT
    3. Content subject alone is not enough
    4. When action unclear, subject is tiebreaker
    5. none is safe

- `state.py`
  - ไม่แก้; inertia logic ยังใช้ได้

- `__init__.py`
  - ไม่แก้ ยกเว้นถ้า signature/debug wiring จำเป็นจริง ๆ

- `plugin.yaml`
  - bump version `1.1.8` → `2.0.0`

- `CHANGELOG.md`
  - เพิ่ม v2.0.0 entry

## Test Matrix

### Technical override → `software_it`
- `แก้พอร์ตในเว็บอ่านนิยาย`
- `เปลี่ยน model ใน config finance`
- `debug api ของระบบ healthcare`
- `fix error ใน legal document parser`
- `รัน server สำหรับเว็บข่าว`
- `เขียน script ดึงข้อมูล finance`

### Creative action + subject
- `เขียนนิยาย fantasy` → `writing_language`
- `แต่งบทความเกี่ยวกับ finance` → `writing_language`
- `draft contract สำหรับ startup` → `legal_government`
- `เขียน report ผลประกอบการ` → `business_finance`

### Analytical action + subject
- `คำนวณ ROI ของ project` → `math` หรือ `business_finance`
- `อธิบาย black hole` → `science`
- `วิเคราะห์ contract clause นี้` → `legal_government`
- `อธิบายอาการ side effect ของยานี้` → `medicine_healthcare`

### None
- `commit และ push ได้เลย` → `none`
- `โอเคครับ` → `none`
- `ขอบคุณ` → `none`

## Verification / Definition of Done

1. `python -m py_compile *.py` ผ่าน
2. `hermes config check` ผ่าน
3. test cases ทั้งหมดผ่าน
4. signature แสดงถูกต้อง
5. `plugin.yaml` version = `2.0.0`
6. `CHANGELOG.md` updated
7. push ขึ้น repo `ShockShoot/hermes-arc`
8. sync กลับ local plugin ที่ `~/.hermes/plugins/topic_detect`
9. ตรวจว่า config.yaml structure, 8 topic names, signature format, fallback behavior ไม่เปลี่ยน
10. ไม่แตะ `install.sh` ถ้าไม่จำเป็น

## Notes

Future action categories should fit the same registry design:
- `TOOL_USE_ACTION`
- `RESEARCH_ACTION`
- `MULTIMODAL_ACTION`
- `AGENTIC_ACTION`

Do not overfit only exact keyword matches. Use keyword scoring as the fast path, but semantic intent prompt should enforce the same action-first logic.
