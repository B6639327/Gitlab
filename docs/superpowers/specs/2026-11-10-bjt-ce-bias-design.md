# BJT Common-Emitter DC Bias Web App — Design

**Course:** ENG29 2121
**Date:** 2026-11-10
**Status:** Approved for planning
**Visual target:** approved dashboard mockup (three-column lab layout)

## Intent and why

This is a short lab deliverable: a small, real Flask web application that
computes the DC operating point of a voltage-divider-biased BJT
common-emitter stage. Students enter seven bias values and see the
operating point with units, input validation, a region warning, an
independent cross-check, and a live schematic. The app must run on
localhost and be committed to GitHub the same day.

The point is to demonstrate the full engineering loop — separate
calculation logic, web layer, presentation, and tests — not to build a
circuit simulator.

## Goals

- One-page Flask app: form on GET, results on POST, server-side rendering.
- Dashboard layout matching the approved mockup: three columns for
  Input Parameters, Circuit, and DC Bias Results, plus a page header and
  a "Week 2 Goal" banner below.
- On GET, pre-fill the mockup's example values and immediately show the
  computed result, so the demo opens looking like the mockup.
- Pure-Python engineering module with no Flask imports.
- DC operating point: `VB`, `VE`, `VC`, `VCE`, `IB`, `IC`, `IE`, with units.
- Validation of all seven inputs with per-field messages.
- Region classification: active / cutoff / saturation, with warnings.
- Independent second calculation and a visible cross-check result.
- A live circuit schematic whose labels follow the current input values.
- Unit tests for the engineering logic and route tests for the web layer.
- Fix the repository's broken README and remove stray junk files.
- Running localhost demo and a commit on `main` today.

## Non-goals

- AC analysis, small-signal model, gain, input/output impedance.
- Transient or frequency response.
- Schematic capture or a general circuit editor.
- FET/MOSFET support.
- Multiple transistor stages, Darlington pairs, or load lines.
- Persistence, user accounts, authentication, deployment.
- JavaScript framework or build step.

## Anti-goals

- Reporting a negative `IB` or `IC` as if it were a valid operating point.
- Presenting saturated or cutoff results with no warning.
- Hidden unit conversions (e.g. silently treating kΩ as Ω).
- Hard-coding result numbers that do not follow from the inputs.
- Over-engineering: no database, no blueprints, no service layer, no
  external API or CDN dependency.

## Constraints

- Python 3.12, Flask 3.x, pytest 8+ on Windows (PowerShell).
- Resistor inputs in **kΩ**; voltages in **V**; `beta` dimensionless.
- `VCE(sat)` is a fixed constant **0.2 V**.
- Internal SI units (Ω, A, V); conversion happens at the module boundary.
- UI copy is **English**, matching the approved mockup.
- Palette: teal accents (`#0f766e` / `#0d9488`), pale blue page
  background, white rounded cards, subtle borders and shadows.
- No external assets: system fonts, local CSS, inline SVG icons and
  schematic only.
- Existing `electrical.py` and `test_electrical.py` are left in place and
  untouched (previous lab work).

## Circuit and equations

Voltage-divider bias: `VCC` feeds `R1` to the base; `R2` from base to
ground; `RC` from `VCC` to collector; `RE` from emitter to ground.

Primary (Thevenin) method:

```
VBB = VCC * R2 / (R1 + R2)
RB  = R1 * R2 / (R1 + R2)
IB  = (VBB - VBE) / (RB + (beta + 1) * RE)
IC  = beta * IB
IE  = (beta + 1) * IB
VE  = IE * RE
VB  = VE + VBE
VC  = VCC - IC * RC
VCE = VC - VE
```

Independent cross-check (nodal formulation, no Thevenin formulas):

Unknowns `VB`, `VE`. Solve the 2x2 linear system:

```
KCL at base:  (VB - VCC)/R1 + VB/R2 + VE/((beta + 1) * RE) = 0
VBE source:   VB - VE = VBE
```

Then `IE = VE / RE`, `IB = IE / (beta + 1)`, `IC = beta * IB`,
`VC = VCC - IC * RC`, `VCE = VC - VE`.

Cross-check passes when `abs(dIC) <= 1e-9 A` and `abs(dVCE) <= 1e-6 V`.
The result exposes the `VCE` difference for display. In cutoff the
cross-check is not applicable (`None`).

## Validation rules

All inputs are parsed as finite floats (`NaN` and `inf` rejected).

| Field | Rule | Message |
|---|---|---|
| VCC | `> 0` | `VCC must be greater than 0 V` |
| R1 | `> 0` | `R1 must be greater than 0 kΩ` |
| R2 | `> 0` | `R2 must be greater than 0 kΩ` |
| RC | `> 0` | `RC must be greater than 0 kΩ` |
| RE | `> 0` | `RE must be greater than 0 kΩ` |
| beta | `> 0` | `beta must be greater than 0` |
| VBE | `0 < VBE < VCC` | `VBE must be between 0 and VCC` |

Non-numeric, non-finite, or missing: `Please enter a valid number.`

## Region rules

- **Cutoff** when `VBB <= VBE`: report `IB = IC = IE = 0`, `VE = 0`,
  `VB = VBB`, `VC = VCE = VCC`; warning that the active-region model does
  not apply. Cross-check is `None`.
- **Saturation** when `VCE <= 0.2 V`: keep the computed values, warning
  that the linear active-region model is invalid and values are
  approximate.
- **Active** otherwise.

Exact warning copy:

```
Cutoff: VBB <= VBE — transistor is off (IC ~ 0); active-region equations do not apply.
Saturation: VCE <= 0.2 V — values are approximate; the linear active-region model does not apply.
```

## Approaches considered

1. **Thevenin closed form + independent nodal solve (chosen).** Small,
   exact, fast, easy to test; the second formulation is genuinely
   different code and catches algebra/sign mistakes.
2. **Numeric root-finding (bisection/Newton) for both methods.** More
   "independent" numerically, but adds tolerances, iteration limits, and
   failure modes for no lab benefit.
3. **SymPy symbolic solve.** Eliminates hand algebra but adds a heavy
   dependency and startup cost; overkill for two linear equations.

## Architecture and files

```
app.py                     Flask app, one route `/`, defaults, form parsing, errors
bjt.py                     Dataclasses, validation, Thevenin solve, nodal cross-check
templates/index.html       Page shell: header, three-column dashboard, goal banner
templates/_schematic.html  Inline SVG common-emitter schematic with live labels
static/style.css           Dashboard grid, cards, badges, responsive rules
tests/test_bjt.py          Engineering unit tests
tests/test_app.py          Flask test-client route and layout tests
requirements.txt           Flask and pytest
README.md                  Rewritten: purpose, install, run, test, formulas, limits
```

### `bjt.py` public interface

```python
VCE_SAT = 0.2  # volts

@dataclass(frozen=True)
class BiasInputs:
    vcc: float      # V
    r1: float       # kΩ (as entered)
    r2: float       # kΩ
    rc: float       # kΩ
    re: float       # kΩ
    beta: float     # dimensionless
    vbe: float      # V

@dataclass(frozen=True)
class BiasResult:
    ib_a: float
    ic_a: float
    ie_a: float
    vb: float
    vc: float
    ve: float
    vce: float
    region: str                     # "active" | "cutoff" | "saturation"
    warnings: tuple[str, ...]
    cross_check_ok: bool | None     # None in cutoff
    cross_check_delta_vce: float | None

def validate_inputs(inputs: BiasInputs) -> dict[str, str]:
    """Return {field_name: English message}; empty dict means valid."""

def calculate_bias(inputs: BiasInputs) -> BiasResult:
    """Raise ValueError if inputs are invalid; otherwise solve the bias point."""
```

The module converts kΩ to Ω internally. It never imports Flask.

### `app.py`

- `DEFAULTS` holds the mockup example as strings: `VCC=12.0`, `R1=100`,
  `R2=22`, `RC=2.2`, `RE=1.0`, `beta=100`, `VBE=0.70`.
- `GET /` renders the form with `DEFAULTS` filled in, computes the result
  for those defaults, and renders the schematic with their values.
- `POST /` reads `request.form`, parses each field, builds `BiasInputs`,
  calls `validate_inputs`, then `calculate_bias`. On error, re-renders the
  form with per-field messages and the values the user entered. On
  success, renders results on the same page.
- The schematic receives a `circuit` dict of display strings built from
  the parsed inputs when they are valid, otherwise from `DEFAULTS`.
- `app = Flask(__name__)` and `if __name__ == "__main__": app.run(debug=True)`.

### Page layout

```
┌──────────────────────────────────────────────────────────────┐
│ [chip icon] Lab 02: BJT DC Bias Web App     [ </> course ]   │
│             ENG29 2121 – Common Emitter (Voltage Divider)    │
├─────────────────┬──────────────────────┬─────────────────────┤
│ ⚙ Input         │ 🔌 Circuit           │ 📊 DC Bias Results  │
│ Parameters      │ Common-Emitter       │                     │
│                 │ Amplifier            │ VB  VE  VC  VCE     │
│ 7 labelled rows │ inline SVG schematic │ IB  IC  IE          │
│ [Calculate]     │ with live values     │ region status box   │
├─────────────────┴──────────────────────┴─────────────────────┤
│ 🎯 Week 2 Goal: rough target text ...                        │
└──────────────────────────────────────────────────────────────┘
```

- Three equal-ish columns on wide screens; stack vertically below 980 px.
- Input card rows: label on the left, numeric input plus unit suffix on
  the right. Units: `V`, `kΩ`, `–`.
- The results table shows rows in mockup order: `VB`, `VE`, `VC`, `VCE`,
  `IB`, `IC`, `IE`, each with unit.
- Region status box: green for active, amber for cutoff, red for
  saturation. Active copy: `Active region approximation OK` plus
  `VCE = <value> V > 0.2 V (transistor in active region)`.
- Cross-check line below the table: `Independent check: PASS (ΔVCE = ... V)`,
  `FAIL`, or `N/A (cutoff)`.
- Warnings listed inside the status area when present.
- Header right badge: `Computer Programming for Electrical Engineers`.
- Goal banner text: `Week 2 Goal` plus
  `Rough target for this lab: Build a Flask web app that takes the circuit
  parameters, computes the BJT DC bias (VB, VE, VC, VCE, IB, IC, IE) for a
  common-emitter amplifier with voltage-divider bias, and displays the results.`

### Schematic

`_schematic.html` is an inline SVG, sized to the middle card. It draws:

- Top `VCC` rail with a node and the label `VCC = <value> V`.
- `R1` from the rail to the base node, and `R2` from the base node to
  ground, both labelled with their kΩ values.
- `RC` from the rail to the collector, labelled with its kΩ value.
- An NPN transistor symbol (`Q1`, `NPN`, `beta = <value>`).
- `RE` from the emitter to ground, labelled with its kΩ value.
- Ground symbols at the bottom of `R2` and `RE`.

Labels are Jinja placeholders fed by `circuit`, never hard-coded numbers.
The schematic is decorative/illustrative; the results table is the
authoritative output.

### Default example

With the mockup inputs (`12 V`, `100 kΩ`, `22 kΩ`, `2.2 kΩ`, `1 kΩ`,
`beta = 100`, `VBE = 0.7 V`) the correct operating point is approximately:

```
VB = 1.94 V   VE = 1.24 V   VC = 9.29 V   VCE = 8.05 V
IB = 12.3 µA  IC = 1.23 mA  IE = 1.24 mA   region = active
```

The mockup's displayed numbers (`2.20 / 1.50 / 8.70 / 7.20 / 15.1 /
1.50 / 1.51`) do not follow from its own inputs. The app always computes
from inputs; it never reproduces inconsistent numbers.

## Testing strategy

- Known textbook example with independently pre-computed expected values
  (the Task 1 test case: `12 V`, `100 kΩ`, `22 kΩ`, `4.7 kΩ`, `1 kΩ`,
  `beta = 150`, `VBE = 0.7 V`).
- Exact formula checks with `pytest.approx`.
- Validation table cases: zero, negative, `VBE >= VCC`, non-finite.
- Cutoff case: `VBB <= VBE`.
- Saturation case: computed `VCE <= 0.2`.
- Cross-check agreement on active and saturation cases, plus a
  monkeypatched disagreement.
- Flask: GET 200 with all fields and the three layout sections; GET shows
  the default computed result; valid POST shows results and units;
  invalid POST shows the English message and preserves entered values;
  non-numeric POST shows the parse error.
- Final: full suite green, app starts, `GET /` returns 200 on localhost.

## What is left to the builder

- Exact SVG coordinates, stroke widths, and icon shapes within the
  approved layout.
- Exact CSS spacing and breakpoint details.
- Whether parsing helpers live in `app.py` or a small function in `bjt.py`
  (preference: `app.py`, since it is HTTP-form specific).
- Additional non-critical tests beyond the required cases.

## Repository cleanup (part of this work)

- Rewrite `README.md`, removing the unresolved merge-conflict markers.
- Delete the two stray files committed by a redirected diff:
  `t? verify DC circuit results?` and `? start DC circuit calculator?`.
- Add `requirements.txt`.
- Leave `electrical.py` and `test_electrical.py` untouched.
- Work on branch `feature/bjt-ce-bias`, merge to `main`, push to
  `origin/main`.
