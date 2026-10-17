---
title: life-radar — Product Card
doc_id: CARD-life-radar
doc_type: product-card
verdict: build
version: 0.1
date: 2026-10-17
status: ร่างเพื่อพิจารณา
owner: Product owner (Book Dev)
---

# life-radar — Product Card

## 1. สรุปคุณค่าในหนึ่งประโยค

เรดาร์โอกาสชีวิตส่วนตัว: รู้ล่วงหน้าว่าโอกาสอะไรจะปิดถาวรเพราะอายุ อะไรต้องเริ่มเตรียมตัวตั้งแต่วันนี้ อะไรเปิดรับอยู่ และอะไรรอได้ — จากวันเกิด สัญชาติ และการศึกษาของเรา

## 2. ปัญหาและผู้ใช้เป้าหมาย

- ปัญหา: โอกาสสำคัญหลายอย่าง (Working Holiday, ทุนที่จำกัดอายุ, โครงการ young professional, cadet pilot, การแข่งขันเฉพาะนักศึกษา, สิทธิรัฐตามช่วงอายุ) พลาดเพราะไม่รู้ว่ามีอยู่ หรือรู้ตอนประตูปิดแล้ว และหลายอย่างต้องเตรียมตัว (IELTS, ประสบการณ์ทำงาน, เอกสาร) นานกว่าช่วงรับสมัคร
- ผู้ใช้: เจ้าของ (คนไทย, solopreneur) เป็นผู้ใช้แรก; ออกแบบให้ต่อยอดเป็นผลิตภัณฑ์สาธารณะสำหรับคนไทยและสัญชาติอื่นได้ภายหลัง

## 3. สิ่งที่ทำได้จริงตอนนี้

- Schema เดียวสำหรับโอกาสทุกประเภท: คุณสมบัติ (อายุต่ำสุด/สูงสุด + วิธีนับอายุ, สัญชาติ, เพศ, การศึกษา, ต้องเป็นนักศึกษาหรือไม่), ช่วงเวลา (rolling / annual / one_off / cohort, วันที่หรือเดือนที่เปิดตามปกติ, โควตา, จำนวนครั้งที่สมัครได้), เวลาเตรียมตัว + prerequisites, ระดับความเร่งด่วน (time_critical / preparation_critical / evergreen) และแหล่งที่มา (source_url, last_verified_at, verification_status)
- `profile` + `opportunity-status` (interested / preparing / applied / accepted / rejected / missed / not_eligible / dismissed) แยกตาม workspace รองรับหลายผู้ใช้ภายหลัง
- Radar: `GET /v1/profiles/{id}/radar` และ `POST /v1/radar` จัดทุกโอกาสลง bucket เดียว — `prepare_now`, `closing_by_age`, `open_now`, `evergreen`, `watch`, `opens_later`, `missed`, `not_eligible` — พร้อมวันที่ปิดตามอายุ, โอกาสสุดท้าย, จำนวนรอบที่เหลือ และวันที่ต้องเริ่มเตรียมตัว
- Seed catalog v1 (`seeds/opportunities.v1.yaml`) พร้อม loader `radar-seed` (check / db / api, upsert ตาม slug)

## 4. หลักฐานสถานะ

| รายการ | ค่า (ตรวจจาก repository) |
|---|---|
| Stack | FastAPI, Python, PostgreSQL (cell kit) |
| Tests | 53 ผ่าน, 7 ข้าม (ของ kit: ไม่มี graph/ref) — contract tests ของ kit + rules + radar API + seed loader (`.venv/bin/pytest -q`, 2026-10-17) |
| Seed v1 | 57 แถว: verified 24, partially_verified 30, unverified 3 (`seeds/README.md`) |
| CI | ไม่มี |
| Deploy | Dockerfile + `.railway/railway.ts` — ยังไม่ได้ provision Neon / deploy Railway (รอเจ้าของอนุมัติ) |
| GitHub remote | ยังไม่มี (git local เท่านั้น) |
| Live URL | ไม่มี |

## 5. คุณค่าและจุดต่าง

- ไม่ใช่แค่รายการทุน: คำนวณตามตัวบุคคลว่า "ประตูไหนจะปิดเมื่อไร" และ "ต้องเริ่มเตรียมตั้งแต่เมื่อไร"
- ทุกแถวมีแหล่งอ้างอิงทางการและสถานะการตรวจสอบ; สิ่งที่ยืนยันไม่ได้จะแสดงเป็น caveat ไม่ซ่อน
- โครงสร้าง cell เดียวกับ life cells อื่น (API + Neon ของตัวเอง, ใช้ empire-platform สำหรับ auth/audit)
- มุมรายได้: ผลิตภัณฑ์สาธารณะ (เว็บ / LINE bot / newsletter "โอกาสที่จะปิดสำหรับคุณปีนี้") **[สมมติฐาน]**

## 6. ช่องว่างสำคัญ

- Seed เป็นชุดเริ่มต้น ไม่ครอบคลุมทั้งหมด และบางแถวยืนยันได้บางส่วน (ดู `seeds/README.md`)
- ยังไม่มีการแจ้งเตือน, UI, calendar export หรือรอบตรวจสอบข้อมูลซ้ำอัตโนมัติ
- ยังไม่มี CI

## 7. คำตัดสิน

**`build`** — แกนหลัก (schema, radar, seed) ทำงานและทดสอบแล้วในเครื่อง ขั้นถัดไปคือให้เจ้าของอนุมัติการขึ้นระบบจริงและใช้งานเองก่อน

## 8. ขั้นต่อไป

1. เจ้าของอนุมัติ: สร้าง GitHub repo, `radar-db provision` (Neon), deploy Railway, ลงทะเบียน `radar` ใน registry
2. โหลด seed ผ่าน API และสร้าง profile ของเจ้าของ
3. ตรวจสอบแถวที่ `partially_verified` / `unverified` ซ้ำ และเพิ่มหมวดที่ยังบาง
4. เพิ่ม digest รายสัปดาห์ / calendar export

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| Product owner (Book Dev) | รอพิจารณา | — | ________ |

## แหล่งข้อมูล

- `README.md`, `PRODUCT.md`
- `cell.yaml`, `migrations/0001_radar.sql`
- `src/life_radar/rules.py`, `tests/`
- `seeds/opportunities.v1.yaml`, `seeds/README.md`
