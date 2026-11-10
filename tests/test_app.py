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
