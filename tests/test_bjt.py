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
