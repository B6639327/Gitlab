# BJT Common-Emitter DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal one-page Flask dashboard that computes and cross-checks the DC operating point of a voltage-divider-biased BJT common-emitter stage, with a live schematic.

**Architecture:** `bjt.py` holds all engineering logic as pure functions and frozen dataclasses. `app.py` is the thin Flask layer that parses the form, maps validation errors, supplies the default example, and renders one dashboard template. The page is a three-column grid: inputs, inline-SVG schematic, results. Tests are split between engineering unit tests and Flask route/layout tests.

**Tech Stack:** Python 3.12, Flask 3.x, pytest 8+, Jinja2 templates, inline SVG, plain CSS.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`

## Global Constraints

- Resistor inputs are in **kΩ**; voltages in **V**; `beta` is dimensionless.
- Internal engineering math uses SI units (Ω, A); convert kΩ → Ω at the `bjt.py` boundary.
- `VCE_SAT = 0.2` V, a module constant.
- `bjt.py` must never import Flask.
- UI copy is **English**, matching the approved mockup; no external assets, icon fonts, or CDN.
- Palette: teal accents, pale blue page background, white rounded cards.
- Leave `electrical.py` and `test_electrical.py` untouched.
- Work on branch `feature/bjt-ce-bias`; merge to `main` and push `origin/main` at the end.
- Every task ends with the full test suite green and a commit.

## Review Focus

- **Blank field** → per-field English parse error, HTTP 200, previously entered values preserved (Task 4).
- **`VBE >= VCC`** → validation error, never a nonsensical cutoff/active result (Task 1).
- **`RE = 0`** → rejected by validation before the nodal cross-check divides by zero (Tasks 1 and 3).
- **`VBB <= VBE`** → cutoff path returns zero currents and no negative operating point (Task 2).
- **`VCE <= 0.2 V`** → saturation warning shown, computed values still displayed, cross-check still runs (Tasks 2 and 3).

---

## Pre-flight: isolate the work

- [ ] Create the working branch:

```powershell
git checkout main
git pull --ff-only
git checkout -b feature/bjt-ce-bias
```

Expected: `Switched to a new branch 'feature/bjt-ce-bias'`.

---

### Task 1: Engineering core — dataclasses, validation, Thevenin solve

**Files:**
- Create: `bjt.py`
- Create: `tests/test_bjt.py`
- Create: `requirements.txt`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `VCE_SAT: float = 0.2`
  - `BiasInputs(vcc, r1, r2, rc, re, beta, vbe)` — frozen dataclass, all `float`.
  - `BiasResult(ib_a, ic_a, ie_a, vb, vc, ve, vce, region, warnings, cross_check_ok, cross_check_delta_vce)` — frozen dataclass. In this task `region="active"`, `warnings=()`, both cross-check fields are `None`.
  - `validate_inputs(inputs: BiasInputs) -> dict[str, str]` — field name → English message; `{}` when valid.
  - `calculate_bias(inputs: BiasInputs) -> BiasResult` — raises `ValueError` when invalid.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_bjt.py`:

```python
import pytest

from bjt import BiasInputs, calculate_bias, validate_inputs


def test_textbook_active_bias_point():
    result = calculate_bias(BiasInputs(12, 100, 22, 4.7, 1, 150, 0.7))

    assert result.region == "active"
    assert result.ib_a == pytest.approx(8.66065367084e-06, rel=1e-9)
    assert result.ic_a == pytest.approx(1.29909805063e-03, rel=1e-9)
    assert result.ie_a == pytest.approx(1.30775870430e-03, rel=1e-9)
    assert result.vb == pytest.approx(2.00775870430, rel=1e-9)
    assert result.vc == pytest.approx(5.89423916206, rel=1e-9)
    assert result.ve == pytest.approx(1.30775870430, rel=1e-9)
    assert result.vce == pytest.approx(4.58648045776, rel=1e-9)
    assert result.warnings == ()


@pytest.mark.parametrize(
    "inputs, field",
    [
        (BiasInputs(0, 100, 22, 4.7, 1, 150, 0.7), "vcc"),
        (BiasInputs(-1, 100, 22, 4.7, 1, 150, 0.7), "vcc"),
        (BiasInputs(12, 0, 22, 4.7, 1, 150, 0.7), "r1"),
        (BiasInputs(12, -1, 22, 4.7, 1, 150, 0.7), "r1"),
        (BiasInputs(12, 100, 0, 4.7, 1, 150, 0.7), "r2"),
        (BiasInputs(12, 100, 22, 0, 1, 150, 0.7), "rc"),
        (BiasInputs(12, 100, 22, 4.7, 0, 150, 0.7), "re"),
        (BiasInputs(12, 100, 22, 4.7, 1, 0, 0.7), "beta"),
        (BiasInputs(12, 100, 22, 4.7, 1, 150, 0), "vbe"),
        (BiasInputs(12, 100, 22, 4.7, 1, 150, 12), "vbe"),
        (BiasInputs(12, 100, 22, 4.7, 1, 150, 13), "vbe"),
    ],
)
def test_validate_rejects_invalid_values(inputs, field):
    errors = validate_inputs(inputs)
    assert field in errors


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_validate_rejects_non_finite(bad):
    errors = validate_inputs(BiasInputs(12, bad, 22, 4.7, 1, 150, 0.7))
    assert "r1" in errors


def test_validate_accepts_textbook_inputs():
    assert validate_inputs(BiasInputs(12, 100, 22, 4.7, 1, 150, 0.7)) == {}


def test_calculate_bias_raises_on_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_bias(BiasInputs(12, 100, 22, 4.7, 0, 150, 0.7))
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python -m pytest tests/test_bjt.py -v`

Expected: collection error, `ModuleNotFoundError: No module named 'bjt'`.

- [ ] **Step 3: Implement `bjt.py`**

Requirements for the implementation:

- `BiasInputs` and `BiasResult` are `@dataclass(frozen=True)` types with the exact field order in the Interfaces block.
- `validate_inputs` returns these exact English messages:

```python
{
    "vcc": "VCC must be greater than 0 V",
    "r1": "R1 must be greater than 0 kΩ",
    "r2": "R2 must be greater than 0 kΩ",
    "rc": "RC must be greater than 0 kΩ",
    "re": "RE must be greater than 0 kΩ",
    "beta": "beta must be greater than 0",
    "vbe": "VBE must be between 0 and VCC",
}
```

Use `math.isfinite` first; a non-finite field gets `"Please enter a valid number."`. Then apply the range rules in the order of the dict above. `vbe` is valid only when `0 < vbe < vcc`.

- `calculate_bias` calls `validate_inputs`; if errors exist it raises `ValueError("; ".join(errors.values()))`.
- Convert `r1`, `r2`, `rc`, `re` from kΩ to Ω by multiplying by 1000.
- Compute with the Thevenin formulas from the spec: `VBB`, `RB`, `IB`, `IC`, `IE`, `VE`, `VB`, `VC`, `VCE`.
- Return `BiasResult(..., region="active", warnings=(), cross_check_ok=None, cross_check_delta_vce=None)`.

- [ ] **Step 4: Run the tests and verify they pass**

Run: `python -m pytest tests/test_bjt.py -v`

Expected: all tests PASS.

- [ ] **Step 5: Add `requirements.txt`**

```text
Flask>=3.0,<4
pytest>=8,<10
```

- [ ] **Step 6: Commit**

```powershell
git add bjt.py tests/test_bjt.py requirements.txt docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md
git commit -m "feat: add BJT bias engineering core and validation"
```

---

### Task 2: Region classification — cutoff, saturation, warnings

**Files:**
- Modify: `bjt.py`
- Modify: `tests/test_bjt.py`

**Interfaces:**
- Consumes: `BiasInputs`, `BiasResult`, `calculate_bias`, `VCE_SAT`.
- Produces: `_classify_region(vbb: float, vbe: float, vce: float) -> str` returning `"cutoff"`, `"saturation"`, or `"active"`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_bjt.py`:

```python
from bjt import _classify_region


def test_cutoff_returns_zero_currents_and_no_cross_check():
    result = calculate_bias(BiasInputs(12, 100, 4.7, 4.7, 1, 150, 0.7))

    assert result.region == "cutoff"
    assert result.ib_a == 0.0
    assert result.ic_a == 0.0
    assert result.ie_a == 0.0
    assert result.ve == 0.0
    assert result.vb == pytest.approx(0.538681948424, rel=1e-9)
    assert result.vc == pytest.approx(12.0)
    assert result.vce == pytest.approx(12.0)
    assert result.cross_check_ok is None
    assert "Cutoff" in result.warnings[0]


def test_boundary_vbb_equals_vbe_is_cutoff():
    result = calculate_bias(BiasInputs(7, 90, 10, 4.7, 1, 150, 0.7))
    assert result.region == "cutoff"


def test_saturation_reports_values_and_warning():
    result = calculate_bias(BiasInputs(12, 68, 100, 0.6, 0.1, 150, 0.7))

    assert result.region == "saturation"
    assert result.ib_a == pytest.approx(1.1592836946277098e-04, rel=1e-9)
    assert result.ic_a == pytest.approx(1.7389255419415647e-02, rel=1e-9)
    assert result.ie_a == pytest.approx(1.7505183788878418e-02, rel=1e-9)
    assert result.vb == pytest.approx(2.4505183788878417, rel=1e-9)
    assert result.vc == pytest.approx(1.5664467483506108, rel=1e-9)
    assert result.ve == pytest.approx(1.7505183788878418, rel=1e-9)
    assert result.vce == pytest.approx(-0.18407163053723097, rel=1e-9)
    assert "Saturation" in result.warnings[0]


def test_region_boundaries():
    assert _classify_region(0.7, 0.7, 10.0) == "cutoff"
    assert _classify_region(2.0, 0.7, 0.2) == "saturation"
    assert _classify_region(2.0, 0.7, 0.2000001) == "active"
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python -m pytest tests/test_bjt.py -v`

Expected: FAIL — `ImportError: cannot import name '_classify_region'` and cutoff/saturation assertions fail.

- [ ] **Step 3: Implement region handling in `bjt.py`**

- Add exact warning constants (tests pin the leading word):

```python
CUTOFF_WARNING = (
    "Cutoff: VBB <= VBE — transistor is off (IC ~ 0); "
    "active-region equations do not apply."
)
SATURATION_WARNING = (
    "Saturation: VCE <= 0.2 V — values are approximate; "
    "the linear active-region model does not apply."
)
```

- Implement `_classify_region(vbb, vbe, vce)` exactly: `vbb <= vbe` → `"cutoff"`; else `vce <= VCE_SAT` → `"saturation"`; else `"active"`.
- In `calculate_bias`, compute `vbb` before the base-current calculation. If `vbb <= vbe` (the cutoff condition), return the cutoff result directly: `ib_a=ic_a=ie_a=0.0`, `vb=vbb`, `vc=vcc`, `ve=0.0`, `vce=vcc`, `region="cutoff"`, `warnings=(CUTOFF_WARNING,)`, `cross_check_ok=None`, `cross_check_delta_vce=None`.
- Otherwise compute the active-region values, classify with the real `vce`, and set `warnings=(SATURATION_WARNING,)` when the region is `"saturation"`; otherwise `()`.

- [ ] **Step 4: Run the tests and verify they pass**

Run: `python -m pytest tests/test_bjt.py -v`

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add bjt.py tests/test_bjt.py
git commit -m "feat: classify BJT cutoff and saturation regions"
```

---

### Task 3: Independent nodal cross-check

**Files:**
- Modify: `bjt.py`
- Modify: `tests/test_bjt.py`

**Interfaces:**
- Consumes: `BiasInputs`, `calculate_bias`, `VCE_SAT`.
- Produces: `_nodal_solve(inputs: BiasInputs) -> tuple[float, float]` returning `(ic_a, vce_a)`; `calculate_bias` now fills `cross_check_ok` and `cross_check_delta_vce` for active and saturation results.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_bjt.py`:

```python
import bjt


def test_cross_check_agrees_for_active_result():
    result = calculate_bias(BiasInputs(12, 100, 22, 4.7, 1, 150, 0.7))
    assert result.cross_check_ok is True
    assert result.cross_check_delta_vce == pytest.approx(0.0, abs=1e-6)


def test_cross_check_agrees_for_saturated_result():
    result = calculate_bias(BiasInputs(12, 68, 100, 0.6, 0.1, 150, 0.7))
    assert result.cross_check_ok is True


def test_cross_check_is_none_in_cutoff():
    result = calculate_bias(BiasInputs(12, 100, 4.7, 4.7, 1, 150, 0.7))
    assert result.cross_check_ok is None
    assert result.cross_check_delta_vce is None


def test_cross_check_detects_disagreement(monkeypatch):
    monkeypatch.setattr(bjt, "_nodal_solve", lambda inputs: (0.5, 9.9))
    result = calculate_bias(BiasInputs(12, 100, 22, 4.7, 1, 150, 0.7))
    assert result.cross_check_ok is False
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python -m pytest tests/test_bjt.py -v`

Expected: FAIL — `_nodal_solve` missing and `cross_check_ok is None` where `True` is expected.

- [ ] **Step 3: Implement `_nodal_solve` and the comparison**

- Convert kΩ → Ω.
- Solve the 2×2 system from the spec with Cramer's rule:

```text
A = [[1/R1 + 1/R2, 1/((beta+1)*RE)],
     [1,            -1          ]]
b = [VCC/R1, VBE]
det = A00*A11 - A01*A10
VB = (b0*A11 - A01*b1) / det
VE = (A00*b1 - b0*A10) / det
```

- Return `(IC, VCE)` where `IE = VE/RE`, `IB = IE/(beta+1)`, `IC = beta*IB`, `VC = VCC - IC*RC`, `VCE = VC - VE`.
- In `calculate_bias`, after computing the primary result for a non-cutoff region:

```python
nodal_ic, nodal_vce = _nodal_solve(inputs)
delta = nodal_vce - vce
ok = abs(nodal_ic - ic) <= 1e-9 and abs(delta) <= 1e-6
```

Store `cross_check_ok=ok` and `cross_check_delta_vce=delta` in the returned result. Cutoff keeps both as `None`.

- [ ] **Step 4: Run the tests and verify they pass**

Run: `python -m pytest tests/test_bjt.py -v`

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add bjt.py tests/test_bjt.py
git commit -m "feat: add independent nodal cross-check"
```

---

### Task 4: Flask dashboard, schematic, and CSS

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Create: `templates/_schematic.html`
- Create: `static/style.css`
- Create: `tests/test_app.py`

**Interfaces:**
- Consumes: `BiasInputs`, `calculate_bias`, `validate_inputs` from `bjt.py`.
- Produces:
  - `app: Flask` — the application object.
  - `DEFAULTS: dict[str, str]` — the mockup example values.
  - `parse_form(form: Mapping[str, str]) -> tuple[BiasInputs | None, dict[str, str], dict[str, str]]` returning `(inputs_or_none, errors_by_field, raw_values_by_field)`.

- [ ] **Step 0: Install dependencies**

Run: `python -m pip install -r requirements.txt`

Expected: Flask installs successfully (pytest is already present).

- [ ] **Step 1: Write the failing route and layout tests**

Create `tests/test_app.py`:

```python
import pytest

from app import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


DEFAULTS = {
    "vcc": "12.0",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.70",
}


def test_get_renders_layout_sections_and_all_inputs(client):
    response = client.get("/")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Input Parameters" in text
    assert "Circuit: Common-Emitter Amplifier" in text
    assert "DC Bias Results" in text
    assert "Week 2 Goal" in text
    for name in DEFAULTS:
        assert f'name="{name}"' in text


def test_get_shows_default_example_and_result(client):
    text = client.get("/").get_data(as_text=True)

    assert 'value="12.0"' in text
    assert "1.23" in text          # default IC in mA
    assert "8.05" in text          # default VCE in V
    assert "Active region approximation OK" in text
    assert "Independent check: PASS" in text


def test_valid_post_shows_operating_point_and_cross_check(client):
    response = client.post("/", data=DEFAULTS)
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "1.23" in text
    assert "8.05" in text
    assert "Active region approximation OK" in text
    assert "Independent check: PASS" in text


def test_validation_error_is_shown_and_value_preserved(client):
    data = {**DEFAULTS, "r1": "-5"}
    response = client.post("/", data=data)
    text = response.get_data(as_text=True)

    assert "R1 must be greater than 0 kΩ" in text
    assert 'value="-5"' in text


def test_blank_field_shows_parse_error(client):
    data = {**DEFAULTS, "rc": ""}
    response = client.post("/", data=data)
    text = response.get_data(as_text=True)

    assert "Please enter a valid number." in text


def test_non_numeric_field_shows_parse_error_and_preserves_value(client):
    data = {**DEFAULTS, "beta": "abc"}
    response = client.post("/", data=data)
    text = response.get_data(as_text=True)

    assert "Please enter a valid number." in text
    assert 'value="abc"' in text
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python -m pytest tests/test_app.py -v`

Expected: collection error, `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Implement `app.py`**

- `app = Flask(__name__)`
- `FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")`
- `DEFAULTS` exactly as in the test file.
- Exact labels and units for the template:

```python
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
```

- `parse_form` reads `form.get(field, "").strip()`, converts to `float` with `math.isfinite`, and on failure records `"Please enter a valid number."`. If any parse error exists, return `(None, errors, raw_values)`. Otherwise build `BiasInputs(**parsed)`, call `validate_inputs`, and return `(inputs if not errors else None, errors, raw_values)`.
- `@app.route("/", methods=["GET", "POST"])`:
  - GET: `values = dict(DEFAULTS)`; build `BiasInputs` from the defaults and call `calculate_bias`; `errors = {}`.
  - POST: call `parse_form`; if `inputs` is not `None`, call `calculate_bias`.
  - `circuit = values if inputs is not None else dict(DEFAULTS)`.
  - Render `index.html` with `fields=FIELDS`, `labels=LABELS`, `units=UNITS`, `values=values`, `errors=errors`, `result=result`, `circuit=circuit`.
- `if __name__ == "__main__": app.run(debug=True)`

- [ ] **Step 4: Implement the dashboard template, schematic, and CSS**

`templates/index.html` must produce this structure:

1. **Header**: chip icon, title `Lab 02: BJT DC Bias Web App`, subtitle
   `ENG29 2121 – Common Emitter (Voltage Divider Bias)`, and a right-side
   badge containing `</>` plus `Computer Programming for Electrical Engineers`.
2. **Three-column grid** (`.dashboard`) with three cards:
   - **Input Parameters** card: gear icon, heading, and one row per field:
     label on the left; `<input name="{{ field }}" value="{{ values[field] }}"
     type="number" step="any" required>` plus the unit suffix from `UNITS`;
     show `{{ errors[field] }}` beneath the field when present. Submit button
     text `Calculate DC Bias`.
   - **Circuit card**: circuit icon, heading `Circuit: Common-Emitter
     Amplifier`, and `{% include "_schematic.html" %}`.
   - **DC Bias Results card**: chart icon, heading `DC Bias Results`, a table
     with rows in this order and formatting:
     - `VB`, `VE`, `VC`, `VCE`: 2 decimals, `V`
     - `IB`: 1 decimal, `µA` (`result.ib_a * 1e6`)
     - `IC`, `IE`: 2 decimals, `mA` (`result.ic_a * 1e3`, `result.ie_a * 1e3`)
     Show the region status box and the cross-check line:
     - active: green box, `Active region approximation OK`, detail
       `VCE = {{ "%.2f"|format(result.vce) }} V > 0.2 V (transistor in active region)`
     - cutoff: amber box, `Cutoff region`, plus every warning
     - saturation: red box, `Saturation region`, plus every warning
     - cross-check: `Independent check: PASS (ΔVCE = {{ "%.6f"|format(result.cross_check_delta_vce) }} V)`,
       `Independent check: FAIL (...)`, or `Independent check: N/A (cutoff)`
3. **Goal banner** below the grid: icon, `Week 2 Goal`, and the text
   `Rough target for this lab: Build a Flask web app that takes the circuit
   parameters, computes the BJT DC bias (VB, VE, VC, VCE, IB, IC, IE) for a
   common-emitter amplifier with voltage-divider bias, and displays the results.`

`templates/_schematic.html` must be an inline `<svg>` sized to the card,
drawing the common-emitter circuit:

- Top `VCC` rail with a node and the label `VCC = {{ circuit.vcc }} V`.
- `R1` between the rail and the base node, labelled `R1` and
  `{{ circuit.r1 }} kΩ`; `R2` between the base node and ground, labelled
  `R2` and `{{ circuit.r2 }} kΩ`.
- `RC` between the rail and the collector, labelled `RC` and
  `{{ circuit.rc }} kΩ`.
- An NPN transistor symbol with labels `Q1` and `NPN`, plus
  `β = {{ circuit.beta }}`.
- `RE` between the emitter and ground, labelled `RE` and
  `{{ circuit.re }} kΩ`.
- Ground symbols at the bottom of `R2` and `RE`.

Use simple `<line>`, `<rect>`, `<circle>`, `<path>`, and `<text>` elements;
coordinates and stroke widths are the builder's call. Do not hard-code
numeric values in the SVG.

`static/style.css` must provide:

- Pale blue page background; centered content with a maximum width.
- White rounded cards with subtle borders/shadows.
- `.dashboard` as a three-column grid with `gap`, collapsing to one
  column below `980px`.
- Header flex row that wraps on narrow screens.
- Input rows as a two-column grid (label / control) with unit suffixes.
- Table styling with alternating light rows and bold right-aligned values.
- Badge colors: green active, amber cutoff, red saturation.
- Goal banner with a pale blue background and rounded corners.

Link CSS with `url_for('static', filename='style.css')`.

- [ ] **Step 5: Run the route tests and verify they pass**

Run: `python -m pytest tests/test_app.py -v`

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add app.py templates/index.html templates/_schematic.html static/style.css tests/test_app.py
git commit -m "feat: add BJT bias dashboard UI and schematic"
```

---

### Task 5: Repository cleanup, README, and end-to-end verification

**Files:**
- Modify: `README.md`
- Delete: the two stray files tracked in git
- Modify: nothing in `electrical.py` or `test_electrical.py`

**Interfaces:**
- Consumes: everything built in Tasks 1–4.
- Produces: a runnable repository with accurate documentation.

- [ ] **Step 1: Remove the stray committed files**

```powershell
git ls-files | Where-Object { $_ -match 'verify DC circuit results|start DC circuit calculator' } | ForEach-Object { git rm -- $_ }
```

Expected: two files removed and staged.

- [ ] **Step 2: Rewrite `README.md`**

Replace the merge-conflict content with these sections:

- Project name and course ENG29 2121
- Features: DC operating point, validation, region warning, independent
  cross-check, live schematic
- Install: `pip install -r requirements.txt`
- Run: `python app.py` then open `http://127.0.0.1:5000`
- Test: `python -m pytest -v`
- Input/output units (kΩ, V, µA, mA)
- Formulas used (Thevenin + nodal cross-check)
- Limitations: DC bias only; no AC, transient, FET, or circuit editor
- File structure

Mention that `electrical.py` is previous lab work and is unchanged. The
documentation may be written in Thai or English; keep the existing
repository's Thai tone if continuing it.

- [ ] **Step 3: Run the full suite**

Run: `python -m pytest -v`

Expected: all tests in `tests/test_bjt.py` and `tests/test_app.py` PASS; `test_electrical.py` collects no tests and causes no failure.

- [ ] **Step 4: Verify the app serves on localhost**

```powershell
$server = Start-Process python -ArgumentList "app.py" -PassThru
Start-Sleep -Seconds 3
$status = (Invoke-WebRequest http://127.0.0.1:5000).StatusCode
Stop-Process -Id $server.Id
$status
```

Expected: `200`.

- [ ] **Step 5: Commit the cleanup and docs**

```powershell
git add -A
git commit -m "docs: document BJT bias app and clean repository"
```

- [ ] **Step 6: Merge and push**

```powershell
git checkout main
git merge --no-ff feature/bjt-ce-bias -m "merge: BJT CE bias web app"
git push origin main
```

Expected: `main` contains all commits and `origin/main` is up to date.

---

## Final acceptance checklist

- [ ] `python -m pytest -v` is green.
- [ ] `python app.py` serves HTTP 200 at `http://127.0.0.1:5000`.
- [ ] The page shows the header, all three cards, and the Week 2 Goal banner.
- [ ] Default example shows `IC ≈ 1.23 mA`, `VCE ≈ 8.05 V`, active status, and a passing independent check.
- [ ] The schematic labels follow the entered values.
- [ ] Textbook unit test still proves `IC ≈ 1.30 mA` and `VCE ≈ 4.59 V`.
- [ ] A cutoff input shows zero currents and a Cutoff warning.
- [ ] A saturation input shows computed values and a Saturation warning.
- [ ] Invalid input shows an English message and keeps entered values.
- [ ] `bjt.py` has no Flask import.
- [ ] `electrical.py` and `test_electrical.py` are unchanged.
- [ ] `main` is pushed to `origin`.
