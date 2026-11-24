"""Flask dashboard for the BJT common-emitter DC bias & SPICE amplifier simulator."""

from __future__ import annotations

import math
from collections.abc import Mapping

from flask import Flask, render_template, request

from bjt import BiasInputs, calculate_bias, validate_inputs
from spice_engine import run_simulation

app = Flask(__name__)

DC_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
SPICE_EXTRA_FIELDS = ("rl", "cin", "cout", "vin_amp", "vin_freq")
ALL_FIELDS = DC_FIELDS + SPICE_EXTRA_FIELDS

DEFAULTS = {
    "vcc": "12.0",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.70",
    "rl": "10.0",
    "cin": "10.0",
    "cout": "10.0",
    "vin_amp": "10.0",
    "vin_freq": "1.0",
}

LABELS = {
    "vcc": "VCC (Supply Voltage)",
    "r1": "R1 / RB (Upper / Base Resistor)",
    "r2": "R2 (Lower Divider)",
    "rc": "RC (Collector Resistor)",
    "re": "RE (Emitter Resistor)",
    "beta": "β (Current Gain - Analytical)",
    "vbe": "VBE (Base-Emitter - Analytical)",
    "rl": "RL (Load Resistor)",
    "cin": "Cin (Input Coupling Cap)",
    "cout": "Cout (Output Coupling Cap)",
    "vin_amp": "Vin Amplitude (Peak)",
    "vin_freq": "Vin Frequency",
}

UNITS = {
    "vcc": "V",
    "r1": "kΩ",
    "r2": "kΩ",
    "rc": "kΩ",
    "re": "kΩ",
    "beta": "–",
    "vbe": "V",
    "rl": "kΩ",
    "cin": "µF",
    "cout": "µF",
    "vin_amp": "mV",
    "vin_freq": "kHz",
}

PARSE_MESSAGE = "Please enter a valid number."


def parse_form(
    form: Mapping[str, str],
    bias_mode: str = "voltage_divider",
) -> tuple[BiasInputs | None, dict[str, float] | None, dict[str, str], dict[str, str]]:
    """Parse and validate submitted form values."""
    raw_values: dict[str, str] = {}
    parsed: dict[str, float] = {}
    errors: dict[str, str] = {}

    for field in ALL_FIELDS:
        default_fallback = DEFAULTS[field] if field in SPICE_EXTRA_FIELDS else ""
        value = form.get(field, default_fallback).strip()
        raw_values[field] = value
        try:
            number = float(value)
        except ValueError:
            errors[field] = PARSE_MESSAGE
            continue
        if not math.isfinite(number):
            errors[field] = PARSE_MESSAGE
            continue
        parsed[field] = number

    if errors:
        return None, None, errors, raw_values

    dc_inputs = BiasInputs(**{f: parsed[f] for f in DC_FIELDS})
    errors = validate_inputs(dc_inputs, bias_mode=bias_mode)

    for extra in SPICE_EXTRA_FIELDS:
        if parsed[extra] <= 0:
            errors[extra] = f"{LABELS[extra]} must be greater than 0"

    if errors:
        return None, None, errors, raw_values

    return dc_inputs, parsed, {}, raw_values


def _default_inputs() -> tuple[BiasInputs, dict[str, float]]:
    parsed = {field: float(value) for field, value in DEFAULTS.items()}
    dc_inputs = BiasInputs(**{f: parsed[f] for f in DC_FIELDS})
    return dc_inputs, parsed


@app.route("/", methods=["GET", "POST"])
def index():
    bias_mode = request.form.get("bias_mode", "voltage_divider")
    analysis_mode = request.form.get("analysis_mode", "op")

    if request.method == "POST":
        dc_inputs, all_parsed, errors, values = parse_form(request.form, bias_mode=bias_mode)
    else:
        dc_inputs, all_parsed = _default_inputs()
        errors = {}
        values = dict(DEFAULTS)

    result = calculate_bias(dc_inputs, bias_mode=bias_mode) if dc_inputs is not None else None
    circuit = values if dc_inputs is not None else dict(DEFAULTS)

    spice_result = None
    if bias_mode == "voltage_divider":
        if all_parsed is not None:
            spice_result = run_simulation(all_parsed, analysis_mode=analysis_mode)
        else:
            spice_result = {
                "status": "error",
                "engine": "ngspice",
                "error": "Fix invalid input parameters before running ngspice simulation.",
            }

    return render_template(
        "index.html",
        dc_fields=DC_FIELDS,
        spice_fields=SPICE_EXTRA_FIELDS,
        labels=LABELS,
        units=UNITS,
        values=values,
        errors=errors,
        result=result,
        spice_result=spice_result,
        bias_mode=bias_mode,
        analysis_mode=analysis_mode,
        circuit=circuit,
    )


if __name__ == "__main__":
    app.run(debug=True)
