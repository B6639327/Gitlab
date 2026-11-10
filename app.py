"""Flask dashboard for the BJT common-emitter DC bias calculator."""

from __future__ import annotations

import math
from collections.abc import Mapping

from flask import Flask, render_template, request

from bjt import BiasInputs, calculate_bias, validate_inputs

app = Flask(__name__)

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

DEFAULTS = {
    "vcc": "12.0",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.70",
}

LABELS = {
    "vcc": "VCC (Supply Voltage)",
    "r1": "R1 (Upper Divider)",
    "r2": "R2 (Lower Divider)",
    "rc": "RC (Collector Resistor)",
    "re": "RE (Emitter Resistor)",
    "beta": "β (Current Gain)",
    "vbe": "VBE (Base-Emitter Voltage)",
}

UNITS = {
    "vcc": "V",
    "r1": "kΩ",
    "r2": "kΩ",
    "rc": "kΩ",
    "re": "kΩ",
    "beta": "–",
    "vbe": "V",
}

PARSE_MESSAGE = "Please enter a valid number."


def parse_form(
    form: Mapping[str, str],
) -> tuple[BiasInputs | None, dict[str, str], dict[str, str]]:
    """Parse and validate one submitted form.

    Returns (inputs_or_none, errors_by_field, raw_values_by_field).
    """
    raw_values: dict[str, str] = {}
    parsed: dict[str, float] = {}
    errors: dict[str, str] = {}

    for field in FIELDS:
        value = form.get(field, "").strip()
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
        return None, errors, raw_values

    inputs = BiasInputs(**parsed)
    errors = validate_inputs(inputs)
    if errors:
        return None, errors, raw_values

    return inputs, {}, raw_values


def _default_inputs() -> BiasInputs:
    return BiasInputs(**{field: float(value) for field, value in DEFAULTS.items()})


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        inputs, errors, values = parse_form(request.form)
    else:
        inputs = _default_inputs()
        errors = {}
        values = dict(DEFAULTS)

    result = calculate_bias(inputs) if inputs is not None else None
    circuit = values if inputs is not None else dict(DEFAULTS)

    return render_template(
        "index.html",
        fields=FIELDS,
        labels=LABELS,
        units=UNITS,
        values=values,
        errors=errors,
        result=result,
        circuit=circuit,
    )


if __name__ == "__main__":
    app.run(debug=True)
