# Lab 03 — Browser Acceptance Validation (A1–A5)

พารามิเตอร์ร่วม: `VCC = 12 V`, `RC = 2.2 kΩ`, `β = 100`, `VBE = 0.70 V`
เกณฑ์ความคลาดเคลื่อน: `|ΔIC| <= 0.01 mA`, `|ΔVCE| <= 0.02 V`

- วิธีตรวจที่ใช้จริง: **OpenCode Browser** (in-app browser ของ OpenCode Desktop, Chromium)
- Playwright MCP: **NOT RUN** — ไม่ได้ติดตั้ง MCP server ในเซสชันนี้ จึงใช้ Browser tool ของแอปแทน
- ทุกกรณีส่งฟอร์มจริงบนหน้าเว็บ (`POST /` ปรากฏใน log ของ Flask) แล้วอ่านค่าจากตารางผลของหน้านั้น
- หลักฐาน: `docs/evidence/A1-divider.jpeg`, `docs/evidence/A5-fixed-rb0.jpeg`

| กรณี | เลือกโหมดและกรอกค่า | คาดหมายก่อนรัน (ค่าอ้างอิงอิสระ) | เห็นจริง | วิธีตรวจ | สถานะ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A1 · โหมดเดิม** | Voltage Divider · `R1 = 100 kΩ`, `R2 = 22 kΩ`, `RE = 1 kΩ` | `IC = 1.23 mA` (`1.2279 mA`), `VCE = 8.05 V` (`8.0545 V`) ตรงกับ Lab 2 | `IC = 1.23 mA`, `VCE = 8.05 V` (Independent check: PASS, ΔVCE = 0.000000 V) | OpenCode Browser | PASS |
| **A2 · Fixed** | Fixed Bias · `RB = 1000 kΩ` (`1 MΩ`) | ไม่ต้องกรอก `RE`, `IC = 1.13 mA` (`1.1300 mA`), `VCE = 9.51 V` (`9.5140 V`) | ฟอร์มไม่มีช่อง `RE`; `IC = 1.13 mA`, `VCE = 9.51 V` | OpenCode Browser | PASS |
| **A3 · Emitter** | Emitter Bias · `RB = 1000 kΩ`, `RE = 1 kΩ` | ใช้ค่า `RE`, `IC = 1.03 mA` (`1.0263 mA`), `VCE = 8.71 V` (`8.7055 V`) | มีช่อง `RE` และถูกใช้จริง; `IC = 1.03 mA`, `VCE = 8.71 V` | OpenCode Browser | PASS |
| **A4 · เปลี่ยนค่าเดียว** | Emitter Bias · `RB = 1000 kΩ`, `RE = 2 kΩ` | **ทำนาย:** `IC` ลดลงจาก A3 เพราะ `(β+1)RE` เพิ่มขึ้นทำให้ `IB` ลดลง (`IC = 0.94 mA`, `VCE = 8.03 V`) | เปลี่ยนเฉพาะ `RE` 1 → 2 kΩ; `IC = 0.94 mA` (ลดจาก 1.03), `VCE = 8.03 V` (ลดจาก 8.71) ตรงตามทำนาย | OpenCode Browser | PASS |
| **A5 · อินพุตผิด** | Fixed Bias · `RB = 0` | แสดงข้อความ `RB must be greater than 0 kΩ` เว็บไม่ล่ม และไม่แสดงผลลัพธ์รอบก่อน | ใต้ช่อง `RB` แสดง `RB must be greater than 0 kΩ`; การ์ดผลลัพธ์ขึ้น `Invalid input for Fixed Bias.` ไม่มีตารางผล และหน้าเว็บยังใช้งานได้ | OpenCode Browser | PASS |

## หมายเหตุการตรวจ

- A4 ตรวจโดยคง `VCC`, `RB`, `RC`, `β`, `VBE` เท่า A3 และเปลี่ยนเฉพาะ `RE` แล้วกด **Calculate DC Bias** ใหม่ (ยืนยันว่าค่าที่เห็นเป็นผลของรอบใหม่ ไม่ใช่ผลค้าง)
- A5 ข้อความที่เห็นเป็นข้อความ validation จาก Flask (`validate_inputs`) ไม่ใช่ HTML `required` ของฟอร์ม เพราะฟอร์มใช้ `novalidate`
- ค่าที่แสดงบนหน้าเว็บปัดทศนิยม 2 ตำแหน่ง; ค่าอ้างอิงในวงเล็บเป็นค่าก่อนปัด ใช้ตรวจกับ tolerance ข้างต้น
- ถ้าต้องใช้ Playwright MCP ตามเส้นทางหลักของใบงาน ให้เพิ่ม `mcp.servers.playwright` ใน `opencode.json` แล้วรัน A1–A5 ซ้ำ; วิธี Manual ใช้ตารางเดียวกันนี้ได้
