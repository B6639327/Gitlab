# BJT Common-Emitter DC Bias Web App (ENG29 2121) — Lab 03

เว็บแอป Flask สำหรับแลปที่ 3 วิชา ENG29 2121 — คำนวณจุดทำงาน DC
(DC operating point) ของวงจร BJT NPN Common-Emitter แบบแหล่งจ่ายเดียว
รองรับ **3 วงจรไบอัส** และตรวจผลบนหน้าเว็บจริงเทียบกับค่าอ้างอิง

## ฟีเจอร์

- เลือกวงจรไบอัสได้ 3 แบบ: **Voltage Divider Bias**, **Fixed Bias**, **Emitter Bias**
- ฟอร์มแสดงเฉพาะช่องที่วงจรนั้นต้องใช้ (สลับโหมดแล้วโหลดฟอร์มใหม่)
- คำนวณ `VB`, `VE`, `VC`, `VCE`, `IB`, `IC`, `IE` พร้อมหน่วย
- ตรวจสอบ input ทุกช่อง พร้อมข้อความ error รายช่อง (ฝั่ง Flask ไม่ใช่ HTML `required`)
- แจ้ง region: Active / Cutoff / Saturation พร้อมเตือนเมื่อแบบจำลอง Forward Active ใช้ไม่ได้
- ตรวจสอบผลของ Divider ด้วยการคำนวณอิสระ (nodal analysis) และแสดง cross-check
- แสดง schematic วงจรที่เปลี่ยนตามโหมดและตามค่าที่กรอก

## การติดตั้ง

```powershell
python -m pip install -r requirements.txt
```

## การรัน

```powershell
python -m flask --app app run
```

หรือ

```powershell
python app.py
```

เปิดเบราว์เซอร์ที่ <http://127.0.0.1:5000> (เลือกโหมดตั้งต้นได้ด้วย `?mode=fixed` หรือ `?mode=emitter`)

## การทดสอบ

```powershell
python -m pytest -v
```

ผลปัจจุบัน: **35 passed** (เทสต์เดิมของ Lab 2 ยังผ่านทั้งหมด)

## หน่วยของ input / output

| Input | หน่วย | ใช้ในโหมด |
|---|---|---|
| `VCC`, `VBE` | V | ทั้งหมด |
| `RB` | kΩ | Fixed, Emitter |
| `R1`, `R2` | kΩ | Divider |
| `RC` | kΩ | ทั้งหมด |
| `RE` | kΩ | Divider, Emitter |
| `beta` | ไม่มีหน่วย | ทั้งหมด |

| Output | หน่วย |
|---|---|
| `VB`, `VE`, `VC`, `VCE` | V |
| `IB` | µA |
| `IC`, `IE` | mA |

## สูตรที่ใช้ (แบบจำลอง DC, β และ VBE คงที่ในย่าน Forward Active)

กระแสฐาน `IB` ตามวงจร:

```
Fixed    IB = (VCC - VBE) / RB
Emitter  IB = (VCC - VBE) / (RB + (beta + 1) * RE)
Divider  IB = (VTH - VBE) / (RTH + (beta + 1) * RE)
         VTH = VCC * R2 / (R1 + R2),  RTH = R1 * R2 / (R1 + R2)
```

ค่าที่เหลือเหมือนกันทุกโหมด:

```
IC  = beta * IB
IE  = (beta + 1) * IB
VE  = IE * RE          (Fixed: VE = 0 V)
VB  = VE + VBE
VC  = VCC - IC * RC
VCE = VC - VE
```

### Independent cross-check (Divider)

แก้ระบบสมการ 2×2 ที่โหนด base และ emitter โดยไม่ใช้สูตร Thevenin
แล้วนำ `IC` และ `VCE` มาเทียบกับผลจากวิธีหลัก
ผ่านเมื่อ `|ΔIC| <= 1e-9 A` และ `|ΔVCE| <= 1e-6 V`

### Region

- **Cutoff** เมื่อ `VBB <= VBE` (หรือ `IB <= 0`)
- **Saturation** เมื่อ `VCE <= 0.2 V`
- **Active** เมื่ออยู่นอกสองกรณีข้างต้น

## ผลตรวจรับรอง (A1–A5)

ตารางผลจริงพร้อมค่าอ้างอิงอิสระ วิธีตรวจ และหลักฐาน: [`docs/validation.md`](docs/validation.md)

- วิธีตรวจที่ใช้: **OpenCode Browser** (Playwright MCP = NOT RUN เพราะยังไม่ได้ตั้ง MCP server)
- หลักฐานภาพหน้าจอ: `docs/evidence/A1-divider.jpeg`, `docs/evidence/A5-fixed-rb0.jpeg`

## โครงสร้างไฟล์

```
app.py                     Flask routes, ตรวจ input ตามโหมด, เลือกฟังก์ชัน
bjt.py                     engineering logic ทั้ง 3 วงจร (ไม่ import Flask)
templates/index.html       หน้า dashboard + dropdown เลือกโหมด
templates/_schematic.html  inline SVG schematic ที่เปลี่ยนตามโหมด
static/style.css           CSS ของ dashboard
tests/test_bjt.py          unit tests ของ engineering logic
tests/test_app.py          route/layout tests ของ Flask
docs/validation.md         ตารางตรวจรับรอง A1–A5
docs/evidence/             ภาพหน้าจอหลักฐาน
requirements.txt           Flask และ pytest
```

## ส่วนที่ AI ช่วย และส่วนที่นักศึกษาตรวจ

- AI (Gemini) ร่างโครงฟังก์ชัน `calculate_fixed_bias` / `calculate_emitter_bias`,
  การเลือกฟังก์ชันตามโหมด, ฟอร์มเลือกโหมด และ schematic ตามโหมด
- นักศึกษาตรวจสมการกับใบงาน/Engineering Electronics, ตรวจหน่วย (kΩ → Ω ที่จุดรับข้อมูลครั้งเดียว),
  ตรรกะการตรวจ input แยกจาก "แบบจำลองใช้ไม่ได้", และทวนผล A1–A5 บนเบราว์เซอร์ด้วยตนเอง
- AI ช่วยแก้บั๊กที่พบระหว่างตรวจ: ปุ่มสลับโหมดส่ง `action` ซ้ำจน Flask อ่านผิด,
  `onchange` อ้าง `form.action` ผิด, แท็ก HTML เสียในหัวเว็บ, และ schematic ที่โชว์ค่า default ขณะอินพุตผิด

## ข้อจำกัด

งานนี้ทำเฉพาะ **DC bias** เท่านั้น ไม่มี SPICE, DC load line, AC/transient,
capacitor bypass หรือ FET/MOSFET

- `electrical.py` และ `test_electrical.py` เป็นงานแลปก่อนหน้า และไม่ได้ถูกแก้ไขในงานนี้
- ตัวเลขผลลัพธ์คำนวณจากค่าที่กรอกจริงเสมอ ไม่มีการ hard-code
