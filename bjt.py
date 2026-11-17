"""BJT common-emitter DC bias engineering calculations.

Supports three single-supply NPN biasing topologies:
- Voltage Divider Bias (calculate_bias / calculate_divider_bias)
- Fixed Bias (calculate_fixed_bias)
- Emitter-Stabilized Bias (calculate_emitter_bias)

Inputs use kΩ for resistors; the module converts to ohms internally and
returns SI units (amperes and volts). This module must never import Flask.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

VCE_SAT = 0.2

PARSE_MESSAGE = "Please enter a valid number."

VALID_MODES = ("divider", "fixed", "emitter")

MODE_LABELS = {
    "divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias",
}

MODE_REQUIRED_FIELDS = {
    "divider": ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
    "fixed": ("vcc", "rb", "rc", "beta", "vbe"),
    "emitter": ("vcc", "rb", "rc", "re", "beta", "vbe"),
}

MESSAGES = {
    "mode": "Invalid bias circuit mode selected.",
    "vcc": "VCC must be greater than 0 V",
    "rb": "RB must be greater than 0 kΩ",
    "r1": "R1 must be greater than 0 kΩ",
    "r2": "R2 must be greater than 0 kΩ",
    "rc": "RC must be greater than 0 kΩ",
    "re": "RE must be greater than 0 kΩ",
    "beta": "beta must be greater than 0",
    "vbe": "VBE must be between 0 and VCC",
}

CUTOFF_WARNING = (
    "Cutoff: VBB <= VBE (or IB <= 0) — transistor is off (IC ~ 0); "
    "active-region equations do not apply."
)
SATURATION_WARNING = (
    "Saturation: VCE <= 0.2 V — values are approximate; "
    "the linear active-region model does not apply."
)


@dataclass(frozen=True)
class BiasInputs:
    vcc: float
    r1: float = 100.0
    r2: float = 22.0
    rc: float = 2.2
    re: float = 1.0
    beta: float = 100.0
    vbe: float = 0.7
    rb: float = 1000.0
    mode: str = "divider"


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
    mode: str = "divider"

    def to_dict(self) -> dict[str, float | str | bool | None | tuple[str, ...]]:
        """Return standard Lab 03 dictionary representation with explicit units."""
        return {
            "mode": self.mode,
            "vb_v": self.vb,
            "ve_v": self.ve,
            "vc_v": self.vc,
            "vce_v": self.vce,
            "ib_ua": self.ib_a * 1e6,
            "ic_ma": self.ic_a * 1e3,
            "ie_ma": self.ie_a * 1e3,
            "region": self.region,
            "warnings": self.warnings,
        }


def validate_inputs(inputs: BiasInputs) -> dict[str, str]:
    """Return field-name to English-message errors for the selected mode; empty when valid."""
    errors: dict[str, str] = {}

    if inputs.mode not in VALID_MODES:
        errors["mode"] = MESSAGES["mode"]
        return errors

    required = MODE_REQUIRED_FIELDS[inputs.mode]
    field_values = {
        "vcc": inputs.vcc,
        "rb": inputs.rb,
        "r1": inputs.r1,
        "r2": inputs.r2,
        "rc": inputs.rc,
        "re": inputs.re,
        "beta": inputs.beta,
    }

    for name in required:
        if name == "vbe":
            continue
        value = field_values[name]
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
    """Solve the voltage-divider bias point with nodal KCL, independently of Thevenin."""
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


def calculate_fixed_bias(
    vcc: float, rb_kohm: float, rc_kohm: float, beta: float, vbe: float
) -> BiasResult:
    """Solve single-supply Fixed Bias DC operating point (RB from VCC to Base, E grounded)."""
    inputs = BiasInputs(
        vcc=vcc, rb=rb_kohm, rc=rc_kohm, beta=beta, vbe=vbe, mode="fixed"
    )
    errors = validate_inputs(inputs)
    if errors:
        raise ValueError("; ".join(errors.values()))

    rb = rb_kohm * 1000.0
    rc = rc_kohm * 1000.0

    if vcc <= vbe:
        return BiasResult(
            ib_a=0.0,
            ic_a=0.0,
            ie_a=0.0,
            vb=vcc,
            vc=vcc,
            ve=0.0,
            vce=vcc,
            region="cutoff",
            warnings=(CUTOFF_WARNING,),
            cross_check_ok=None,
            cross_check_delta_vce=None,
            mode="fixed",
        )

    ib = (vcc - vbe) / rb
    ic = beta * ib
    ie = (beta + 1.0) * ib

    ve = 0.0
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    region = _classify_region(vcc, vbe, vce)
    warnings = (SATURATION_WARNING,) if region == "saturation" else ()

    check_ic = beta * (vcc - vb) / rb
    check_vce = vcc - check_ic * rc
    delta = check_vce - vce
    cross_check_ok = abs(check_ic - ic) <= 1e-9 and abs(delta) <= 1e-6

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
        mode="fixed",
    )


def calculate_emitter_bias(
    vcc: float, rb_kohm: float, rc_kohm: float, re_kohm: float, beta: float, vbe: float
) -> BiasResult:
    """Solve single-supply Emitter Bias DC operating point (RB from VCC to Base, RE at Emitter)."""
    inputs = BiasInputs(
        vcc=vcc, rb=rb_kohm, rc=rc_kohm, re=re_kohm, beta=beta, vbe=vbe, mode="emitter"
    )
    errors = validate_inputs(inputs)
    if errors:
        raise ValueError("; ".join(errors.values()))

    rb = rb_kohm * 1000.0
    rc = rc_kohm * 1000.0
    re = re_kohm * 1000.0

    if vcc <= vbe:
        return BiasResult(
            ib_a=0.0,
            ic_a=0.0,
            ie_a=0.0,
            vb=vcc,
            vc=vcc,
            ve=0.0,
            vce=vcc,
            region="cutoff",
            warnings=(CUTOFF_WARNING,),
            cross_check_ok=None,
            cross_check_delta_vce=None,
            mode="emitter",
        )

    ib = (vcc - vbe) / (rb + (beta + 1.0) * re)
    ic = beta * ib
    ie = (beta + 1.0) * ib

    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    region = _classify_region(vcc, vbe, vce)
    warnings = (SATURATION_WARNING,) if region == "saturation" else ()

    check_ib = (vcc - vb) / rb
    check_ic = beta * check_ib
    check_ve = (beta + 1.0) * check_ib * re
    check_vce = (vcc - check_ic * rc) - check_ve
    delta = check_vce - vce
    cross_check_ok = abs(check_ic - ic) <= 1e-9 and abs(delta) <= 1e-6

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
        mode="emitter",
    )


def calculate_divider_bias(inputs: BiasInputs) -> BiasResult:
    """Solve the voltage-divider bias point using the Thevenin method."""
    div_inputs = BiasInputs(
        vcc=inputs.vcc,
        r1=inputs.r1,
        r2=inputs.r2,
        rc=inputs.rc,
        re=inputs.re,
        beta=inputs.beta,
        vbe=inputs.vbe,
        mode="divider",
    )
    errors = validate_inputs(div_inputs)
    if errors:
        raise ValueError("; ".join(errors.values()))

    r1 = div_inputs.r1 * 1000.0
    r2 = div_inputs.r2 * 1000.0
    rc = div_inputs.rc * 1000.0
    re = div_inputs.re * 1000.0

    vbb = div_inputs.vcc * r2 / (r1 + r2)
    rb = r1 * r2 / (r1 + r2)

    if vbb <= div_inputs.vbe:
        return BiasResult(
            ib_a=0.0,
            ic_a=0.0,
            ie_a=0.0,
            vb=vbb,
            vc=div_inputs.vcc,
            ve=0.0,
            vce=div_inputs.vcc,
            region="cutoff",
            warnings=(CUTOFF_WARNING,),
            cross_check_ok=None,
            cross_check_delta_vce=None,
            mode="divider",
        )

    ib = (vbb - div_inputs.vbe) / (rb + (div_inputs.beta + 1.0) * re)
    ic = div_inputs.beta * ib
    ie = (div_inputs.beta + 1.0) * ib

    ve = ie * re
    vb = ve + div_inputs.vbe
    vc = div_inputs.vcc - ic * rc
    vce = vc - ve

    region = _classify_region(vbb, div_inputs.vbe, vce)
    warnings = (SATURATION_WARNING,) if region == "saturation" else ()

    nodal_ic, nodal_vce = _nodal_solve(div_inputs)
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
        mode="divider",
    )


def calculate_bias(inputs: BiasInputs) -> BiasResult:
    """Dispatch DC bias calculation according to inputs.mode."""
    if inputs.mode == "divider":
        return calculate_divider_bias(inputs)
    elif inputs.mode == "fixed":
        return calculate_fixed_bias(
            vcc=inputs.vcc,
            rb_kohm=inputs.rb,
            rc_kohm=inputs.rc,
            beta=inputs.beta,
            vbe=inputs.vbe,
        )
    elif inputs.mode == "emitter":
        return calculate_emitter_bias(
            vcc=inputs.vcc,
            rb_kohm=inputs.rb,
            rc_kohm=inputs.rc,
            re_kohm=inputs.re,
            beta=inputs.beta,
            vbe=inputs.vbe,
        )
    else:
        raise ValueError(MESSAGES["mode"])