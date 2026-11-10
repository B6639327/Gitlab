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
