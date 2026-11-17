"""Flask dashboard for the BJT common-emitter DC bias calculator (Lab 03)."""

from __future__ import annotations

import math
from collections.abc import Mapping

from flask import Flask, render_template, request

from bjt import (
    MESSAGES,
    MODE_LABELS,
    MODE_REQUIRED_FIELDS,
    VALID_MODES,
    BiasInputs,
    calculate_divider_bias,
    calculate_emitter_bias,
    calculate_fixed_bias,
    validate_inputs,
)

app = Flask(__name__)

ALL_FIELDS = ("vcc", "rb", "r1", "r2", "rc", "re", "beta", "vbe")

DEFAULTS = {
    "mode": "divider",
    "vcc": "12.0",
    "rb": "1000",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.70",
}

LABELS = {
    "vcc": "VCC (Supply Voltage)",
    "rb": "RB (Base Resistor)",
    "r1": "R1 (Upper Divider)",
    "r2": "R2 (Lower Divider)",
    "rc": "RC (Collector Resistor)",
    "re": "RE (Emitter Resistor)",
    "beta": "β (Current Gain)",
    "vbe": "VBE (Base-Emitter Voltage)",
}

UNITS = {
    "vcc": "V",
    "rb": "kΩ",
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
) -> tuple[BiasInputs | None, dict[str, str], dict[str, str], str]:
    """Parse and validate one submitted form according to the selected bias mode.

    Returns (inputs_or_none, errors_by_field, raw_values_by_field, mode).
    """
    mode = form.get("mode", "divider").strip()
    raw_values: dict[str, str] = {"mode": mode}
    parsed: dict[str, float] = {}
    errors: dict[str, str] = {}

    for field in ALL_FIELDS:
        raw_values[field] = form.get(field, DEFAULTS[field]).strip()

    if mode not in VALID_MODES:
        errors["mode"] = MESSAGES["mode"]
        return None, errors, raw_values, mode

    required_fields = MODE_REQUIRED_FIELDS[mode]

    for field in required_fields:
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
        return None, errors, raw_values, mode

    inputs = BiasInputs(
        vcc=parsed["vcc"],
        rb=parsed.get("rb", float(DEFAULTS["rb"])),
        r1=parsed.get("r1", float(DEFAULTS["r1"])),
        r2=parsed.get("r2", float(DEFAULTS["r2"])),
        rc=parsed["rc"],
        re=parsed.get("re", float(DEFAULTS["re"])),
        beta=parsed["beta"],
        vbe=parsed["vbe"],
        mode=mode,
    )
    errors = validate_inputs(inputs)
    if errors:
        return None, errors, raw_values, mode

    return inputs, {}, raw_values, mode


def _default_inputs(mode: str = "divider") -> BiasInputs:
    return BiasInputs(
        vcc=float(DEFAULTS["vcc"]),
        rb=float(DEFAULTS["rb"]),
        r1=float(DEFAULTS["r1"]),
        r2=float(DEFAULTS["r2"]),
        rc=float(DEFAULTS["rc"]),
        re=float(DEFAULTS["re"]),
        beta=float(DEFAULTS["beta"]),
        vbe=float(DEFAULTS["vbe"]),
        mode=mode,
    )


def _compute_for_mode(inputs: BiasInputs):
    """Explicit if / elif dispatch by bias circuit mode as specified in Lab 03."""
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


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        actions = request.form.getlist("action")
        action = "switch_mode" if "switch_mode" in actions else "calculate"
        if action == "switch_mode":
            mode = request.form.get("mode", "divider").strip()
            if mode not in VALID_MODES:
                mode = "divider"
            values = dict(DEFAULTS)
            values["mode"] = mode
            for field in ALL_FIELDS:
                if field in request.form and request.form.get(field, "").strip() != "":
                    values[field] = request.form.get(field, "").strip()
            inputs, errors, values, mode = parse_form(values)
        else:
            inputs, errors, values, mode = parse_form(request.form)
    else:
        requested_mode = request.args.get("mode", "divider").strip()
        mode = requested_mode if requested_mode in VALID_MODES else "divider"
        inputs = _default_inputs(mode)
        errors = {}
        values = dict(DEFAULTS)
        values["mode"] = mode

    result = _compute_for_mode(inputs) if inputs is not None else None
    result_dict = result.to_dict() if result is not None else None

    if inputs is not None:
        circuit = dict(values)
    else:
        # Keep the schematic showing what the student actually typed, falling
        # back to the default only for fields left blank.
        circuit = {}
        for field in ALL_FIELDS:
            raw = values.get(field, "").strip()
            circuit[field] = raw if raw else DEFAULTS[field]
        circuit["mode"] = mode if mode in VALID_MODES else "divider"

    active_mode = mode if mode in VALID_MODES else "divider"
    visible_fields = MODE_REQUIRED_FIELDS[active_mode]

    return render_template(
        "index.html",
        mode=mode,
        active_mode=active_mode,
        mode_labels=MODE_LABELS,
        valid_modes=VALID_MODES,
        fields=visible_fields,
        all_fields=ALL_FIELDS,
        labels=LABELS,
        units=UNITS,
        values=values,
        errors=errors,
        result=result,
        result_dict=result_dict,
        circuit=circuit,
    )


if __name__ == "__main__":
    app.run(debug=True)