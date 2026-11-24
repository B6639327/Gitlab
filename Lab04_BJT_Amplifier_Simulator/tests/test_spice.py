import pytest
from spice_engine import build_netlist, run_simulation, _parse_op


def test_build_netlist_contains_components_and_directives():
    params = {
        "vcc": 12.0, "r1": 100.0, "r2": 22.0, "rc": 2.2, "re": 1.0,
        "rl": 10.0, "cin": 10.0, "cout": 10.0, "vin_amp": 10.0, "vin_freq": 1.0,
    }
    net_op = build_netlist(params, "op")
    assert ".op" in net_op
    assert "Q2N2222" in net_op

    net_ac = build_netlist(params, "ac")
    assert ".ac dec" in net_ac

    net_tran = build_netlist(params, "tran")
    assert ".tran" in net_tran
    assert "SIN(0 0.01 1000.0)" in net_tran


def test_build_netlist_rejects_zero_re():
    params = {
        "vcc": 12.0, "r1": 100.0, "r2": 22.0, "rc": 2.2, "re": 0.0,
        "rl": 10.0, "cin": 10.0, "cout": 10.0, "vin_amp": 10.0, "vin_freq": 1.0,
    }
    with pytest.raises(ValueError):
        build_netlist(params, "op")


def test_parse_op_extracts_voltages():
    sample_log = """
    v(base) = 2.015000e+00
    v(emit) = 1.352000e+00
    v(coll) = 9.034000e+00
    v(coll,emit) = 7.682000e+00
    """
    params = {"vcc": 12.0, "rc": 2.2}
    parsed = _parse_op(sample_log, "* netlist", "ngspice-42", params)
    assert parsed["status"] == "success"
    assert parsed["vb"] == pytest.approx(2.015)
    assert parsed["vce"] == pytest.approx(7.682)


def test_run_simulation_handles_missing_ngspice(monkeypatch):
    monkeypatch.setattr("spice_engine.shutil.which", lambda _: None)
    params = {
        "vcc": 12.0, "r1": 100.0, "r2": 22.0, "rc": 2.2, "re": 1.0,
        "rl": 10.0, "cin": 10.0, "cout": 10.0, "vin_amp": 10.0, "vin_freq": 1.0,
    }
    res = run_simulation(params, "op")
    assert res["status"] == "error"
    assert "not found" in res["error"]
