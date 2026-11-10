# BJT Common-Emitter DC Bias Web App (ENG29 2121)

เว็บแอป Flask สำหรับแลปที่ 2 วิชา ENG29 2121 — คำนวณจุดทำงาน DC
(DC operating point) ของวงจร BJT Common-Emitter แบบ voltage-divider bias
ผ่านหน้า dashboard หน้าเดียว

## ฟีเจอร์

- คำนวณ `VB`, `VE`, `VC`, `VCE`, `IB`, `IC`, `IE` พร้อมหน่วย
- ตรวจสอบ input ทุกช่อง พร้อมข้อความ error รายช่อง
- แจ้ง region: Active / Cutoff / Saturation
- ตรวจสอบผลด้วยการคำนวณอิสระ (nodal analysis) และแสดง cross-check
- แสดง schematic วงจรที่อัปเดตตามค่าที่กรอก
- หน้าเว็บแสดงตัวอย่างเริ่มต้นทันทีเมื่อเปิด

## การติดตั้ง

```powershell
python -m pip install -r requirements.txt
```

## การรัน

```powershell
python app.py
```

เปิดเบราว์เซอร์ที่ <http://127.0.0.1:5000>

## การทดสอบ

```powershell
python -m pytest -v
```

## หน่วยของ input / output

| Input | หน่วย |
|---|---|
| `VCC`, `VBE` | V |
| `R1`, `R2`, `RC`, `RE` | kΩ |
| `beta` | ไม่มีหน่วย |

| Output | หน่วย |
|---|---|
| `VB`, `VE`, `VC`, `VCE` | V |
| `IB` | µA |
| `IC`, `IE` | mA |

## สูตรที่ใช้

### Primary: Thevenin equivalent

```
VBB = VCC * R2 / (R1 + R2)
RB  = R1 * R2 / (R1 + R2)
IB  = (VBB - VBE) / (RB + (beta + 1) * RE)
IC  = beta * IB
IE  = (beta + 1) * IB
VE  = IE * RE
VB  = VE + VBE
VC  = VCC - IC * RC
VCE = VC - VE
```

### Independent cross-check: nodal analysis

แก้ระบบสมการ 2×2 ที่โหนด base และ emitter โดยไม่ใช้สูตร Thevenin
แล้วนำ `IC` และ `VCE` มาเทียบกับผลจากวิธีหลัก

```
(VB - VCC)/R1 + VB/R2 + VE/((beta + 1) * RE) = 0
VB - VE = VBE
```

ผลถือว่าผ่านเมื่อ `|ΔIC| <= 1e-9 A` และ `|ΔVCE| <= 1e-6 V`

### Region

- **Cutoff** เมื่อ `VBB <= VBE`
- **Saturation** เมื่อ `VCE <= 0.2 V`
- **Active** เมื่ออยู่นอกสองกรณีข้างต้น

## ข้อจำกัด

แลปนี้ทำเฉพาะ **DC bias** เท่านั้น ไม่มี AC analysis, transient,
circuit editor หรือ FET/MOSFET

## โครงสร้างไฟล์

```
app.py                     Flask routes, form parsing, defaults
bjt.py                     engineering logic (ไม่ import Flask)
templates/index.html       หน้า dashboard หลัก
templates/_schematic.html  inline SVG schematic
static/style.css           CSS ของ dashboard
tests/test_bjt.py          unit tests ของ engineering logic
tests/test_app.py          route/layout tests ของ Flask
requirements.txt           Flask และ pytest
```

## หมายเหตุ

- `electrical.py` และ `test_electrical.py` เป็นงานแลปก่อนหน้า
  และไม่ได้ถูกแก้ไขในงานนี้
- ตัวเลขผลลัพธ์คำนวณจากค่าที่กรอกจริงเสมอ ไม่มีการ hard-code
