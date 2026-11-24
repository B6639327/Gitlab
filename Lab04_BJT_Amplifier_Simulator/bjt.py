"""BJT common-emitter DC bias engineering calculations.

Inputs use kΩ for resistors; the module converts to ohms internally and
returns SI units (amperes and volts). This module must never import Flask.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

VCE_SAT = 0.2

PARSE_MESSAGE = "Please enter a valid number."

MESSAGES = {
    "vcc": "VCC must be greater than 0 V",
    "r1": "R1 must be greater than 0 kΩ",
    "r2": "R2 must be greater than 0 kΩ",
    "rc": "RC must be greater than 0 kΩ",
    "re": "RE must be greater than 0 kΩ",
    "beta": "beta must be greater than 0",
    "vbe": "VBE must be between 0 and VCC",
}

CUTOFF_WARNING = (
    "Cutoff: VBB <= VBE — transistor is off (IC ~ 0); "
    "active-region equations do not apply."
)
SATURATION_WARNING = (
    "Saturation: VCE <= 0.2 V — values are approximate; "
    "the linear active-region model does not apply."
)


@dataclass(frozen=True)
class BiasInputs:
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


@dataclass(frozen=True)
class BiasResult:
    ib_a: float
    ic_a: float
    ie_a: float
    vb: float
    vc: float
    ve: float
    vce: float
    region: str
    warnings: tuple[str, ...]
    cross_check_ok: bool | None
    cross_check_delta_vce: float | None


def validate_inputs(inputs: BiasInputs, bias_mode: str = "voltage_divider") -> dict[str, str]:
    """Return field-name to English-message errors; empty when valid."""
    errors: dict[str, str] = {}

    positive_rules = [
        ("vcc", inputs.vcc),
        ("r1", inputs.r1),
        ("rc", inputs.rc),
        ("beta", inputs.beta),
    ]
    if bias_mode == "voltage_divider":
        positive_rules.append(("r2", inputs.r2))
    if bias_mode in ("voltage_divider", "emitter"):
        positive_rules.append(("re", inputs.re))

    for name, value in positive_rules:
        if not math.isfinite(value):
            errors[name] = PARSE_MESSAGE
        elif value <= 0:
            errors[name] = MESSAGES[name]

    if not math.isfinite(inputs.vbe):
        errors["vbe"] = PARSE_MESSAGE
    elif not math.isfinite(inputs.vcc) or inputs.vcc <= 0:
        if inputs.vbe <= 0:
            errors["vbe"] = MESSAGES["vbe"]
    elif not 0 < inputs.vbe < inputs.vcc:
        errors["vbe"] = MESSAGES["vbe"]

    return errors


def _classify_region(vbb: float, vbe: float, vce: float) -> str:
    if vbb <= vbe:
        return "cutoff"
    if vce <= VCE_SAT:
        return "saturation"
    return "active"


def _nodal_solve(inputs: BiasInputs) -> tuple[float, float]:
    """Solve the bias point with nodal KCL, independently of Thevenin."""
    r1 = inputs.r1 * 1000.0
    r2 = inputs.r2 * 1000.0
    rc = inputs.rc * 1000.0
    re = inputs.re * 1000.0

    a00 = 1.0 / r1 + 1.0 / r2
    a01 = 1.0 / ((inputs.beta + 1.0) * re)
    a10 = 1.0
    a11 = -1.0
    b0 = inputs.vcc / r1
    b1 = inputs.vbe

    det = a00 * a11 - a01 * a10
    vb = (b0 * a11 - a01 * b1) / det
    ve = (a00 * b1 - b0 * a10) / det

    ie = ve / re
    ib = ie / (inputs.beta + 1.0)
    ic = inputs.beta * ib
    vc = inputs.vcc - ic * rc
    vce = vc - ve
    return ic, vce


def calculate_bias(inputs: BiasInputs, bias_mode: str = "voltage_divider") -> BiasResult:
    """Solve the DC bias point for voltage_divider, fixed, or emitter bias."""
    errors = validate_inputs(inputs, bias_mode=bias_mode)
    if errors:
        raise ValueError("; ".join(errors.values()))

    r1 = inputs.r1 * 1000.0  # RB in fixed / emitter modes
    r2 = inputs.r2 * 1000.0
    rc = inputs.rc * 1000.0
    re = inputs.re * 1000.0

    if bias_mode == "fixed":
        vbb = inputs.vcc
        if vbb <= inputs.vbe:
            return BiasResult(
                ib_a=0.0, ic_a=0.0, ie_a=0.0,
                vb=vbb, vc=inputs.vcc, ve=0.0, vce=inputs.vcc,
                region="cutoff", warnings=(CUTOFF_WARNING,),
                cross_check_ok=None, cross_check_delta_vce=None,
            )
        ib = (inputs.vcc - inputs.vbe) / r1
        ic = inputs.beta * ib
        ie = (inputs.beta + 1.0) * ib
        ve = 0.0
        vb = inputs.vbe
        vc = inputs.vcc - ic * rc
        vce = vc - ve
        region = _classify_region(vbb, inputs.vbe, vce)
        warnings = (SATURATION_WARNING,) if region == "saturation" else ()
        return BiasResult(
            ib_a=ib, ic_a=ic, ie_a=ie,
            vb=vb, vc=vc, ve=ve, vce=vce,
            region=region, warnings=warnings,
            cross_check_ok=True, cross_check_delta_vce=0.0,
        )

    if bias_mode == "emitter":
        vbb = inputs.vcc
        if vbb <= inputs.vbe:
            return BiasResult(
                ib_a=0.0, ic_a=0.0, ie_a=0.0,
                vb=vbb, vc=inputs.vcc, ve=0.0, vce=inputs.vcc,
                region="cutoff", warnings=(CUTOFF_WARNING,),
                cross_check_ok=None, cross_check_delta_vce=None,
            )
        ib = (inputs.vcc - inputs.vbe) / (r1 + (inputs.beta + 1.0) * re)
        ic = inputs.beta * ib
        ie = (inputs.beta + 1.0) * ib
        ve = ie * re
        vb = ve + inputs.vbe
        vc = inputs.vcc - ic * rc
        vce = vc - ve
        region = _classify_region(vbb, inputs.vbe, vce)
        warnings = (SATURATION_WARNING,) if region == "saturation" else ()
        return BiasResult(
            ib_a=ib, ic_a=ic, ie_a=ie,
            vb=vb, vc=vc, ve=ve, vce=vce,
            region=region, warnings=warnings,
            cross_check_ok=True, cross_check_delta_vce=0.0,
        )

    # Voltage-divider bias (default)
    vbb = inputs.vcc * r2 / (r1 + r2)
    rb = r1 * r2 / (r1 + r2)

    if vbb <= inputs.vbe:
        return BiasResult(
            ib_a=0.0,
            ic_a=0.0,
            ie_a=0.0,
            vb=vbb,
            vc=inputs.vcc,
            ve=0.0,
            vce=inputs.vcc,
            region="cutoff",
            warnings=(CUTOFF_WARNING,),
            cross_check_ok=None,
            cross_check_delta_vce=None,
        )

    ib = (vbb - inputs.vbe) / (rb + (inputs.beta + 1.0) * re)
    ic = inputs.beta * ib
    ie = (inputs.beta + 1.0) * ib

    ve = ie * re
    vb = ve + inputs.vbe
    vc = inputs.vcc - ic * rc
    vce = vc - ve

    region = _classify_region(vbb, inputs.vbe, vce)
    warnings = (SATURATION_WARNING,) if region == "saturation" else ()

    nodal_ic, nodal_vce = _nodal_solve(inputs)
    delta = nodal_vce - vce
    cross_check_ok = abs(nodal_ic - ic) <= 1e-9 and abs(delta) <= 1e-6

    return BiasResult(
        ib_a=ib,
        ic_a=ic,
        ie_a=ie,
        vb=vb,
        vc=vc,
        ve=ve,
        vce=vce,
        region=region,
        warnings=warnings,
        cross_check_ok=cross_check_ok,
        cross_check_delta_vce=delta,
    )
