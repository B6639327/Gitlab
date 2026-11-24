"""External ngspice adapter for BJT Common-Emitter Voltage-Divider Amplifier."""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile

BJT_MODEL_NAME = "Q2N2222"
BJT_MODEL_DEF = (
    ".model Q2N2222 NPN(IS=14.34f XTI=3 EG=1.11 VAF=74.03 BF=255.9 "
    "NE=1.307 ISE=14.34f IKF=.2847 XTB=1.5 BR=6.092 NC=2 ISC=0 IKR=0 RC=1 "
    "CJC=7.306p MJC=.3416 VJC=.75 FC=.5 CJE=22.01p MJE=.377 VJE=.75 "
    "TR=46.91n TF=411.1p ITF=.6 VTF=1.7 XTF=3 RB=10)"
)


def check_ngspice() -> tuple[bool, str]:
    """Check if ngspice executable is reachable in PATH."""
    exe = shutil.which("ngspice")
    if not exe:
        return False, "ngspice executable not found in PATH. Please install ngspice and add it to PATH."
    try:
        res = subprocess.run([exe, "-v"], capture_output=True, text=True, timeout=5)
        out = (res.stdout or res.stderr).strip().splitlines()
        version = out[0] if out else "ngspice (version unknown)"
        return True, version
    except Exception as exc:
        return False, f"Failed to execute ngspice: {exc}"


def build_netlist(params: dict[str, float], analysis_mode: str) -> str:
    """Generate SPICE netlist for the reference CE Voltage Divider circuit.

    Expected input units in `params`:
    - vcc: V
    - r1, r2, rc, re, rl: kΩ
    - cin, cout: µF
    - vin_amp: mV (peak)
    - vin_freq: kHz
    """
    vcc = params["vcc"]
    r1 = params["r1"] * 1e3
    r2 = params["r2"] * 1e3
    rc = params["rc"] * 1e3
    re_ohm = params["re"] * 1e3
    rl = params["rl"] * 1e3
    cin = params["cin"] * 1e-6
    cout = params["cout"] * 1e-6
    vin_amp = params["vin_amp"] * 1e-3
    vin_freq = params["vin_freq"] * 1e3

    for name, val in [
        ("VCC", vcc), ("R1", r1), ("R2", r2), ("RC", rc),
        ("RE", re_ohm), ("RL", rl), ("Cin", cin), ("Cout", cout),
        ("Vin Amplitude", vin_amp), ("Vin Frequency", vin_freq),
    ]:
        if not math.isfinite(val) or val <= 0:
            raise ValueError(f"{name} must be strictly greater than 0 for SPICE simulation.")

    lines = [
        "* ENG29 2121 Lab 04 - Reference CE Voltage-Divider Amplifier",
        f"VCC vcc 0 DC {vcc}",
        f"R1 vcc base {r1}",
        f"R2 base 0 {r2}",
        f"RC vcc coll {rc}",
        f"RE emit 0 {re_ohm}",
        f"Cin in base {cin}",
        f"Cout coll out {cout}",
        f"RL out 0 {rl}",
        f"Q1 coll base emit {BJT_MODEL_NAME}",
        BJT_MODEL_DEF,
    ]

    if analysis_mode == "op":
        lines.extend([
            "Vin in 0 DC 0 AC 1",
            ".op",
            ".control",
            "run",
            "print v(base) v(emit) v(coll) v(coll,emit) i(VCC)",
            "quit",
            ".endc",
        ])
    elif analysis_mode == "ac":
        lines.extend([
            "Vin in 0 DC 0 AC 1",
            ".ac dec 25 10 10Meg",
            ".control",
            "run",
            "wrdata ac_data.txt db(v(out)/v(in)) vp(out)",
            "quit",
            ".endc",
        ])
    elif analysis_mode == "tran":
        period = 1.0 / vin_freq
        t_stop = 4.0 * period
        t_step = period / 100.0
        lines.extend([
            f"Vin in 0 SIN(0 {vin_amp} {vin_freq})",
            f".tran {t_step:.6e} {t_stop:.6e}",
            ".control",
            "run",
            "wrdata tran_data.txt v(in) v(out)",
            "quit",
            ".endc",
        ])
    else:
        raise ValueError(f"Unsupported analysis mode: {analysis_mode}")

    lines.append(".end")
    return "\n".join(lines) + "\n"


def run_simulation(params: dict[str, float], analysis_mode: str = "op") -> dict:
    """Execute ngspice in an isolated temporary directory and parse real outputs."""
    ok, version_or_err = check_ngspice()
    if not ok:
        return {
            "status": "error",
            "engine": "ngspice",
            "error": version_or_err,
        }

    try:
        netlist = build_netlist(params, analysis_mode)
    except ValueError as exc:
        return {
            "status": "error",
            "engine": "ngspice",
            "error": str(exc),
        }

    with tempfile.TemporaryDirectory() as tmpdir:
        cir_path = os.path.join(tmpdir, "circuit.cir")
        log_path = os.path.join(tmpdir, "run.log")

        with open(cir_path, "w", encoding="utf-8") as f:
            f.write(netlist)

        try:
            proc = subprocess.run(
                ["ngspice", "-b", "-o", log_path, cir_path],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "engine": "ngspice",
                "error": "ngspice timed out after 10 seconds.",
                "netlist": netlist,
            }
        except Exception as exc:
            return {
                "status": "error",
                "engine": "ngspice",
                "error": f"Subprocess execution error: {exc}",
                "netlist": netlist,
            }

        log_text = ""
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_text = f.read()

        if proc.returncode != 0:
            return {
                "status": "error",
                "engine": "ngspice",
                "error": f"ngspice exited with non-zero code ({proc.returncode}).",
                "log": log_text,
                "netlist": netlist,
            }

        if analysis_mode == "op":
            return _parse_op(log_text, netlist, version_or_err, params)
        if analysis_mode == "ac":
            return _parse_ac(os.path.join(tmpdir, "ac_data.txt"), log_text, netlist, version_or_err)
        if analysis_mode == "tran":
            return _parse_tran(os.path.join(tmpdir, "tran_data.txt"), log_text, netlist, version_or_err)

    return {"status": "error", "engine": "ngspice", "error": "Unknown simulation error"}


def _parse_op(log_text: str, netlist: str, version: str, params: dict[str, float]) -> dict:
    patterns = {
        "vb": r"v\(base\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)",
        "ve": r"v\(emit\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)",
        "vc": r"v\(coll\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)",
        "vce": r"v\(coll,emit\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)",
        "ivcc": r"i\(vcc\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)",
    }
    parsed: dict[str, float] = {}
    for key, pat in patterns.items():
        m = re.search(pat, log_text, re.IGNORECASE)
        if m:
            parsed[key] = float(m.group(1))

    if "vb" not in parsed or "vce" not in parsed:
        return {
            "status": "error",
            "engine": "ngspice",
            "error": "Could not parse DC operating point voltages from ngspice log.",
            "log": log_text,
            "netlist": netlist,
        }

    rc_ohm = params["rc"] * 1e3
    ic_ma = ((params["vcc"] - parsed["vc"]) / rc_ohm) * 1e3

    return {
        "status": "success",
        "mode": "op",
        "engine": "ngspice",
        "version": version,
        "model": BJT_MODEL_NAME,
        "vb": parsed["vb"],
        "ve": parsed["ve"],
        "vc": parsed["vc"],
        "vce": parsed["vce"],
        "ic_ma": ic_ma,
        "netlist": netlist,
        "log": log_text,
    }


def _parse_ac(data_path: str, log_text: str, netlist: str, version: str) -> dict:
    if not os.path.exists(data_path):
        return {
            "status": "error",
            "engine": "ngspice",
            "error": "AC output file was not generated by ngspice.",
            "log": log_text,
            "netlist": netlist,
        }

    freqs, gain_db, phase_deg = [], [], []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                freqs.append(float(parts[0]))
                gain_db.append(float(parts[1]))
                phase_deg.append(math.degrees(float(parts[3])))

    if not freqs:
        return {
            "status": "error",
            "engine": "ngspice",
            "error": "AC simulation produced empty trace data.",
            "log": log_text,
            "netlist": netlist,
        }

    max_gain = max(gain_db)
    target_3db = max_gain - 3.0
    fl_hz = None
    fh_hz = None
    peak_idx = gain_db.index(max_gain)

    for i in range(peak_idx, 0, -1):
        if gain_db[i] >= target_3db >= gain_db[i - 1]:
            fl_hz = freqs[i]
            break
    for i in range(peak_idx, len(gain_db) - 1):
        if gain_db[i] >= target_3db >= gain_db[i + 1]:
            fh_hz = freqs[i]
            break

    return {
        "status": "success",
        "mode": "ac",
        "engine": "ngspice",
        "version": version,
        "model": BJT_MODEL_NAME,
        "reference": "|V(out) / V(in)| at input source node",
        "freqs": freqs,
        "gain_db": gain_db,
        "phase_deg": phase_deg,
        "midband_gain_db": max_gain,
        "fl_hz": fl_hz,
        "fh_hz": fh_hz,
        "netlist": netlist,
        "log": log_text,
    }


def _parse_tran(data_path: str, log_text: str, netlist: str, version: str) -> dict:
    if not os.path.exists(data_path):
        return {
            "status": "error",
            "engine": "ngspice",
            "error": "Transient output file was not generated by ngspice.",
            "log": log_text,
            "netlist": netlist,
        }

    time_ms, vin_mv, vout_v = [], [], []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                time_ms.append(float(parts[0]) * 1e3)
                vin_mv.append(float(parts[1]) * 1e3)
                vout_v.append(float(parts[3]))

    if not time_ms:
        return {
            "status": "error",
            "engine": "ngspice",
            "error": "Transient simulation produced empty waveform data.",
            "log": log_text,
            "netlist": netlist,
        }

    vin_pp = max(vin_mv) - min(vin_mv)
    vout_pp = max(vout_v) - min(vout_v)

    return {
        "status": "success",
        "mode": "tran",
        "engine": "ngspice",
        "version": version,
        "model": BJT_MODEL_NAME,
        "time_ms": time_ms,
        "vin_mv": vin_mv,
        "vout_v": vout_v,
        "vin_pp_mv": vin_pp,
        "vout_pp_v": vout_pp,
        "netlist": netlist,
        "log": log_text,
    }
