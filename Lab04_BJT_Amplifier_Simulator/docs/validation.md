# Lab 04 Browser Acceptance & Validation Log

- **Environment:** Windows PC / Python Flask
- **SPICE Engine:** ngspice (กรอกเวอร์ชันจริงที่ได้จาก `ngspice -v` เช่น `ngspice-42`)
- **BJT Model Used:** `Q2N2222` (`IS=14.34f BF=255.9 VAF=74.03 IKF=0.2847 BR=6.092`)
- **Verification Method:** Playwright MCP + Real Local Flask Server (`http://127.0.0.1:5000/`)

## Browser Acceptance Test Cases (B1–B8)

| Case | Method | Input | Expected / Reference | Observed | Evidence | Status |
|---|---|---|---|---|---|---|
| **B1 · Regression** | Playwright MCP / Browser | Default Lab 3 values (`VCC=12V, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.7V`) + switch Fixed/Emitter/Divider | `IC = 1.23 mA`, `VCE = 8.05 V`, Active region OK, Independent check PASS; switches modes cleanly | *(บันทึกค่าที่อ่านได้จริง)* | `docs/captures/b1_regression.png` | PASS / NOT RUN |
| **B2 · DC SPICE** | Playwright MCP / Browser | Voltage Divider CE, Mode = `DC (.op)`, Default parameters | Displays `VB, VE, VC, VCE, IC` parsed from `ngspice` log with badge `Engine: ngspice · PASS (Q2N2222)` | *(บันทึกค่า VB, VE, VC, VCE จาก ngspice)* | `docs/captures/b2_dc_spice.png` | PASS / NOT RUN |
| **B3 · Change RE** | Playwright MCP / Browser | Change `RE` from `1.0 kΩ` to `2.0 kΩ`, Run `.op` / `.ac` | Operating point (`VE` increases, `IC` decreases) and gain update dynamically | *(บันทึกค่าก่อน/หลังเปลี่ยน RE)* | `docs/captures/b3_change_re.png` | PASS / NOT RUN |
| **B4 · AC Bode** | Playwright MCP / Browser | Voltage Divider CE, Mode = `AC (.ac)`, Default parameters | Bode magnitude (dB) and phase (deg) charts plotted against Frequency (Hz) from real `ngspice` output | *(บันทึกค่า Midband Gain dB, fL, fH)* | `docs/captures/b4_ac_bode.png` | PASS / NOT RUN |
| **B5 · Transient** | Playwright MCP / Browser | Voltage Divider CE, Mode = `Transient (.tran)`, `Vin = 10 mV`, `1 kHz` | `Vin (mV)` and `Vout (V)` vs `Time (ms)` plotted; `Vout` inverted (~180° phase shift) relative to `Vin` | *(บันทึกค่า Vin_pp, Vout_pp และการกลับเฟส)* | `docs/captures/b5_transient.png` | PASS / NOT RUN |
| **B6 · Change Source** | Playwright MCP / Browser | Change `Vin Amplitude` to `20 mV` or `Frequency` to `2 kHz`, Run `.tran` | Waveform amplitude and/or period updates immediately to match new input | *(บันทึกค่าก่อน/หลังเปลี่ยน Source)* | `docs/captures/b6_change_source.png` | PASS / NOT RUN |
| **B7 · Invalid / Fail** | Playwright MCP / Browser | Set `RE = 0` (or test missing `ngspice`) and submit | Displays clear validation/engine error message; does NOT show stale success charts | *(บันทึกข้อความ Error ที่ปรากฏจริง)* | `docs/captures/b7_error.png` | PASS / NOT RUN |
| **B8 · UI Responsive** | Playwright MCP + Impeccable | Inspect Desktop (`1280px`) and Mobile (`390px`) viewports | Readable labels, units, schematic, charts, and buttons without horizontal clipping | *(บันทึกผลตรวจ Desktop & Mobile)* | `docs/captures/b8_desktop.png`, `docs/captures/b8_mobile.png` | PASS / NOT RUN |

## Notes on Model Assumptions & Limitations

1. **Analytical vs. SPICE Difference:** โมเดล Analytical ใน `bjt.py` ใช้ค่าคงที่ $\beta = 100$ และ $V_{BE} = 0.70\text{ V}$ ขณะที่ `ngspice` ใช้พารามิเตอร์ Gummel-Poon ของรุ่น `Q2N2222` ($BF = 255.9$) ทำให้ค่า $I_B$ และ $V_{CE}$ แตกต่างกันเล็กน้อยตามหลักฟิสิกส์ของอุปกรณ์จริง
2. **AI & Student Role Summary:**
   - **AI Assistance:** ช่วยวางโครงสร้าง `spice_engine.py`, เชื่อม Flask route, สร้างกราฟ Chart.js และปรับปรุง UI ด้วย Impeccable Skill
   - **Student Verification:** นักศึกษาตรวจสอบความถูกต้องของ SPICE Netlist, หน่วยทางวิศวกรรม, ผลลัพธ์ `.op`/`.ac`/`.tran` เทียบกับทฤษฎี และรันทดสอบ B1–B8 บนเบราว์เซอร์จริง
