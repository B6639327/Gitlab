# Lab 04: BJT Common-Emitter Amplifier Simulator v1 (ENG29 2121)

เว็บแอป Flask ต่อยอดจาก Lab 3 สำหรับวิชา **ENG29 2121 Computer Programming for Electrical Engineers**
รองรับการคำนวณจุดทำงาน DC แบบ Analytical ทั้ง 3 รูปแบบ (Voltage Divider, Fixed, Emitter Bias)
ร่วมกับการจำลองวงจร **Common-Emitter Voltage-Divider Amplifier** ผ่านโปรแกรมภายนอก **`ngspice`** ในโหมด `.op` (DC), `.ac` (Bode) และ `.tran` (Transient)

## ความสามารถหลัก

- **Preserved Lab 3 Analytical Engine (`bjt.py`):** คำนวณ `VB`, `VE`, `VC`, `VCE`, `IB`, `IC`, `IE` พร้อมตรวจสอบ Active / Cutoff / Saturation และ Nodal Cross-Check
- **Real SPICE Integration (`spice_engine.py`):** สร้าง SPICE Netlist แบบไดนามิก เรียก `ngspice` แบบ Batch (`-b`) ผ่าน `subprocess.run` (กำหนด `timeout`, ไม่ใช้ `shell=True`) และดึงค่าจริงมาแสดงผล
- **Interactive Plots:** แสดงกราฟ Bode Response (Gain dB & Phase deg) และ Transient Waveforms (`Vin`, `Vout` เทียบเวลา ms) พร้อมป้ายกำกับที่มา (`ngspice`) และหน่วยชัดเจน
- **Safe Error Handling:** ตรวจสอบพารามิเตอร์อินพุตและสถานะการรัน `ngspice` แจ้งเตือนชัดเจนโดยไม่แสดงกราฟค้างหรือผลสำเร็จปลอม

## ข้อกำหนดระบบและการติดตั้ง

1. ติดตั้ง **Python 3.10+** และ Python Dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
2. ติดตั้งโปรแกรมภายนอก **ngspice** (ดาวน์โหลดได้จาก [ngspice Downloads](https://ngspice.sourceforge.io/download.html)) และเพิ่มโฟลเดอร์ `bin` ลงใน System `PATH` จากนั้นทดสอบใน Terminal:
   ```powershell
   ngspice -v
   ```

## การรันแอปพลิเคชัน

```powershell
python -m flask --app app run
```
เปิดเบราว์เซอร์ไปที่ <http://127.0.0.1:5000/>

## การรัน Unit Tests

```powershell
python -m pytest -v
```

## โครงสร้างไฟล์

```
app.py                     Flask routes, form validation, Analytical & SPICE dispatch
bjt.py                     Analytical DC bias module (Voltage Divider, Fixed, Emitter)
spice_engine.py            ngspice netlist generator, batch runner, and output parser
templates/index.html       Dashboard UI + Chart.js Bode/Transient plots
templates/_schematic.html  SVG schematic of CE Voltage-Divider amplifier
static/style.css           Dashboard styling
tests/                     Unit tests (test_bjt.py, test_app.py, test_spice.py)
docs/validation.md         Browser acceptance test log (B1–B8) & environment evidence
```
