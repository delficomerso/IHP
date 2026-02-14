"""Verify all physical layout cells use pin sublayers and port_type='electrical'.

Every add_port() call in physical layout cells must:
1. Use a pin sublayer (datatype == 2) instead of a drawing layer (datatype == 0)
2. Include port_type="electrical"

The gold standard for this pattern is bjt_transistors.py.
"""

from __future__ import annotations

import importlib

import pytest

from ihp import PDK
from ihp.cells import bondpads as bondpads_mod
from ihp.cells import capacitors as capacitors_mod
from ihp.cells import fet_transistors as fet_mod
from ihp.cells import inductors as inductors_mod
from ihp.cells import passives as passives_mod
from ihp.cells import resistors as resistors_mod
from ihp.cells import rf_transistors as rf_mod
from ihp.cells import via_stacks as via_mod

# bipolar module is shadowed by primitives.bipolar() function in ihp.cells namespace
bipolar_mod = importlib.import_module("ihp.cells.bipolar")


@pytest.fixture(autouse=True)
def activate_pdk():
    PDK.activate()


CELLS_TO_TEST = [
    # FET transistors
    ("nmos", fet_mod.nmos, {}),
    ("pmos", fet_mod.pmos, {}),
    ("nmos_hv", fet_mod.nmos_hv, {}),
    ("pmos_hv", fet_mod.pmos_hv, {}),
    # RF transistors
    ("rfnmos", rf_mod.rfnmos, {}),
    ("rfpmos", rf_mod.rfpmos, {}),
    ("rfnmos_hv", rf_mod.rfnmos_hv, {}),
    ("rfpmos_hv", rf_mod.rfpmos_hv, {}),
    # Inductors
    ("inductor2_1turn", inductors_mod.inductor2, {"turns": 1}),
    ("inductor2_2turn", inductors_mod.inductor2, {"turns": 2}),
    # Resistors
    ("rsil", resistors_mod.rsil, {}),
    ("rppd", resistors_mod.rppd, {}),
    ("rhigh", resistors_mod.rhigh, {}),
    # Passives
    ("svaricap", passives_mod.svaricap, {}),
    ("esd_nmos", passives_mod.esd_nmos, {}),
    ("ptap1", passives_mod.ptap1, {}),
    ("ntap1", passives_mod.ntap1, {}),
    # Capacitors
    ("cmom", capacitors_mod.cmom, {}),
    ("cmim", capacitors_mod.cmim, {}),
    ("rfcmim", capacitors_mod.rfcmim, {}),
    # Bipolar (simplified)
    ("bipolar_npn13G2", bipolar_mod.npn13G2, {}),
    ("bipolar_pnpMPA", bipolar_mod.pnpMPA, {}),
    # Bondpads
    ("bondpad", bondpads_mod.bondpad, {}),
    ("bondpad_array", bondpads_mod.bondpad_array, {}),
    # Via stacks
    ("via_stack", via_mod.via_stack, {}),
    ("via_stack_with_pads", via_mod.via_stack_with_pads, {}),
]


def _resolve_layer(comp, port) -> tuple[int, int]:
    """Resolve port layer index to (layer_number, datatype) tuple."""
    layer_idx = port.layer
    info = comp.kcl.layout.get_info(layer_idx)
    return (info.layer, info.datatype)


@pytest.mark.parametrize(
    "name,factory,kwargs",
    CELLS_TO_TEST,
    ids=[t[0] for t in CELLS_TO_TEST],
)
def test_port_type_is_electrical(name, factory, kwargs):
    """Every port on a physical cell must have port_type='electrical'."""
    comp = factory(**kwargs)
    assert len(comp.ports) > 0, f"{name} has no ports"
    for port in comp.ports:
        assert port.port_type == "electrical", (
            f"{name}.ports['{port.name}'] has port_type='{port.port_type}', "
            f"expected 'electrical'"
        )


@pytest.mark.parametrize(
    "name,factory,kwargs",
    CELLS_TO_TEST,
    ids=[t[0] for t in CELLS_TO_TEST],
)
def test_port_layer_is_pin_sublayer(name, factory, kwargs):
    """Every port layer must be a pin sublayer (datatype == 2), not drawing (0)."""
    comp = factory(**kwargs)
    assert len(comp.ports) > 0, f"{name} has no ports"
    for port in comp.ports:
        layer_num, datatype = _resolve_layer(comp, port)
        assert datatype == 2, (
            f"{name}.ports['{port.name}'] layer=({layer_num}, {datatype}), "
            f"expected datatype=2 (pin sublayer)"
        )
